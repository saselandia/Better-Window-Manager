"""Store tooling must fail closed before Qt/network and contain legacy KNS writes."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('store_compat', ROOT / 'src/bwm-plasma-host/store-compat.py')
store = importlib.util.module_from_spec(spec); spec.loader.exec_module(store)


class StoreIsolationTest(unittest.TestCase):
    def test_shared_or_non_temporary_roots_rejected(self):
        with tempfile.TemporaryDirectory(prefix='bwm-store-guard-') as tmp:
            root = Path(tmp)
            self.assertEqual(store.private_root(root), root)
            root.chmod(0o755)
            with self.assertRaises(ValueError): store.private_root(root)
        with self.assertRaises(ValueError): store.private_root(Path.home())

    @unittest.skipUnless(Path('/usr/bin/bwrap').exists(), 'bubblewrap required')
    def test_dependency_legacy_destination_is_private_and_host_is_read_only(self):
        with tempfile.TemporaryDirectory(prefix='bwm-store-guard-') as tmp, tempfile.TemporaryDirectory(prefix='bwm-store-host-') as outside:
            work = Path(tmp); item = work / 'item'; item.mkdir(mode=0o700)
            sentinel = Path(outside) / 'unchanged'; sentinel.write_text('original')
            env = store.environment(item)
            # The shell tries the same legacy HOME path that KNS dependencies use.
            name = 'bwm-store-isolation-' + work.name
            script = 'printf private > "$HOME/.icons/$1"; if printf changed > "$2" 2>/dev/null; then exit 4; fi'
            reply = subprocess.run(store.sandbox(work, item, ['/bin/sh', '-c', script, 'guard', name, sentinel]),
                                   env=env, capture_output=True, text=True)
            self.assertEqual(reply.returncode, 0, reply.stderr)
            self.assertEqual((item / 'data/icons' / name).read_text(), 'private')
            self.assertFalse((Path.home() / '.icons' / name).exists())
            self.assertEqual(sentinel.read_text(), 'original')

    def test_item_cannot_escape_work_directory(self):
        with tempfile.TemporaryDirectory(prefix='bwm-store-a-') as a, tempfile.TemporaryDirectory(prefix='bwm-store-b-') as b:
            with self.assertRaises(ValueError): store.sandbox(Path(a), Path(b), ['/bin/true'])

    def test_review_digest_changes_for_code_and_symlink_changes(self):
        with tempfile.TemporaryDirectory(prefix='bwm-store-review-') as tmp:
            root = Path(tmp); code = root / 'main.qml'; code.write_text('Item {}')
            before = store.tree_hash(root); code.write_text('Item { Component.onCompleted: action() }')
            self.assertNotEqual(before, store.tree_hash(root))
            code.unlink(); code.symlink_to('a'); before = store.tree_hash(root)
            code.unlink(); code.symlink_to('b'); self.assertNotEqual(before, store.tree_hash(root))

    def test_native_client_rejects_daily_roots_before_qt_initializes(self):
        binary = ROOT / 'build/bwm-plasma-host-tests/kns-store'
        if not binary.exists(): self.skipTest('Build test-only kns-store first')
        env = dict(os.environ, XDG_CONFIG_HOME=str(Path.home() / '.config'), QT_QPA_PLATFORM='invalid-qt-platform-for-guard')
        reply = subprocess.run([binary, 'plasmoids', 'search', ''], env=env, capture_output=True, text=True, timeout=5)
        self.assertEqual(reply.returncode, 2, reply.stderr)
        self.assertIn('disposable XDG roots', reply.stderr)
        self.assertNotIn('Qt platform plugin', reply.stderr)


if __name__ == '__main__': unittest.main()
