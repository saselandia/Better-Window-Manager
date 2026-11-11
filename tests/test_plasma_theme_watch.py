"""KConfig defaults and live local overrides, using only temporary XDG files."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
SHELL = ROOT / 'config/quickshell/ii'


@unittest.skipUnless(os.environ.get('BWM_RUN_QML_TESTS') == '1', 'optional QML file watcher check')
class ThemeWatchTest(unittest.TestCase):
    def test_kde_defaults_and_local_change_are_visible_without_restart(self):
        with tempfile.TemporaryDirectory(prefix='bwm-f13-theme-') as folder:
            base = Path(folder)
            config = base / 'config'
            (config / 'kdedefaults').mkdir(parents=True)
            (config / 'kdedefaults/kdeglobals').write_text('[General]\nColorScheme=FromGlobalTheme\n[Icons]\nTheme=global-icons\n')
            (config / 'kdedefaults/plasmarc').write_text('[Theme]\nname=global-style\n')
            (config / 'kdeglobals').write_text('[Icons]\nTheme=user-icons\n')
            probe = SHELL / f'zz_f13_theme_watch_{os.getpid()}.qml'
            # No windows, services, IPC, authentication or desktop actions.
            probe.write_text('''import QtQuick
import Quickshell
import qs.modules.plasma.theme
Scope {
 Component.onCompleted: console.log("INIT", PlasmaTheme.colorScheme)
 property bool seenDefaults: false
 Timer {interval:100;running:true;repeat:true;onTriggered:{
  if (!seenDefaults && PlasmaTheme.colorScheme === "FromGlobalTheme") {
   seenDefaults = true;
   console.log("DEFAULTS",JSON.stringify({scheme:PlasmaTheme.colorScheme,style:PlasmaTheme.desktopTheme,icons:PlasmaTheme.iconTheme}));
  }
  if (seenDefaults && PlasmaTheme.colorScheme === "LocalOverride") {
   console.log("CHANGED",PlasmaTheme.colorScheme);Qt.quit();
  }
 }}
 Timer {interval:8000;running:true;onTriggered:Qt.quit()}
}
''')
            env = dict(os.environ, XDG_CONFIG_HOME=str(config), XDG_CONFIG_DIRS=str(base / 'system'))
            try:
                with (base / 'run.log').open('w') as log:
                    process = subprocess.Popen(['qs', '-p', str(probe)], env=env, stdout=log, stderr=subprocess.STDOUT)
                    try:
                        deadline = time.monotonic() + 6
                        while time.monotonic() < deadline:
                            output = (base / 'run.log').read_text()
                            if 'DEFAULTS {' in output or process.poll() is not None:
                                break
                            time.sleep(0.05)
                        (config / 'kdeglobals').write_text('[General]\nColorScheme=LocalOverride\n[Icons]\nTheme=user-icons\n')
                        process.wait(timeout=8)
                    finally:
                        if process.poll() is None:
                            process.terminate()
                            process.wait(timeout=3)
                output = (base / 'run.log').read_text()
                line = next((line.split('DEFAULTS ', 1)[1] for line in output.splitlines() if 'DEFAULTS {' in line), '{}')
                self.assertEqual(json.loads(line), {'scheme':'FromGlobalTheme','style':'global-style','icons':'user-icons'}, output)
                self.assertIn('CHANGED LocalOverride', output)
                for error in ('TypeError', 'ReferenceError', 'is not a type'):
                    self.assertNotIn(error, output)
            finally:
                probe.unlink(missing_ok=True)
