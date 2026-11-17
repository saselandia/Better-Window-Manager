# SPDX-License-Identifier: GPL-2.0-or-later
"""Native adapter transactions must serialize and revalidate after contention."""
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
SCRIPTS=ROOT/'config/hypr/skins/plasma/scripts'
spec=importlib.util.spec_from_file_location('r4_guard_manager',SCRIPTS/'kwin-window.py')
manager=importlib.util.module_from_spec(spec);spec.loader.exec_module(manager)
from native_guard import action_lock


class NativeGuardTest(unittest.TestCase):
    def test_lock_contends_and_is_reusable_without_unlinking(self):
        with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,{'XDG_RUNTIME_DIR':tmp}):
            with action_lock():
                inode=(Path(tmp)/'bwm-r4-native-actions.lock').stat().st_ino
                with self.assertRaises(TimeoutError):
                    with action_lock(timeout=.02):self.fail('Overlapping transaction')
            with action_lock():self.assertEqual((Path(tmp)/'bwm-r4-native-actions.lock').stat().st_ino,inode)

    def test_nonprivate_runtime_and_linked_or_permissive_lock_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,{'XDG_RUNTIME_DIR':tmp}):
            root=Path(tmp);root.chmod(0o755)
            with self.assertRaises(ValueError):
                with action_lock():self.fail('Nonprivate runtime accepted')
            root.chmod(0o700);target=root/'target';target.touch(mode=0o600)
            alias=root/'alias';alias.symlink_to(root,target_is_directory=True)
            with patch.dict(os.environ,{'XDG_RUNTIME_DIR':str(alias)}),self.assertRaises(ValueError):
                with action_lock():self.fail('Symlinked runtime accepted')
            lock=root/'bwm-r4-native-actions.lock';lock.symlink_to(target)
            with self.assertRaises(OSError):
                with action_lock():self.fail('Symlink accepted')
            lock.unlink();os.link(target,lock)
            with self.assertRaises(ValueError):
                with action_lock():self.fail('Hardlink accepted')
            lock.unlink();lock.touch(mode=0o644)
            with self.assertRaises(ValueError):
                with action_lock():self.fail('Permissive lock accepted')
            self.assertEqual(lock.stat().st_mode&0o777,0o644) # No silent chmod of foreign authority.

    def test_native_identity_and_skin_guards_precede_mutation(self):
        with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,{'XDG_RUNTIME_DIR':tmp,'XDG_CONFIG_HOME':tmp}):
            config=Path(tmp)/'illogical-impulse';config.mkdir();path=config/'config.json'
            path.write_text('{"appearance":{"bwmTheme":"plasma"}}')
            with patch.object(manager,'find_client',return_value={'address':'0xabc','pid':123}), \
                 patch.object(manager.bwm_windows,'process_generation',return_value='new'),patch.object(manager,'focus') as focus:
                self.assertEqual(manager.main(['--native-serialized','--expected-generation','old','--pid','123','focus','0xabc']),1)
                focus.assert_not_called()
                self.assertEqual(manager.main(['--native-serialized','--expected-generation','new','--pid','123','focus','0xabc']),0)
                focus.assert_called_once();focus.reset_mock()
                path.write_text('{"appearance":{"bwmTheme":"retro"}}')
                self.assertEqual(manager.main(['--native-serialized','--pid','123','focus','0xabc']),1)
                focus.assert_not_called()

    def test_waiting_process_rechecks_skin_and_generation_after_lock_release(self):
        child='''import importlib.util,os,sys
from pathlib import Path
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('guarded',sys.argv[1]);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
root=Path(os.environ['XDG_RUNTIME_DIR'])
with patch.object(m,'find_client',return_value={'address':'0xabc','pid':123}),patch.object(m.bwm_windows,'process_generation',side_effect=lambda pid:(root/'generation').read_text()),patch.object(m,'focus',side_effect=lambda client:(root/'mutated').touch()):
 print('ready',flush=True)
 raise SystemExit(m.main(['--native-serialized','--expected-generation','old','--pid','123','focus','0xabc']))
'''
        for changed in ('skin','generation'):
            with self.subTest(changed=changed),tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,{'XDG_RUNTIME_DIR':tmp,'XDG_CONFIG_HOME':tmp}):
                root=Path(tmp);(root/'generation').write_text('old');config=root/'illogical-impulse';config.mkdir()
                path=config/'config.json';path.write_text('{"appearance":{"bwmTheme":"plasma"}}')
                with action_lock():
                    process=subprocess.Popen([sys.executable,'-c',child,str(SCRIPTS/'kwin-window.py')],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
                    self.addCleanup(lambda p=process:p.poll() is None and p.kill())
                    self.assertEqual(process.stdout.readline().strip(),'ready')
                    if changed=='skin':path.write_text('{"appearance":{"bwmTheme":"retro"}}')
                    else:(root/'generation').write_text('new')
                stdout,stderr=process.communicate(timeout=3)
                self.assertEqual(process.returncode,1,(stdout,stderr));self.assertFalse((root/'mutated').exists())

    def test_process_death_releases_lock_without_replacing_inode(self):
        child="import sys;sys.path.insert(0,sys.argv[1]);from native_guard import action_lock\nwith action_lock():\n print('locked',flush=True)\n sys.stdin.read(1)"
        with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,{'XDG_RUNTIME_DIR':tmp}):
            with subprocess.Popen([sys.executable,'-c',child,str(SCRIPTS)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True) as process:
                self.assertEqual(process.stdout.readline().strip(),'locked')
                inode=(Path(tmp)/'bwm-r4-native-actions.lock').stat().st_ino
                process.kill();process.wait(timeout=2)
            with action_lock(timeout=.05):self.assertEqual((Path(tmp)/'bwm-r4-native-actions.lock').stat().st_ino,inode)


if __name__=='__main__':unittest.main()
