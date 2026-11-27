"""Run the real startup plugin block against command stubs, never a compositor."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class BreezeStartupTests(unittest.TestCase):
    def startup(self, skin, *, loaded=False, binary=True, fail=False, repeats=1):
        source = (ROOT / 'config/hypr/scripts/autostart.sh').read_text()
        block = source.split('# 9. Preparar Breeze', 1)[1].split('# 9b.', 1)[0]
        block = '# 9. Preparar Breeze' + block
        # Redirect only this excerpt's fixture paths. The real HOME and all session
        # variables stay untouched; external commands below are shell stubs.
        block = block.replace('$HOME', '${BWM_TEST_ROOT}')
        with tempfile.TemporaryDirectory(prefix='bwm-startup-test-') as tmp:
            root = Path(tmp)
            hypr = root / '.config/hypr'
            (hypr / 'modules').mkdir(parents=True)
            (hypr / 'plugins').mkdir()
            (hypr / 'modules/theme.lua').write_text(f'local theme = {{ name = "{skin}" }}\n')
            if binary:
                (hypr / 'plugins/breezebars.so').touch()
            if loaded:
                (root / 'loaded').touch()
            stubs = r'''
set -euo pipefail
sleep() { :; }
python3() { printf 'python %s\n' "$*" >> "$BWM_TEST_ROOT/calls"; }
hyprctl() {
    printf 'hyprctl %s\n' "$*" >> "$BWM_TEST_ROOT/calls"
    if [ "$*" = 'plugin list' ]; then
        if [ -f "$BWM_TEST_ROOT/loaded" ]; then printf 'Plugin breezebars loaded\n'; fi
    elif [ "$1 $2" = 'plugin load' ]; then
        if [ "$BWM_TEST_FAIL" = 1 ]; then return 1; fi
        : > "$BWM_TEST_ROOT/loaded"
    else
        return 99
    fi
}
'''
            result = subprocess.run(['bash', '-c', stubs + (block + '\nwait\n') * repeats],
                                    env={**os.environ, 'BWM_TEST_ROOT': str(root), 'BWM_TEST_FAIL': str(int(fail))},
                                    text=True, capture_output=True, timeout=5)
            self.assertEqual(result.returncode, 0, result.stderr)
            calls = (root / 'calls').read_text().splitlines() if (root / 'calls').exists() else []
            return calls, result.stderr

    def test_all_initial_skins_preload_but_only_breeze_starts_its_services(self):
        for skin in ('retro', 'default', 'plasma'):
            with self.subTest(skin=skin):
                calls, _ = self.startup(skin)
                loads = [c for c in calls if c.startswith('hyprctl plugin load ')]
                self.assertEqual(len(loads), 1)
                # §255: the opt-in desktop provider decides by itself, in every skin
                provider = [c for c in calls if c.endswith('native-desktops.py startup')]
                self.assertEqual(len(provider), 1)
                helpers = [c for c in calls if c.startswith('python ') and c not in provider]
                expected = ['kde-config-bridge.py enter', 'kde-config-bridge.py start',
                            'decorator.py start', 'kde-shortcuts.py start', 'plasma-host.py start'] if skin == 'plasma' else []
                self.assertEqual([h.rsplit('/', 1)[1] for h in helpers], expected)
                if helpers:
                    self.assertLess(calls.index(helpers[0]), calls.index(loads[0]))

    def test_loaded_plugin_is_not_loaded_again(self):
        for loaded, repeats in ((True, 1), (False, 2)):
            calls, _ = self.startup('retro', loaded=loaded, repeats=repeats)
            self.assertEqual(sum(c.startswith('hyprctl plugin load ') for c in calls), 0 if loaded else 1)
            self.assertFalse(any('plugin unload' in c for c in calls))

    def test_optional_plugin_absent_and_failed_load_do_not_trigger_retries(self):
        calls, _ = self.startup('retro', binary=False)
        self.assertFalse([c for c in calls if not c.endswith('native-desktops.py startup')])
        calls, stderr = self.startup('retro', fail=True)
        self.assertEqual(sum(c.startswith('hyprctl plugin load ') for c in calls), 1)
        self.assertIn('No se pudo cargar breezebars', stderr)

    @unittest.skipUnless(shutil.which('lua'), 'Lua not installed')
    def test_preloaded_bars_are_enabled_only_in_breeze(self):
        source = (ROOT / 'config/hypr/modules/appearance.lua').read_text()
        block = 'if hl.plugin and hl.plugin.breezebars then' + source.split(
            'if hl.plugin and hl.plugin.breezebars then', 1)[1].split('-- XWayland sin escalado', 1)[0]
        for plasma in (True, False):
            prefix = 'local is_plasma = ' + str(plasma).lower() + '''
hl = {plugin = {breezebars = {}}, config = function(config)
    print(tostring(config.plugin.breezebars.enabled))
end}
'''
            result = subprocess.run(['lua', '-'], input=prefix + block, text=True, capture_output=True, timeout=5)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), str(plasma).lower())


if __name__ == '__main__':
    unittest.main()
