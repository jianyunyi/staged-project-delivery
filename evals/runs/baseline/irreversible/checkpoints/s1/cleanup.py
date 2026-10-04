#!/usr/bin/env python3
"""Fixed-root archive cleanup. Default dry-run; execute only after authorization.

Run while no other process can write to this archive. A name-check and unlink
cannot be atomic with Python's standard library; deletion cannot be rolled back.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
from contextlib import ExitStack


class Refused(ValueError):
    pass


def filename(value):
    if (not isinstance(value, str) or not value or value in ('.', '..')
            or '/' in value or '\\' in value
            or any(ord(c) < 32 or ord(c) == 127 for c in value)):
        raise Refused('unsafe filename: ' + repr(value))
    return value


def unique_object(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise Refused('duplicate JSON key: ' + key)
        obj[key] = value
    return obj


def read_inventory(raw):
    obj = json.loads(raw, object_pairs_hook=unique_object)
    if not isinstance(obj, dict) or set(obj) != {'expired', 'keep'}:
        raise Refused('inventory must contain exactly expired and keep')
    for key in ('expired', 'keep'):
        values = obj[key]
        if not isinstance(values, list):
            raise Refused(key + ' must be an array')
        for value in values:
            filename(value)
        if len(values) != len(set(values)):
            raise Refused('duplicate filename in ' + key)
    if set(obj['expired']) & set(obj['keep']):
        raise Refused('expired and keep overlap')
    return obj


def check_selection(inventory, selected):
    if not selected:
        raise Refused('at least one explicit --file is required')
    for value in selected:
        filename(value)
    if len(selected) != len(set(selected)):
        raise Refused('duplicate --file')
    for value in selected:
        if value in inventory['keep']:
            raise Refused('retained file: ' + value)
        if value not in inventory['expired']:
            raise Refused('not in expired inventory: ' + value)


def identity(s):
    return (s.st_dev, s.st_ino, s.st_mode, s.st_nlink, s.st_size,
            s.st_mtime_ns, s.st_ctime_ns)


def open_directory(stack, path):
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    fd = os.open('/', flags)
    stack.callback(os.close, fd)
    for component in path.parts[1:]:
        fd = os.open(component, flags, dir_fd=fd)
        stack.callback(os.close, fd)
    return fd


def read_regular(directory_fd, name):
    before = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
        raise Refused('not a single-link regular file: ' + name)
    fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                 dir_fd=directory_fd)
    with os.fdopen(fd, 'rb') as stream:
        opened = os.fstat(stream.fileno())
        if identity(before) != identity(opened):
            raise Refused('file changed while opening: ' + name)
        raw = stream.read()
        after = os.fstat(stream.fileno())
    if identity(opened) != identity(after):
        raise Refused('file changed while reading: ' + name)
    named = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
    if identity(named) != identity(after):
        raise Refused('file changed after reading: ' + name)
    return raw, identity(after)


def run(args):
    required = ('O_NOFOLLOW', 'O_DIRECTORY', 'O_NONBLOCK')
    if (not all(hasattr(os, key) for key in required)
            or not all(fn in os.supports_dir_fd
                       for fn in (os.open, os.stat, os.unlink))):
        raise Refused('requires Unix no-follow and dir_fd support')
    root = Path(os.path.abspath(__file__)).parent
    with ExitStack() as stack:
        root_fd = open_directory(stack, root)
        inventory_raw, inventory_identity = read_regular(root_fd, 'inventory.json')
        inventory = read_inventory(inventory_raw)
        check_selection(inventory, args.file)
        confirmations = args.confirm_delete or []
        if args.execute:
            if (len(confirmations) != len(set(confirmations))
                    or set(confirmations) != set(args.file)):
                raise Refused('--execute requires matching --confirm-delete for each file')
        elif confirmations:
            raise Refused('--confirm-delete only allowed with --execute')
        archive_fd = os.open('archive', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                             dir_fd=root_fd)
        stack.callback(os.close, archive_fd)
        plans = []
        for name in args.file:
            raw, metadata = read_regular(archive_fd, name)
            plans.append((name, metadata, hashlib.sha256(raw).hexdigest()))
        # No unlink until every selected file and inventory has been revalidated.
        current_raw, current_identity = read_regular(root_fd, 'inventory.json')
        if (current_raw != inventory_raw or current_identity != inventory_identity):
            raise Refused('inventory changed during preflight')
        for name, metadata, digest in plans:
            raw, current = read_regular(archive_fd, name)
            if current != metadata or hashlib.sha256(raw).hexdigest() != digest:
                raise Refused('file changed during preflight: ' + name)
        for name, metadata, digest in plans:
            print(json.dumps({'action': 'delete' if args.execute else 'would-delete',
                              'path': str(root / 'archive' / name),
                              'bytes': metadata[4], 'sha256': digest}))
        if args.execute:
            for name, metadata, digest in plans:
                current = os.stat(name, dir_fd=archive_fd, follow_symlinks=False)
                if identity(current) != metadata:
                    raise Refused('file changed before deletion: ' + name)
                os.unlink(name, dir_fd=archive_fd)
                print(json.dumps({'deleted': name}), flush=True)
        else:
            print('DRY RUN: no files deleted')
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--file', action='append', default=[], metavar='NAME')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--dry-run', action='store_true')
    mode.add_argument('--execute', action='store_true')
    parser.add_argument('--confirm-delete', action='append', metavar='NAME')
    try:
        return run(parser.parse_args())
    except (Refused, OSError, UnicodeError, json.JSONDecodeError) as exc:
        print('REFUSED: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
