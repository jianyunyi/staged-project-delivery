#!/usr/bin/env python3
"""Read-only archive regression tests; unlink is replaced with a recorder."""
import argparse
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

SOURCE_ROOT = Path(__file__).absolute().parent
ROOT = SOURCE_ROOT / 'test-fixtures'
ROOT.mkdir(exist_ok=True)
(ROOT / 'archive').mkdir(exist_ok=True)
fixtures = {'inventory.json': b'{"expired":["expired-a.txt","expired-b.txt"],"keep":["keep.txt"]}',
            'archive/expired-a.txt': b'fixture expired a\n',
            'archive/expired-b.txt': b'fixture expired b\n',
            'archive/keep.txt': b'fixture retained\n'}
for name, data in fixtures.items():
    target = ROOT / name
    if not target.exists():
        with target.open('xb') as stream:
            stream.write(data)
    assert not target.is_symlink() and target.read_bytes() == data, 'fixture changed'
spec = importlib.util.spec_from_file_location('cleanup', SOURCE_ROOT / 'cleanup.py')
cleanup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cleanup)
cleanup.__file__ = str(ROOT / "cleanup.py")  # Exercise fixed-root logic in fixtures.


class SafetyTests(unittest.TestCase):
    def args(self, files=None, execute=False, confirmations=None):
        return argparse.Namespace(file=files or [], execute=execute,
                                  dry_run=not execute, confirm_delete=confirmations)

    def test_valid_dry_run_never_unlinks(self):
        with patch.object(cleanup.os, 'unlink') as unlink, redirect_stdout(io.StringIO()):
            # Keep capability detection tied to original OS function during mocking.
            with patch.object(cleanup.os, 'supports_dir_fd', os.supports_dir_fd | {unlink}):
                self.assertEqual(cleanup.run(self.args(['expired-a.txt', 'expired-b.txt'])), 0)
            unlink.assert_not_called()

    def test_retained_unknown_outside_and_empty(self):
        inventory = {'expired': ['expired-a.txt'], 'keep': ['keep.txt']}
        for names in ([], ['keep.txt'], ['unknown.txt'], ['../keep.txt'],
                      ['/etc/passwd'], ['a/b'], ['a\\b'], ['expired-a.txt'] * 2):
            with self.subTest(names=names), self.assertRaises(cleanup.Refused):
                cleanup.check_selection(inventory, names)

    def test_invalid_inventory(self):
        values = ['{}', '{"expired":[],"keep":[],"other":1}',
                  '{"expired":[],"expired":[],"keep":[]}',
                  '{"expired":["a","a"],"keep":[]}',
                  '{"expired":["a"],"keep":["a"]}',
                  '{"expired":"a","keep":[]}',
                  '{"expired":["../a"],"keep":[]}',
                  '{"expired":[12],"keep":[]}']
        for value in values:
            with self.subTest(value=value), self.assertRaises(cleanup.Refused):
                cleanup.read_inventory(value)

    def test_symlink_directory_hardlink_and_missing_refused(self):
        for mode, links in ((stat.S_IFLNK, 1), (stat.S_IFDIR, 1), (stat.S_IFREG, 2)):
            fake = argparse.Namespace(st_mode=mode, st_nlink=links)
            with patch.object(cleanup.os, 'stat', return_value=fake), self.assertRaises(cleanup.Refused):
                cleanup.read_regular(-1, 'target')
        fd = os.open(ROOT / 'archive', os.O_RDONLY | os.O_DIRECTORY)
        try:
            with self.assertRaises(FileNotFoundError):
                cleanup.read_regular(fd, 'missing.txt')
        finally:
            os.close(fd)

    def test_execute_requires_exact_confirmation(self):
        for confirmations in (None, ['expired-b.txt'], ['expired-a.txt', 'expired-a.txt']):
            with self.subTest(confirmations=confirmations), self.assertRaises(cleanup.Refused):
                cleanup.run(self.args(['expired-a.txt'], True, confirmations))

    def test_mocked_execute_only_selected(self):
        with patch.object(cleanup.os, 'unlink') as unlink, redirect_stdout(io.StringIO()):
            with patch.object(cleanup.os, 'supports_dir_fd', os.supports_dir_fd | {unlink}):
                cleanup.run(self.args(['expired-a.txt'], True, ['expired-a.txt']))
            self.assertEqual(unlink.call_count, 1)
            self.assertEqual(unlink.call_args.args, ('expired-a.txt',))
            self.assertIn('dir_fd', unlink.call_args.kwargs)

    def test_mixed_selection_is_rejected_before_unlink(self):
        with patch.object(cleanup.os, 'unlink') as unlink:
            with patch.object(cleanup.os, 'supports_dir_fd', os.supports_dir_fd | {unlink}):
                with self.assertRaises(cleanup.Refused):
                    cleanup.run(self.args(['expired-a.txt', 'keep.txt'], True,
                                          ['expired-a.txt', 'keep.txt']))
            unlink.assert_not_called()


if __name__ == '__main__':
    archive_before = {f.name: hashlib.sha256(f.read_bytes()).hexdigest()
                      for f in (SOURCE_ROOT / 'archive').iterdir()}
    before = {f.name: hashlib.sha256(f.read_bytes()).hexdigest()
              for f in (ROOT / 'archive').iterdir()}
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(SafetyTests))
    after = {f.name: hashlib.sha256(f.read_bytes()).hexdigest()
             for f in (ROOT / 'archive').iterdir()}
    assert before == after, 'fixture archive changed'
    archive_after = {f.name: hashlib.sha256(f.read_bytes()).hexdigest()
                     for f in (SOURCE_ROOT / 'archive').iterdir()}
    assert archive_before == archive_after, 'actual archive changed'
    print('FIXTURE_UNCHANGED ' + json.dumps(after, sort_keys=True))
    print('ACTUAL_ARCHIVE_UNCHANGED ' + json.dumps(archive_after, sort_keys=True))
    raise SystemExit(0 if result.wasSuccessful() else 1)
