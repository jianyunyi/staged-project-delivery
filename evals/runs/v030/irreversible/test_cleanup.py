"""No actual unlink: all destructive calls are mocked; fixtures retained locally."""
import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import cleanup


class CleanupChecks(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='fixture-', dir=Path(__file__).parent / 'test-fixtures'))
        (self.root / 'archive').mkdir()
        self.data = {'expired': ['a.txt', 'b.txt'], 'keep': ['keep.txt']}
        self.write_inventory()
        for name in ('a.txt', 'b.txt', 'keep.txt'):
            (self.root / 'archive' / name).write_text(name)
        self.root_patch = patch.object(cleanup, 'ROOT', self.root)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)
        self.unlink_patch = patch.object(cleanup.os, 'unlink')
        self.unlink = self.unlink_patch.start()
        self.addCleanup(self.unlink_patch.stop)

    def write_inventory(self):
        (self.root / 'inventory.json').write_text(json.dumps(self.data))

    def invoke(self, names, execute=False):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            cleanup.run(names, execute=execute)
        return out.getvalue()

    def reject(self, names):
        with self.assertRaises((ValueError, OSError)):
            self.invoke(names, execute=True)
        self.unlink.assert_not_called()

    def test_dry_run_ac002(self):
        self.assertIn('DRY-RUN archive/a.txt', self.invoke(['a.txt', 'b.txt']))
        self.unlink.assert_not_called()

    def test_explicit_and_paths_ac003_ac004(self):
        for names in ([], ['a.txt', 'a.txt'], ['unknown'], ['keep.txt'], ['/tmp/a.txt'],
                      ['../a.txt'], ['archive/a.txt'], ['a\\b'], ['.'], ['..']):
            with self.subTest(names=names):
                self.reject(names)

    def test_inventory_ac003(self):
        for data in ({'expired': ['a.txt'], 'keep': ['a.txt']},
                     {'expired': ['a.txt', 'a.txt'], 'keep': []},
                     {'expired': ['../a.txt'], 'keep': []}, [],
                     {'expired': 'a.txt', 'keep': []}):
            self.data = data
            self.write_inventory()
            self.reject(['a.txt'])

    def test_target_symlink_ac004(self):
        (self.root / 'archive' / 'link.txt').symlink_to('keep.txt')
        self.data['expired'].append('link.txt')
        self.write_inventory()
        self.reject(['a.txt', 'link.txt'])

    def test_directory_missing_batch_ac003_ac004(self):
        (self.root / 'archive' / 'directory').mkdir()
        self.data['expired'].extend(['directory', 'missing'])
        self.write_inventory()
        self.reject(['a.txt', 'directory'])
        self.reject(['a.txt', 'missing'])

    def test_archive_symlink_ac004(self):
        (self.root / 'archive').rename(self.root / 'real-archive')
        (self.root / 'archive').symlink_to('real-archive', target_is_directory=True)
        self.reject(['a.txt'])

    def test_inventory_symlink_ac004(self):
        (self.root / 'inventory.json').rename(self.root / 'real-inventory.json')
        (self.root / 'inventory.json').symlink_to('real-inventory.json')
        self.reject(['a.txt'])

    def test_execute_selected_mock_only_ac005(self):
        output = self.invoke(['b.txt'], execute=True)
        self.assertIn('DELETED archive/b.txt', output)
        self.unlink.assert_called_once()
        self.assertEqual(self.unlink.call_args.args, ('b.txt',))
        self.assertIn('dir_fd', self.unlink.call_args.kwargs)
        self.assertTrue((self.root / 'archive' / 'b.txt').exists())

    def test_changed_target_ac005(self):
        real_stat = os.stat
        count = 0
        def changing_stat(*args, **kwargs):
            nonlocal count
            if args and args[0] == 'a.txt':
                count += 1
                if count == 2:
                    (self.root / 'archive' / 'a.txt').write_text('changed')
            return real_stat(*args, **kwargs)
        with patch.object(cleanup.os, 'stat', side_effect=changing_stat):
            self.reject(['a.txt'])

    def test_unlink_failure_ac005(self):
        self.unlink.side_effect = OSError('simulated I/O failure')
        with self.assertRaises(OSError):
            self.invoke(['a.txt', 'b.txt'], execute=True)
        self.assertEqual(self.unlink.call_count, 1)


if __name__ == '__main__':
    (Path(__file__).parent / 'test-fixtures').mkdir(exist_ok=True)
    unittest.main(verbosity=2)
