#!/usr/bin/env python3
"""Review with --files NAME... (dry-run by default).

Only after user authorization and stopping archive writers, use --execute with
one --expected-sha256 NAME=HASH for each selected file. CLI flags are not user
consent. Deletion is irreversible; unlink cannot atomically assert an inode.
Linux/POSIX required; Python standard library only. No recursive deletion.
"""
import argparse
import contextlib
import hashlib
import json
import os
from pathlib import Path
import stat
import sys


class Refusal(ValueError):
    pass


def name_only(name):
    if (not isinstance(name, str) or not name or name in ('.', '..')
            or '/' in name or '\\' in name or '\x00' in name):
        raise Refusal('Only simple archive filenames are permitted: %r' % name)
    return name


@contextlib.contextmanager
def directory_fd(path):
    # Traverse without resolve(): resolving would silently accept symlinks.
    if not hasattr(os, 'O_NOFOLLOW') or not hasattr(os, 'O_DIRECTORY'):
        raise Refusal('Platform lacks required no-follow directory operations')
    path = Path(os.path.abspath(path))
    fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in path.parts[1:]:
            new_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                             dir_fd=fd)
            os.close(fd)
            fd = new_fd
        yield fd
    finally:
        os.close(fd)


def read_regular(fd, name):
    # O_NONBLOCK ensures a malicious FIFO does not hang before fstat rejects it.
    opened = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
    try:
        before = os.fstat(opened)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise Refusal('Not a single-link regular file: ' + name)
        chunks = []
        while True:
            chunk = os.read(opened, 65536)
            if not chunk:
                break
            chunks.append(chunk)
        after = os.fstat(opened)
        identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns,
                              s.st_ctime_ns, s.st_nlink)
        if identity(before) != identity(after):
            raise Refusal('File changed while reading: ' + name)
        return b''.join(chunks), identity(after)
    finally:
        os.close(opened)


def inventory(parent_fd):
    raw, _ = read_regular(parent_fd, 'inventory.json')
    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise Refusal('Duplicate inventory key: ' + key)
            result[key] = value
        return result
    data = json.loads(raw, object_pairs_hook=unique_keys)
    if not isinstance(data, dict) or set(data) != {'expired', 'keep'}:
        raise Refusal('Inventory must contain exactly expired and keep')
    sets = []
    for key in ('expired', 'keep'):
        values = data[key]
        if not isinstance(values, list):
            raise Refusal('Inventory entries must be lists')
        names = [name_only(value) for value in values]
        if len(set(names)) != len(names):
            raise Refusal('Duplicate inventory filenames')
        sets.append(set(names))
    if sets[0] & sets[1]:
        raise Refusal('Inventory expired/keep conflict')
    return sets


def preflight(parent_fd, archive_fd, selected, expected=None):
    expired, keep = inventory(parent_fd)
    if not selected or len(selected) != len(set(selected)):
        raise Refusal('Specify distinct filenames explicitly')
    for name in selected:
        name_only(name)
        if name in keep or name not in expired:
            raise Refusal('Not an inventory-approved expired file: ' + name)
    if expected is not None and set(expected) != set(selected):
        raise Refusal('Expected hashes must cover exactly the selected files')
    plans = []
    for name in selected:
        raw, identity = read_regular(archive_fd, name)
        digest = hashlib.sha256(raw).hexdigest()
        if expected is not None and expected[name] != digest:
            raise Refusal('Expected SHA-256 mismatch: ' + name)
        plans.append((name, len(raw), digest, identity))
    return plans


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--files', nargs='+', required=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--dry-run', action='store_true')
    mode.add_argument('--execute', action='store_true')
    parser.add_argument('--expected-sha256', action='append', default=[],
                        metavar='NAME=HASH')
    args = parser.parse_args(argv)
    deleted = []
    try:
        hashes = {}
        for item in args.expected_sha256:
            name, sep, digest = item.partition('=')
            name_only(name)
            if (not sep or name in hashes or len(digest) != 64
                    or any(c not in '0123456789abcdef' for c in digest)):
                raise Refusal('Invalid or duplicate expected SHA-256: ' + item)
            hashes[name] = digest
        if args.execute and not hashes:
            raise Refusal('--execute requires reviewed --expected-sha256 values')
        if not args.execute and hashes:
            raise Refusal('Expected hashes are only accepted with --execute')
        base = Path(os.path.abspath(__file__)).parent
        with directory_fd(base) as parent_fd, directory_fd(base / 'archive') as fd:
            plans = preflight(parent_fd, fd, args.files, hashes if args.execute else None)
            for name, size, digest, _ in plans:
                print('%s %s %d bytes sha256=%s' %
                      ('DELETE' if args.execute else 'DRY-RUN', name, size, digest),
                      flush=True)
            if args.execute:
                # Revalidate the complete batch before the first deletion.
                if preflight(parent_fd, fd, args.files, hashes) != plans:
                    raise Refusal('Plan changed before execution')
                for name, _, digest, identity in plans:
                    # Recheck inventory and each file immediately before unlink.
                    current = preflight(parent_fd, fd, [name], {name: digest})
                    if current[0][3] != identity:
                        raise Refusal('File identity changed: ' + name)
                    os.unlink(name, dir_fd=fd)
                    deleted.append(name)
                    print('DELETED ' + name, flush=True)
        return 0
    except (OSError, ValueError, UnicodeError) as exc:
        print('REFUSED: %s; already deleted: %s' % (exc, deleted), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
