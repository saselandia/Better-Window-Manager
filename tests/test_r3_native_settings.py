"""R3 adapters: isolated stores and controller fixtures; no compositor or power actions."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class NativeSettingsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.config = Path(self.tmp.name)
        self.env = mock.patch.dict(os.environ, {'XDG_CONFIG_HOME': str(self.config)})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.m = module('native_settings_test', ROOT / 'config/hypr/skins/plasma/scripts/native-settings.py')
        self.shared = module('shared_settings_test', ROOT / 'config/hypr/scripts/bwm-shared-settings.py')

    def test_idle_actual_store_reopen_three_skins_preserves_foreign(self):
        p = self.config / 'illogical-impulse/config.json'
        p.parent.mkdir()
        p.write_text(json.dumps({'appearance': {'bwmTheme': 'plasma'}, 'idle': {'screen': 300, 'lock': 600, 'suspend': 0}, 'unknown': {'key': 42}}))
        def command(script, action, data):
            self.assertEqual((script, action), ('bwm-shared-settings.py', 'idle'))
            return self.shared.save_idle(json.loads(data))
        current = self.m.page('energy')
        with mock.patch.object(self.m, 'command', side_effect=command):
            reopened = self.m.apply('energy', {'revision': current['revision'], 'changes': {'screen': 900, 'lock': 1200}})
        self.assertEqual({f['key']: f['value'] for f in reopened['fields']}['screen'], 900)
        for skin in ('default', 'retro', 'plasma'):
            data = json.loads(p.read_text()); data['appearance']['bwmTheme'] = skin; p.write_text(json.dumps(data))
            self.assertEqual(self.m.page('energy')['revision'], reopened['revision'])
            self.assertEqual(json.loads(p.read_text())['unknown'], {'key': 42})

    def test_user_locked_idle_not_written(self):
        p = self.config / 'illogical-impulse/config.json'; p.parent.mkdir()
        p.write_text('{"appearance":{"bwmTheme":"plasma"},"idle":{"screen":300}}')
        user = self.config / 'bwm/user/shell.jsonc'; user.parent.mkdir(parents=True)
        user.write_text('{"all":{"idle":{"screen":700}}}')
        before = p.read_bytes()
        with self.assertRaisesRegex(ValueError, 'fijado'):
            self.shared.save_idle({'screen': 900})
        self.assertEqual(before, p.read_bytes())

    def test_cursor_batch_calls_manager_once_and_reads_result(self):
        state = {'theme': 'old', 'size': 24}
        calls = []
        def command(script, action, *args):
            self.assertEqual(script, 'cursor-manager.py')
            calls.append((action, args))
            if action == 'get': return state.copy()
            if action == 'list': return [{'id': 'old', 'name': 'Old'}, {'id': 'third-party', 'name': 'Third Party'}]
            state.update(theme=args[0], size=args[1])
        with mock.patch.object(self.m, 'command', side_effect=command):
            current = self.m.page('cursor')
            self.m.apply('cursor', {'revision': current['revision'], 'changes': {'theme': 'third-party', 'size': 48}})
            self.assertEqual(len([c for c in calls if c[0] == 'apply']), 1)
            self.assertEqual(self.m.page('cursor')['fields'][0]['value'], 'third-party')
            with self.assertRaisesRegex(ValueError, 'cambió'):
                self.m.apply('cursor', {'revision': current['revision'], 'changes': {'size': 40}})

    def test_no_false_success_when_manager_ignores_write(self):
        def command(script, action, *args):
            return {'theme': 'fixed', 'size': 24} if action == 'get' else []
        with mock.patch.object(self.m, 'command', side_effect=command):
            current = self.m.page('cursor')
            with self.assertRaisesRegex(ValueError, 'no confirmó'):
                self.m.apply('cursor', {'revision': current['revision'], 'changes': {'size': 48}})

    def test_screen_batch_uses_descriptions_and_one_apply(self):
        monitors = [dict(description='MSI test', scale=1.0, x=0, y=0, transform=0, workspaces='1-9')]
        calls = []
        def command(script, action, *args):
            calls.append((script, action, args))
            if action == 'apply': monitors[:] = json.loads(args[0])
            return json.loads(json.dumps(monitors))
        with mock.patch.object(self.m, 'command', side_effect=command):
            current = self.m.page('screens')
            self.m.apply('screens', dict(revision=current['revision'], changes={'MSI test\x1fscale': 1.5, 'MSI test\x1fx': -100}))
            self.assertEqual(len([c for c in calls if c[1] == 'apply']), 1)
            self.assertEqual(monitors[0]['scale'], 1.5)

    def test_validation_before_any_controller_write(self):
        specs = dict(revision='r', fields=[dict(key='size', value=24, type='int', min=16, max=96)])
        with mock.patch.object(self.m, 'page', return_value=specs), mock.patch.object(self.m, 'command') as command:
            for changes in ({'size': True}, {'size': 1000}, {'unknown': 'x'}):
                with self.assertRaises(ValueError): self.m.apply('cursor', dict(revision='r', changes=changes))
            command.assert_not_called()

    def test_shortcut_and_startup_delegate_existing_managers(self):
        for category, script, state, key, new, expected in [
            ('shortcuts', 'keybinds-manager.py', [{'id':'test', 'description':'Test','mods':['SUPER'],'key':'x'}], 'test', 'CTRL + y', ('update', '--id', 'test', '--mods', 'CTRL', '--key', 'y')),
            ('startup', 'autostart-manager.py', [{'file':'test.desktop','name':'Test','enabled':True}], 'test.desktop', False, ('toggle', 'test.desktop', 'false'))]:
            calls=[]
            def command(program, *args):
                self.assertEqual(program, script); calls.append(args)
                if args[0] != 'list':
                    if category == 'shortcuts': state[0].update(mods=['CTRL'], key='y')
                    else: state[0]['enabled'] = False
                return state
            with mock.patch.object(self.m,'command', side_effect=command):
                current=self.m.page(category)
                self.m.apply(category, dict(revision=current['revision'],changes={key:new}))
            self.assertIn(expected, calls)

    def test_windows_kde_write_apply_readback_and_skin_cycle(self):
        import subprocess
        with mock.patch.dict(os.environ, {'XDG_STATE_HOME': str(self.config / 'state'), 'XDG_CONFIG_DIRS': str(self.config / 'system')}):
            b = module('r3_window_bridge', ROOT / 'config/hypr/skins/plasma/scripts/kde-config-bridge.py')
        options = self.config / 'illogical-impulse/config.json'; options.parent.mkdir()
        options.write_text('{"appearance":{"bwmTheme":"plasma"}}')
        defaults = self.config / 'kdedefaults/kwinrc'; defaults.parent.mkdir()
        defaults.write_text('[Windows]\nBorderSnapZone=13\n')
        source = self.config / 'kwinrc'; source.write_text('# mine\n[Unknown]\nOption=untouched\n')
        def run(args):
            return subprocess.CompletedProcess(args, 0, 'breezebars' if 'plugins' in args else '{}', '')
        with mock.patch.object(b, 'run', side_effect=run) as calls, mock.patch.object(self.m, 'bridge', return_value=b):
            b.enter()
            current = self.m.page('windows')
            request = dict(revision=current['revision'], changes={'kwinrc\x1fWindows\x1fBorderSnapZone': 29, 'kdeglobals\x1fKDE\x1fAnimationDurationFactor': 0.5})
            calls.reset_mock()
            result = self.m.apply('windows', request)
            self.assertEqual(sum(c.args[0] == ['hyprctl', 'reload'] for c in calls.call_args_list), 1)
            self.assertIn('borderSnap = 29', b.KWIN_STATE.read_text())
            self.assertIn('animationFactor = 0.5', b.KWIN_STATE.read_text())
            self.assertIn('Option=untouched', source.read_text())
            self.assertEqual(defaults.read_text(), '[Windows]\nBorderSnapZone=13\n')
            b.leave()
            options.write_text('{"appearance":{"bwmTheme":"retro"}}')
            with self.assertRaisesRegex(ValueError, 'Breeze activo'): self.m.page('windows')
            options.write_text('{"appearance":{"bwmTheme":"plasma"}}')
            b.enter()
            self.assertEqual(result['revision'], self.m.page('windows')['revision'])

    def test_windows_fail_closed_when_ipc_unavailable(self):
        import subprocess
        b = mock.Mock()
        b.active.return_value = True
        b.run.return_value = subprocess.CompletedProcess([], 1, '', 'denied')
        with mock.patch.object(self.m, 'bridge', return_value=b):
            with self.assertRaisesRegex(ValueError, 'No hay acceso'): self.m.page('windows')
        b.kwin_settings.assert_not_called()

    def test_effect_contract_has_no_installed_equals_supported(self):
        contract=json.loads((ROOT/'config/hypr/skins/plasma/scripts/settings-capabilities.json').read_text())
        self.assertEqual(set(contract['r7_contract']['supported_effects']),
                         {'blur', 'scale', 'maximize', 'slide', 'fadingpopups', 'slidingpopups'})
        self.assertIn('implemented BWM renderer', contract['r7_contract']['capability_rule'])
        self.assertFalse(any(s['starts_service'] for s in contract['service_contracts']))

    def test_open_settings_routes_plasma_to_native_with_aliases_and_fallback(self):
        import subprocess
        open_script = ROOT / 'config/hypr/scripts/open-settings.sh'
        with tempfile.TemporaryDirectory() as tmp:
            t = Path(tmp)
            fake_sys = t / 'fake-systemsettings'
            fake_qs = t / 'fake-qs'
            fake_sys.write_text('#!/usr/bin/env bash\nprintf "SYS:%s|PLUGINS=%s|XDG=%s\\n" "$*" "${QT_PLUGIN_PATH:-}" "${XDG_CONFIG_DIRS:-}"\n')
            fake_qs.write_text('#!/usr/bin/env bash\nprintf "QS:%s|PAGE=%s\\n" "$*" "${SETTINGS_PAGE:-}"\n')
            fake_sys.chmod(0o755)
            fake_qs.chmod(0o755)
            fake_kcm = t / 'bwm/systemsettings/lib/qt6/plugins/plasma/kcms/systemsettings/kcm_bwm_windows.so'
            fake_kcm.parent.mkdir(parents=True)
            fake_kcm.write_text('')
            base_env = {**os.environ, 'XDG_DATA_HOME': str(t), 'BWM_SETTINGS_THEME_OVERRIDE': 'plasma',
                        'BWM_SYSTEMSETTINGS_BIN': str(fake_sys), 'BWM_QS_BIN': str(fake_qs)}
            base_env.pop('BWM_SETTINGS_HOST', None)
            base_env.pop('SETTINGS_PAGE', None)

            def run_open(*args, extra_env=None):
                env = {**base_env, **(extra_env or {})}
                return subprocess.run(['bash', str(open_script), *args], capture_output=True, text=True, check=True, env=env).stdout.strip()

            out = run_open()
            self.assertTrue(out.startswith('SYS:|PLUGINS='), out)
            self.assertIn('settings-profile:', out)
            for alias, expected in [
                ('display', 'kcm_bwm_screens'),
                ('effects', 'kcm_bwm_effects'),
                ('windowbehavior', 'kcm_bwm_windows'),
                ('workspaces', 'kcm_bwm_workspaces'),
                ('keybinds', 'kcm_bwm_shortcuts'),
                ('cursor', 'kcm_bwm_cursor'),
                ('idle', 'kcm_bwm_energy'),
                ('nightlight', 'kcm_bwm_nightlight'),
                ('defaultapps', 'kcm_bwm_apps'),
                ('autostart', 'kcm_bwm_startup'),
                ('sound', 'kcm_pulseaudio'),
                ('decorations', 'kcm_kwindecoration'),
            ]:
                aliased = run_open(alias)
                self.assertTrue(aliased.startswith(f'SYS:{expected}|'), f'{alias} -> {aliased}')

            for legacy_page in ('background', 'bar', 'services', 'general', 'style', 'about', 'windowrules'):
                leg = run_open(legacy_page)
                self.assertIn('plasmaSettings.qml', leg)
                self.assertIn(f'PAGE={legacy_page}', leg)

            forced_legacy = run_open('display', extra_env={'BWM_SETTINGS_HOST': 'legacy'})
            self.assertIn('plasmaSettings.qml', forced_legacy)

            missing_sys = run_open('display', extra_env={'BWM_SYSTEMSETTINGS_BIN': str(t / 'no-such-bin')})
            self.assertIn('plasmaSettings.qml', missing_sys)

            retro = run_open('bar', extra_env={'BWM_SETTINGS_THEME_OVERRIDE': 'retro'})
            self.assertIn('omarchyMenu settings bar', retro)


if __name__ == '__main__':
    unittest.main()
