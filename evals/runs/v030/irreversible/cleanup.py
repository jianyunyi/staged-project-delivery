#!/usr/bin/env python3
"""Explicit flat-archive cleanup. Default dry-run; execute needs prior authorization."""
import argparse
import json
import os
from pathlib import Path
import stat
import sys

ROOT = Path(__file__).resolve().parent


def name_ok(name):
    return (isinstance(name, str) and bool(name) and name not in ('.', '..')
            and '/' not in name and '\\' not in name and '\x00' not in name)


def load_inventory():
    fd = os.open(ROOT / 'inventory.json', os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, 'r', encoding='utf-8') as source:
        if not stat.S_ISREG(os.fstat(source.fileno()).st_mode):
            raise ValueError('inventory must be a regular file')
        data = json.load(source)
    if not isinstance(data, dict) or set(data) != {'expired', 'keep'}:
        raise ValueError('inventory must contain exactly expired and keep')
    for key in ('expired', 'keep'):
        values = data[key]
        if (not isinstance(values, list) or not all(name_ok(x) for x in values)
                or len(set(values)) != len(values)):
            raise ValueError('invalid inventory names or duplicates')
    if set(data['expired']) & set(data['keep']):
        raise ValueError('expired and keep overlap')
    return data


def identity(info):
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def run(names, execute=False):
    if not names or not all(name_ok(x) for x in names):
        raise ValueError('explicit archive basenames required; paths rejected')
    if len(set(names)) != len(names):
        raise ValueError('duplicate requested names')
    data = load_inventory()
    for name in names:
        if name in data['keep']:
            raise ValueError('protected file: ' + name)
        if name not in data['expired']:
            raise ValueError('not listed as expired: ' + name)
    fd = os.open(ROOT / 'archive', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        checked = []
        for name in names:
            info = os.stat(name, dir_fd=fd, follow_symlinks=False)
            if not stat.S_ISREG(info.st_mode):
                raise ValueError('not a regular non-symlink file: ' + name)
            checked.append((name, identity(info)))
        # Validate the entire batch before any unlink call.
        for name, original in checked:
            current = os.stat(name, dir_fd=fd, follow_symlinks=False)
            if not stat.S_ISREG(current.st_mode) or identity(current) != original:
                raise ValueError('file changed during validation: ' + name)
        if not execute:
            for name, original in checked:
                print('DRY-RUN archive/' + name + ' bytes=' + str(original[2]))
            return
        for name, original in checked:
            current = os.stat(name, dir_fd=fd, follow_symlinks=False)
            if not stat.S_ISREG(current.st_mode) or identity(current) != original:
                raise ValueError('file changed before deletion: ' + name)
            os.unlink(name, dir_fd=fd)
            print('DELETED archive/' + name, flush=True)
    finally:
        os.close(fd)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--dry-run', action='store_true')
    mode.add_argument('--execute', action='store_true', help='only after user authorization')
    parser.add_argument('files', nargs='+', help='explicit expired basenames')
    args = parser.parse_args(argv)
    try:
        run(args.files, execute=args.execute)
    except (OSError, ValueError) as error:
        print('REFUSED: ' + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
