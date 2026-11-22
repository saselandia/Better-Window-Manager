"""R7 effects: real KDE stores and bridge, compositor commands replaced in temporary XDG.

No setting or compositor in the user's session is changed by these tests.
"""
import importlib.util
import json
import os
import shutil
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'config/hypr/skins/plasma/scripts'


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class EffectsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.config = self.root / 'config'
        self.config.mkdir()
        self.env = mock.patch.dict(os.environ, {
            'XDG_CONFIG_HOME': str(self.config), 'XDG_STATE_HOME': str(self.root / 'state'),
            'XDG_DATA_HOME': str(self.root / 'data'), 'XDG_CONFIG_DIRS': str(self.root / 'system'),
        })
        self.env.start()
        self.addCleanup(self.env.stop)
        self.b = module('effects_bridge_test', SCRIPTS / 'kde-config-bridge.py')
        self.m = module('effects_native_test', SCRIPTS / 'native-settings.py')
        self.bridge = mock.patch.object(self.m, 'bridge', return_value=self.b)
        self.bridge.start()
        self.addCleanup(self.bridge.stop)
        self.run = mock.patch.object(self.b, 'run', side_effect=lambda argv, **kwargs: subprocess.CompletedProcess(argv, 0, '{}', ''))
        self.calls = self.run.start()
        self.addCleanup(self.run.stop)
        counts = mock.patch.object(self.b.native_workspaces, 'Runtime')
        counts.start()
        self.addCleanup(counts.stop)
        self.b.OPTIONS.parent.mkdir()
        self.b.OPTIONS.write_text('{"appearance":{"bwmTheme":"plasma"}}')
        self.source = self.config / 'kwinrc'
        self.foreign = '# user comment\n[Plugins]\nwobblywindowsEnabled=true\n[Effect-blur]\nSaturation=140\nNoiseStrength=3\n[Unknown][Nested]\nKey[$e]=untouched\n'
        self.source.write_text(self.foreign)
        self.b.enter()
        self.calls.reset_mock()

    def save(self, changes):
        return self.m.apply('effects', dict(revision=self.m.page('effects')['revision'], changes=changes))

    def test_only_implemented_controls_and_native_defaults(self):
        page = self.m.page('effects')
        fields = {f['key']: f for f in page['fields']}
        self.assertEqual(len(fields), 11)
        contract = json.loads((SCRIPTS / 'settings-capabilities.json').read_text())['r7_contract']
        toggles = {key.split('\x1f')[-1][:-7] for key, f in fields.items() if f['type'] == 'bool'}
        self.assertEqual(toggles, set(contract['supported_effects']))
        self.assertTrue(all(f['value'] == f['default'] for f in fields.values()))
        self.assertEqual(fields['kwinrc\x1fEffect-scale\x1fDuration']['value'], 0)
        self.assertEqual(self.b.kwin_settings()['scaleDuration'], 200)

    def test_batch_apply_readback_and_single_reload(self):
        changes = {f['key']: False for f in self.m.page('effects')['fields'] if f['type'] == 'bool'}
        changes.update({'kdeglobals\x1fKDE\x1fAnimationDurationFactor': 0.0625,
                        'kwinrc\x1fEffect-blur\x1fBlurStrength': 7,
                        'kwinrc\x1fEffect-scale\x1fDuration': 350,
                        'kwinrc\x1fEffect-scale\x1fInScale': 0.7,
                        'kwinrc\x1fEffect-scale\x1fOutScale': 0.9})
        result = self.save(changes)
        self.assertEqual({f['key']: f['value'] for f in result['fields']}, changes)
        self.assertEqual(sum(c.args[0] == ['hyprctl', 'reload'] for c in self.calls.call_args_list), 1)
        lua = self.b.KWIN_STATE.read_text()
        for value in ('blur = false', 'scaleEnabled = false', 'maximizeEnabled = false',
                      'slideEnabled = false', 'fadingPopupsEnabled = false', 'slidingPopupsEnabled = false',
                      'scaleDuration = 350', 'blurStrength = 7', 'animationFactor = 0.0625'):
            self.assertIn(value, lua)
        for line in self.foreign.splitlines():
            self.assertIn(line, self.source.read_text())
        self.assertNotIn('Enabled=False', self.source.read_text())

    def test_defaults_roundtrip_and_noop_no_reload(self):
        self.save({'kwinrc\x1fEffect-scale\x1fDuration': 450, 'kwinrc\x1fPlugins\x1fscaleEnabled': False})
        self.save({f['key']: f['default'] for f in self.m.page('effects')['fields']})
        self.assertEqual(self.b.merged('kwinrc')['Effect-scale']['Duration'], '0')
        self.assertEqual(self.b.kwin_settings()['scaleDuration'], 200)
        self.assertTrue(self.b.kwin_settings()['scaleEnabled'])
        self.calls.reset_mock()
        self.save({})
        self.assertFalse(any(c.args[0] == ['hyprctl', 'reload'] for c in self.calls.call_args_list))

    def test_external_edit_conflicts_preserve_both_files(self):
        page = self.m.page('effects')
        self.source.write_text(self.source.read_text() + '\n[Effect-scale]\nInScale=0.65\n')
        before = self.source.read_bytes()
        with self.assertRaisesRegex(ValueError, 'cambió'):
            self.m.apply('effects', dict(revision=page['revision'], changes={'kwinrc\x1fPlugins\x1fscaleEnabled': False}))
        self.assertEqual(before, self.source.read_bytes())

    def test_invalid_batch_writes_nothing(self):
        before = self.source.read_bytes()
        for changes in ({'kwinrc\x1fEffect-blur\x1fSaturation': 160},
                        {'kwinrc\x1fPlugins\x1fscaleEnabled': 'false'},
                        {'kwinrc\x1fEffect-scale\x1fInScale': float('nan')},
                        {'kwinrc\x1fEffect-scale\x1fDuration': 5001},
                        {'kwinrc\x1fEffect-blur\x1fBlurStrength': 0}):
            with self.assertRaises(ValueError):
                self.save({'kwinrc\x1fPlugins\x1fblurEnabled': False, **changes})
        self.assertEqual(before, self.source.read_bytes())
        self.assertFalse(any(c.args[0] == ['hyprctl', 'reload'] for c in self.calls.call_args_list))

    def test_reload_failure_is_error_with_pending_retry(self):
        def run(argv, **kwargs):
            return subprocess.CompletedProcess(argv, int(argv == ['hyprctl', 'reload']), '{}', '')
        with mock.patch.object(self.b, 'run', side_effect=run):
            with self.assertRaisesRegex(RuntimeError, 'recarga pendiente'):
                self.save({'kwinrc\x1fPlugins\x1fscaleEnabled': False})
        self.assertTrue(self.b.load_json(self.b.META)['pendingReload'])
        self.assertFalse(self.b.kwin_settings()['scaleEnabled'])
        self.b.reconcile()
        self.assertNotIn('pendingReload', self.b.load_json(self.b.META))

    def test_kdedefaults_and_skin_guard(self):
        defaults = self.config / 'kdedefaults/kwinrc'
        defaults.parent.mkdir()
        defaults.write_text('[Plugins]\nscaleEnabled=false\n[Effect-scale]\nDuration=280\n')
        page = self.m.page('effects')
        self.assertFalse(next(f['value'] for f in page['fields'] if f['key'].endswith('\x1fscaleEnabled')))
        self.save({'kwinrc\x1fPlugins\x1fscaleEnabled': True})
        self.assertIn('scaleEnabled=false', defaults.read_text())
        for skin in ('retro', 'default'):
            self.b.OPTIONS.write_text(json.dumps({'appearance': {'bwmTheme': skin}}))
            with self.assertRaisesRegex(ValueError, 'Breeze activo'):
                self.m.page('effects')

    @unittest.skipUnless(os.environ.get('BWM_RUN_QML_TESTS') == '1', 'QML opcional')
    def test_qml_page_apply_defaults_reset_and_error(self):
        # Copy only the new view/store; replace its controller path in this private copy.
        # The real Python controller still executes, with compositor commands stubbed.
        ui = self.root / 'ui'
        (ui / 'pages').mkdir(parents=True)
        backend = self.root / 'controller.py'
        backend.write_text(f'''import importlib.util, json, pathlib, subprocess, sys
spec = importlib.util.spec_from_file_location('r7_native', {str(SCRIPTS / 'native-settings.py')!r})
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
b = m.bridge()
b.run = lambda args, **kwargs: subprocess.CompletedProcess(args, 0, '{{}}', '')
from types import SimpleNamespace
b.native_workspaces.Runtime = lambda *args, **kwargs: SimpleNamespace(tick=lambda **kwargs: None)
m.bridge = lambda: b
counter = pathlib.Path({str(self.root / 'saves')!r})
if sys.argv[-1] == 'save':
 count = int(counter.read_text()) + 1 if counter.exists() else 1
 counter.write_text(str(count))
 if count == 2:
  print(json.dumps(dict(error='R7 simulated save failure'))); sys.exit(1)
sys.exit(m.main())
''')
        settings = ROOT / 'config/quickshell/ii/modules/plasma/settings'
        source = (settings / 'EffectsStore.qml').read_text()
        source = source.replace('Quickshell.env("HOME") + "/.config/hypr/skins/plasma/scripts/native-settings.py"', json.dumps(str(backend)))
        (ui / 'EffectsStore.qml').write_text(source)
        shutil.copy(settings / 'pages/DesktopEffects.qml', ui / 'pages')
        shutil.copy(settings / 'ModuleView.qml', ui)
        (ui / 'SettingsState.qml').write_text('''pragma Singleton
import QtQuick
QtObject {
    property bool spanish: true
    property bool unsavedChanges: false
    property bool defaultsIndicatorsVisible: false
    property var askBeforeLeaving: null
    property var kcmApi: ({})
    property var current: ({entry: {kind: "page", component: "ui/pages/DesktopEffects.qml"}})
    function label(entry) { return "Efectos de escritorio"; }
}
''')
        (ui / 'SettingsI18n.qml').write_text('pragma Singleton\nimport QtQuick\nQtObject { function i18n(text) { return text; } }\n')
        (ui / 'qmldir').write_text('singleton SettingsState 1.0 SettingsState.qml\nsingleton SettingsI18n 1.0 SettingsI18n.qml\nEffectsStore 1.0 EffectsStore.qml\nModuleView 1.0 ModuleView.qml\n')
        harness = self.root / 'probe.qml'
        harness.write_text('''import QtQuick
import QtQuick.Controls as QQC2
import Quickshell
import "ui" as Settings
QQC2.ApplicationWindow {
    width: 960; height: 800; visible: true
    Settings.ModuleView { id: page; anchors.fill: parent; headerHeight: 40 }
    property int stage: 0
    property bool navigated: false
    function check(ok, message) { if (!ok) throw new Error(message); }
    Timer {
        interval: 50; running: true; repeat: true
        onTriggered: {
            const s = page.kcm;
            if (!s) return;
            if (s.busy) return;
            try {
                if (stage === 0) {
                    check(s.ready && s.error === "", "initial load: " + s.error);
                    check(s.fields.length === 11 && !s.needsSave, "fields");
                    s.setValue("kwinrc\\u001fPlugins\\u001fblurEnabled", false);
                    s.setValue("kdeglobals\\u001fKDE\\u001fAnimationDurationFactor", 0.0625);
                    check(s.needsSave, "draft changes");
                    s.save(); stage = 1;
                } else if (stage === 1) {
                    check(s.error === "" && !s.needsSave, "apply: " + s.error);
                    s.defaults();
                    check(s.representsDefaults && s.needsSave, "defaults staged");
                    s.load(); stage = 2;
                } else if (stage === 2) {
                    check(!s.needsSave && !s.representsDefaults, "reset");
                    s.defaults();
                    page.askBeforeLeaving(() => { navigated = true; });
                    const dialog = Array.from(page.data).find(o => o.objectName === "unsavedChangesDialog");
                    check(!!dialog, "unsaved dialog");
                    dialog.applied();
                    check(!navigated, "must wait for controller before leaving");
                    stage = 3;
                } else if (stage === 3) {
                    check(s.error.indexOf("simulated save failure") >= 0 && s.needsSave, "error must preserve draft");
                    check(!navigated && Settings.SettingsState.unsavedChanges, "failed save must not navigate");
                    s.load(); stage = 4;
                } else if (stage === 4) {
                    check(s.error === "" && !s.needsSave, "reload after failure");
                    s.defaults();
                    page.askBeforeLeaving(() => { navigated = true; });
                    Array.from(page.data).find(o => o.objectName === "unsavedChangesDialog").applied();
                    check(!navigated, "success must also wait for readback");
                    stage = 5;
                } else {
                    check(s.error === "" && !s.needsSave && navigated, "successful save must complete navigation");
                    console.log("R7QMLPASS"); Qt.quit();
                }
            } catch (e) { console.error("R7QMLFAIL " + e); Qt.quit(); }
        }
    }
    Timer { interval: 20000; running: true; onTriggered: { console.error("R7QMLFAIL timeout"); Qt.quit(); } }
}
''')
        env = dict(os.environ, QT_QUICK_CONTROLS_STYLE='org.kde.desktop', QT_QPA_PLATFORM='offscreen')
        env.pop('QT_QPA_PLATFORMTHEME', None)
        run = subprocess.run(['qs', '-p', str(harness)], env=env, capture_output=True, text=True, timeout=30)
        output = run.stdout + run.stderr
        self.assertIn('R7QMLPASS', output, output)
        self.assertNotIn('R7QMLFAIL', output, output)
        for error in ('TypeError', 'ReferenceError', 'Cannot assign', 'Unable to assign', 'is not a type'):
            self.assertNotIn(error, output, output)
        self.assertTrue(self.b.kwin_settings()['blur'])
        self.assertEqual(self.b.kwin_settings()['animationFactor'], 1)
        self.assertEqual((self.root / 'saves').read_text(), '3')


if __name__ == '__main__':
    unittest.main()
