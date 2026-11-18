# SPDX-License-Identifier: GPL-2.0-or-later
"""Persistent profile choice must stay separate from live panel activation."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'src/bwm-plasma-host/profile-selection.py'
PREVIEW=SCRIPT.with_name('preview-isolated.py')


class ProfileSelectionTest(unittest.TestCase):
    def test_metadata_commands_use_private_offscreen_environment_and_keep_state_authority(self):
        for action,expected in ((['status'],['--profile-selection-info']),
                (['select','my-panel','--revision','0'],['--select-profile','my-panel','0']),
                (['clear','--revision','23'],['--clear-profile-selection','23'])):
            with self.subTest(action=action),tempfile.TemporaryDirectory() as temporary:
                root=Path(temporary);observed=root/'observed';binary=root/'probe'
                binary.write_text('#!'+sys.executable+'\nimport json,os,sys\nfrom pathlib import Path\n'
                    +'assert sys.argv[1:]=='+repr(expected)+'\n'
                    +'assert not any(k.startswith("BWM_R4_") for k in os.environ)\n'
                    +'assert not any(k in os.environ for k in ("DISPLAY","WAYLAND_DISPLAY","WAYLAND_SOCKET","HYPRLAND_INSTANCE_SIGNATURE","KDESYCOCA"))\n'
                    +'assert os.environ["QT_QPA_PLATFORM"]=="offscreen"\n'
                    +'assert os.environ["XDG_STATE_HOME"]=='+repr(str(root/'state'))+'\n'
                    +'assert os.environ["XDG_DATA_DIRS"].split(os.pathsep)[0]=='+repr(str(root/'original-data'))+'\n'
                    +'assert not Path(os.environ["DBUS_SESSION_BUS_ADDRESS"].split("unix:path=",1)[1]).exists()\n'
                    +'Path('+repr(str(observed))+').write_text(json.dumps([os.environ[k] for k in ("XDG_CONFIG_HOME","XDG_DATA_HOME","XDG_CACHE_HOME","XDG_RUNTIME_DIR")]))\n'
                    +'print(json.dumps({"activationAllowed":False,"replacementReady":False}))\n');binary.chmod(0o700)
                reply=subprocess.run([sys.executable,str(SCRIPT),'--binary',str(binary),*action],
                    env=dict(os.environ,XDG_STATE_HOME=str(root/'state'),XDG_DATA_HOME=str(root/'original-data'),
                        DISPLAY='fake',WAYLAND_DISPLAY='fake',WAYLAND_SOCKET='77',HYPRLAND_INSTANCE_SIGNATURE='fake',KDESYCOCA='fake',BWM_R4_TASK_ACTIONS='1'),
                    capture_output=True,text=True,timeout=5)
                self.assertEqual(reply.returncode,0,reply.stderr);self.assertFalse(json.loads(reply.stdout)['activationAllowed'])
                self.assertTrue(all(not Path(path).exists() for path in json.loads(observed.read_text())))

    def test_selection_rejects_paths_and_invalid_revisions_before_invoking_native_code(self):
        cases=[['select',name,'--revision','0'] for name in ('../escape','/absolute','.selection','a/b','with space','')]
        cases += [['clear','--revision',revision] for revision in ('-1','9007199254740992','1.5','true')]
        cases += [['select','panel'],['clear']]
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);marker=root/'executed';binary=root/'probe'
            binary.write_text('#!'+sys.executable+'\nfrom pathlib import Path\nPath('+repr(str(marker))+').touch()\n');binary.chmod(0o700)
            for args in cases:
                with self.subTest(args=args):
                    reply=subprocess.run([sys.executable,str(SCRIPT),'--binary',str(binary),*args],capture_output=True,text=True,timeout=5)
                    self.assertEqual(reply.returncode,2);self.assertFalse(marker.exists());self.assertNotIn('Traceback',reply.stderr)

    def test_native_conflict_is_reported_without_a_retry_or_preview(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);marker=root/'calls';binary=root/'probe'
            binary.write_text('#!'+sys.executable+'\nimport sys\nfrom pathlib import Path\n'
                +'with Path('+repr(str(marker))+').open("a") as f:f.write("called\\n")\n'
                +'sys.stderr.write("Profile selection revision changed; inspect it before retrying\\n")\nraise SystemExit(7)\n');binary.chmod(0o700)
            reply=subprocess.run([sys.executable,str(SCRIPT),'--binary',str(binary),'select','panel','--revision','4'],capture_output=True,text=True,timeout=5)
            self.assertEqual(reply.returncode,2);self.assertIn('revision changed',reply.stderr);self.assertNotIn('Traceback',reply.stderr)
            self.assertEqual(marker.read_text(),'called\n')

    def test_selected_preview_opens_in_native_host_without_resolving_a_stale_path(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);binary=root/'probe';observed=root/'observed';runtime=root/'runtime';runtime.mkdir(mode=0o700)
            binary.write_text('#!'+sys.executable+'\nimport json,sys\nfrom pathlib import Path\n'
                +'Path('+repr(str(observed))+').write_text(json.dumps(sys.argv[1:]))\nraise SystemExit(8)\n');binary.chmod(0o700)
            reply=subprocess.run([sys.executable,str(PREVIEW),'--binary',str(binary),'--selected-profile','--follow-skin'],
                env=dict(os.environ,XDG_RUNTIME_DIR=str(runtime),XDG_CONFIG_HOME=str(root/'config')),
                capture_output=True,text=True,timeout=5)
            self.assertEqual(reply.returncode,1,reply.stderr);self.assertEqual(json.loads(observed.read_text()),['--serve-selected-profile'])
            self.assertNotIn('Traceback',reply.stderr);self.assertFalse((runtime/'bwm-plasma-host-preview/active.json').exists())

    def test_selected_profile_obeys_saved_profile_preview_restrictions(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);binary=root/'unused';binary.write_text('#!/bin/false\n');binary.chmod(0o700)
            for args in ([],['--follow-skin','--output','Fixture output'],['--follow-skin','--all-desktops','--task-actions'],
                         ['--follow-skin','--session-appearance'],['--follow-skin','--native-panel','--instances','2'],
                         ['--export-as','new'],['--recover-snapshot','a1'*16]):
                with self.subTest(args=args):
                    reply=subprocess.run([sys.executable,str(PREVIEW),'--binary',str(binary),'--selected-profile',*args],capture_output=True,text=True,timeout=5)
                    self.assertEqual(reply.returncode,2);self.assertNotIn('Traceback',reply.stderr)


if __name__=='__main__':unittest.main()
