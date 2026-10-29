"""Opt-in regression tests using real Qt key events in an isolated qs -p window.

Run in the BWM session: BWM_RUN_QML_TESTS=1 python3 -m unittest discover -s tests -p test_retro_ui.py -v
The regular shell is never started or restarted. No user configuration files are edited.
"""
import json
import base64
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import unittest
import uuid

ROOT = Path(__file__).resolve().parents[1]
SHELL = ROOT / 'config/quickshell/ii'

ROOT_QML = r'''//@ pragma UseQApplication
//@ pragma Env QS_NO_RELOAD_POPUP=1
//@ pragma Env QT_QUICK_CONTROLS_STYLE=Basic
import QtQuick
import QtQuick.Controls
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import QtTest
import qs.services
import qs.modules.common
import qs.modules.common.widgets as Widgets
import qs.Commons as Om
import "modules/ii/omarchyMenu" as Source
import "modules/ii/omarchyMenu/omarchy/settings" as Native
import "modules/settings/retro" as Retro
import "modules/ii/omarchyMenu/omarchy/settings/display/Layout.js" as DisplayGeometry
ApplicationWindow {
    id: root
    title: "BWM Retro UI Tests"
    width: 1000
    height: 680
    visible: true
    readonly property color fg: Om.Color.popups.text
    readonly property bool inPage: activeFocusItem === qaText
    Component.onCompleted: { Config.blockWrites = true; Om.Style.bwmScale = 1.15; }
    Retro.SettingsStyle { }
    Widgets.MaterialTextArea { id: qaText; x: 20; y: 20; width: 400; height: 56 }
@HARNESS@
}
'''

HARNESS = r'''
    property var qaGrid: null
    property var qaMenu: null
    property string qaMode: "settings"
    property string qaLaunched: ""
    property string qaSummoned: ""
    Source.AppLibrary { id: qaLibrary }
    Native.SettingsController { id: qaSettings }
    function prepareNativeSettings() {
        const data = {};
        for (const field of qaSettings.fields) {
            if (field.backend) continue;
            const keys = field.path.split(".");
            let src = Config.options;
            for (const key of keys) src = src?.[key];
            if (src === undefined) continue;
            let obj = data;
            for (const key of keys.slice(0, -1)) { if (!obj[key]) obj[key] = {}; obj = obj[key]; }
            obj[keys[keys.length - 1]] = src;
        }
        qaSettings.options = data;
    }
    QtObject {
        id: qaApps
        signal appsChanged()
        function refreshIcons() {}
        function sortedEntries(query) { return qaLibrary.sortedEntries(query); }
        function entryName(entry) { return qaLibrary.entryName(entry); }
        function entrySubtext(entry) { return qaLibrary.entrySubtext(entry); }
        function iconSource(icon) { return qaLibrary.iconSource(icon); }
        function launch(id, label) { root.qaLaunched = id; }
        function remove(id, label) { throw new Error("Uninstall must not run in a text editing test"); }
    }
    QtObject {
        id: qaShell
        readonly property var appLibrary: qaApps
        function summon(id, payload) { root.qaSummoned = id; return id === "bwm.apps"; }
    }
    Widgets.StyledSpinBox { id: qaNumber; x: -500; width: 140; height: 40; from: 0; to: 999; value: 42 }
    TestCase { id: qaDriver; name: "RetroRegression"; when: false }
    IpcHandler {
        target: "retroRegression"
        function visibleTexts(mode: string): string {
            const out = [];
            function visit(item) {
                if (!item || !item.visible) return;
                if (typeof item.text === "string") out.push(item.text);
                for (const child of item.children ?? []) visit(child);
            }
            visit(mode === "grid" ? root.qaGrid.qaCard : root.qaMenu.qaCard);
            return JSON.stringify(out);
        }
        function nativeRoute(route: string, select: string): void { root.qaMenu.open(JSON.stringify({menu:route, select:select})); }
        function nativeState(): string {
            return JSON.stringify({menu:root.qaMenu.activeMenu, selected:root.qaMenu.selectedItemId(), editing:qaSettings.editing?.id ?? "", page:qaSettings.page?.[0] ?? "", pageLoaded:!!root.qaMenu.qaDetails?.pageItem, section:root.qaMenu.qaDetails?.sectionIndex ?? -1, controlFocused:root.qaMenu.qaDetails?.controlFocused ?? false, value:qaSettings.editing ? qaSettings.value(qaSettings.editing) : null, draft:root.qaMenu.qaEditor?.inputItem.text ?? "", option:qaSettings.options.time?.secondPrecision, format:qaSettings.options.time?.format, date:qaSettings.options.time?.dateFormat, battery:qaSettings.options.battery?.low, productionOption:Config.options.time.secondPrecision});
        }
        function displayFixture(payload: string): void {
            const fixture = JSON.parse(Qt.atob(payload));
            const page = root.qaMenu.qaDetails.pageItem;
            page.managerScript = fixture.script;
            page.load(fixture.data);
            page.selectRow(0);
        }
        function displayState(): string {
            const page = root.qaMenu.qaDetails?.pageItem;
            return JSON.stringify({script:page?.managerScript, row:page?.rowIndex, selected:page?.selectedIndex, editing:page?.editingLayout, hints:page?.keyboardHintsVisible, monitors:page?.monitors, logicalSizes:page?.monitors?.map(m => DisplayGeometry.size(m)), dirty:page?.dirty, busy:page?.busy, message:page?.message, error:page?.messageIsError});
        }
        function missingFields(): string {
            return JSON.stringify(qaSettings.fields.filter(f => { if (f.backend) return false; let obj = Config.options; for (const key of f.path.split(".")) obj = obj?.[key]; return obj === undefined; }).map(f => f.path));
        }
        function nativeSection(index: int): void { root.qaMenu.qaDetails.goSection(index); }
        function delayedRoute(route: string): void { root.qaMenu.items = ({}); root.qaMenu.open(JSON.stringify({menu:route})); root.qaMenu.rebuildItemsFromSources(true); }
        function nativeSearch(text: string): void { root.qaMenu.setFilter(text); }
        function nativeValue(path: string): string { let obj = qaSettings.options; for (const key of path.split(".")) obj = obj?.[key]; return JSON.stringify(obj); }
        function state(): string {
            const input = root.qaMode === "grid" ? root.qaGrid.qaInput : root.qaMode === "menu" ? root.qaMenu.qaInput : root.activeFocusItem;
            return JSON.stringify({mode: root.qaMode, ready: Config.ready,
                inPage: root.inPage, text: input?.text ?? "", cursor: input?.cursorPosition ?? -1,
                selected: input?.selectedText ?? "", number: qaNumber.value,
                opened: root.qaMode === "grid" ? root.qaGrid.opened : root.qaMode === "menu" ? root.qaMenu.opened : true,
                count: root.qaMode === "grid" ? root.qaGrid.apps.length : 0,
                index: root.qaMode === "grid" ? root.qaGrid.selectedIndex : 0,
                menu: root.qaGrid?.menuEntry !== null && !!root.qaGrid?.menuEntry, menuIndex: root.qaGrid?.menuIndex ?? -1, launched: root.qaLaunched, summoned: root.qaSummoned, palette: String(Appearance.m3colors.m3onBackground), fg: String(root.fg)});
        }
        function editor(): void { qaText.forceActiveFocus(); }
        function number(): void { qaNumber.contentItem.children[0].forceActiveFocus(); }
        function key(name: string, modifiers: int): void { qaDriver.keyClick(Qt[name], modifiers, 1); }
        function type(text: string): void { for (const ch of text) qaDriver.keyClick(ch, Qt.NoModifier, 1); }
        function openMode(mode: string): void {
            if (root.qaGrid) root.qaGrid.close();
            if (root.qaMenu) root.qaMenu.close();
            root.qaMode = mode;
            if (mode === "settings") { qaDriver.parent = root.contentItem; return; }
            const name = mode === "grid" ? "@GRID@" : "@MENU@";
            let item = mode === "grid" ? root.qaGrid : root.qaMenu;
            if (!item) {
                item = Qt.createComponent(name).createObject(root.contentItem);
                if (!item) throw new Error("Could not create " + mode);
                item.qaPanel.shownKeyboardFocus = WlrKeyboardFocus.None;
                item.qaPanel.shownLayer = WlrLayer.Bottom;
                if (mode === "grid") { item.appLibrary = qaApps; root.qaGrid = item; }
                else { item.shell = qaShell; prepareNativeSettings(); item.settingsAdapter = qaSettings; root.qaMenu = item; }
            }
            qaDriver.parent = item.qaPanel.contentItem;
            if (mode === "grid") item.open(); else item.open("{}");
        }
        function palette(light: bool): void {
            Om.Color.shellValues = {"popups.text": light ? "#151515" : "#eeeeee", "popups.background": light ? "#fafafa" : "#202020"};
        }
        function visual(mode: string): string {
            if (mode === "settings") return "";
            const item = mode === "grid" ? root.qaGrid : root.qaMenu;
            item.qaPanel.shownLayer = WlrLayer.Overlay;
            return JSON.stringify({ x: item.qaPanel.screen.x + item.qaCard.x, y: item.qaPanel.screen.y + item.qaCard.y, width: item.qaCard.width, height: item.qaCard.height });
        }
        function close(): void { Qt.quit(); }
    }
'''


@unittest.skipUnless(os.environ.get('BWM_RUN_QML_TESTS') == '1', 'requires an explicit live-session test run')
class RetroUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (shutil.which('qs') and os.environ.get('WAYLAND_DISPLAY')):
            raise unittest.SkipTest('Quickshell and a Wayland session are required')
        token = uuid.uuid4().hex[:10]
        cls.paths = [SHELL / f'zz_retro_{token}_{suffix}.qml' for suffix in ('settings', 'grid', 'menu')]
        settings, grid, menu = cls.paths
        for source, target, input_id in [
            ('AppGrid', grid, 'searchInput'), ('Menu', menu, 'filterInput')
        ]:
            text = (SHELL / f'modules/ii/omarchyMenu/omarchy/{source}.qml').read_text()
            text = text.replace('"MenuModel.js"', '"modules/ii/omarchyMenu/omarchy/MenuModel.js"').replace('import "settings" as Settings', 'import "modules/ii/omarchyMenu/omarchy/settings" as Settings')
            text = text.replace('  id: root', f'  id: root\n  property alias qaInput: {input_id}\n  property alias qaPanel: panel\n  property alias qaCard: card\n  property alias qaEditor: settingEditor.item\n  property alias qaDetails: detailLoader.item', 1)
            if source == 'AppGrid': text = text.replace('  property alias qaEditor: settingEditor.item', '').replace('  property alias qaDetails: detailLoader.item', '')
            target.write_text(text)
        harness = HARNESS.replace('@GRID@', grid.name).replace('@MENU@', menu.name)
        settings.write_text(ROOT_QML.replace('@HARNESS@', harness))
        cls.display_files = {path:path.read_bytes() for path in (ROOT / 'config/hypr/modules/monitors.lua', ROOT / 'config/hypr/monitors_layout.json', ROOT / 'config/hypr/workspace_rules.json')}
        cls.command = ['qs', '-p', str(settings), 'ipc', 'call', 'retroRegression']
        cls.rule = 'tmp-retro-ui-tests'
        subprocess.run(['hyprctl', 'eval', 'hl.window_rule({name="tmp-retro-ui-tests", match={title="^BWM Retro UI Tests$"}, workspace="9 silent", no_initial_focus=true, float=true})'], check=True, capture_output=True)
        cls.log = tempfile.TemporaryFile(mode='w+')
        cls.proc = subprocess.Popen(['qs', '-p', str(settings)], env={**os.environ, 'SETTINGS_PAGE': 'general', 'BWM_SETTINGS_FROM_MENU': ''}, stdout=cls.log, stderr=subprocess.STDOUT)
        try:
            cls.wait_for(lambda s: s['ready'])
        except Exception:
            cls.tearDownClass()
            raise

    @classmethod
    def call(cls, *args):
        try:
            result = subprocess.check_output(cls.command + list(map(str, args)), text=True, stderr=subprocess.STDOUT).strip()
            if 'Function definition:' in result or result.startswith(('Too many arguments', 'Not enough arguments')):
                raise RuntimeError(result)
            return result
        except subprocess.CalledProcessError as error:
            raise RuntimeError(error.output) from error

    @classmethod
    def state(cls):
        return json.loads(cls.call('state'))

    @classmethod
    def wait_for(cls, condition):
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            try:
                state = cls.state()
                if condition(state):
                    return state
            except (subprocess.CalledProcessError, json.JSONDecodeError, RuntimeError):
                pass
            time.sleep(.05)
        cls.log.seek(0)
        raise AssertionError('UI did not become ready: ' + str(cls.state()) + '\n' + cls.log.read()[-3000:])

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, 'proc', None):
            cls.proc.terminate()
            try:
                cls.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                cls.proc.kill()
                cls.proc.wait()
        for path in getattr(cls, 'paths', []):
            path.unlink(missing_ok=True)
        subprocess.run(['hyprctl', 'reload'], capture_output=True)
        if getattr(cls, 'log', None):
            cls.log.close()

    def key(self, name, modifiers=0):
        self.call('key', 'Key_' + name, modifiers)

    def edit(self, text):
        self.key('A', 0x04000000)
        self.call('type', text)

    def setUp(self):
        self.call('openMode', 'settings')
        self.wait_for(lambda s: s['ready'])

    def test_settings_edit_middle_and_backspace(self):
        self.call('editor')
        self.edit('abcdef')
        self.key('Home')
        self.key('Right')
        self.key('Right')
        self.key('Delete')
        self.assertEqual(self.state()['text'], 'abdef')
        self.key('End')
        self.key('Backspace')
        self.assertEqual(self.state()['text'], 'abde')
        self.assertTrue(self.state()['inPage'])

    def test_number_commits_after_editing(self):
        self.call('number')
        self.key('A', 0x04000000)
        self.key('Backspace')
        self.assertEqual(self.state()['number'], 42)
        self.call('type', '137')
        self.assertEqual(self.state()['number'], 42)
        self.key('Tab')
        self.assertEqual(self.state()['number'], 137)

    def test_palette_tracks_light_and_dark(self):
        for light, color in [('true', '#151515'), ('false', '#eeeeee')]:
            self.call('palette', light)
            self.wait_for(lambda s: s['palette'] == color and s['fg'] == color)

    def test_grid_uses_native_editing_and_delete(self):
        self.call('openMode', 'grid')
        self.wait_for(lambda s: s['opened'] and s['count'] > 0)
        self.edit('abcdef')
        self.key('Home')
        self.key('Right')
        self.key('Delete')
        self.assertEqual(self.state()['text'], 'acdef')
        self.key('A', 0x04000000)
        self.assertEqual(self.state()['selected'], 'acdef')
        self.call('type', 'fire')
        self.assertEqual(self.state()['text'], 'fire')
        self.key('Escape')
        self.assertEqual(self.state()['text'], '')
        self.assertTrue(self.state()['opened'])
        self.key('Escape')
        self.assertFalse(self.state()['opened'])

    def test_grid_context_menu_keyboard(self):
        self.call('openMode', 'grid')
        self.wait_for(lambda s: s['opened'] and s['count'] > 0)
        self.key('Menu')
        self.assertTrue(self.state()['menu'])
        self.key('Down')
        self.assertEqual(self.state()['menuIndex'], 1)
        self.key('Escape')
        self.assertFalse(self.state()['menu'])
        self.assertTrue(self.state()['opened'])

    def test_grid_navigation_and_launch(self):
        self.call('openMode', 'grid')
        self.wait_for(lambda s: s['opened'] and s['count'] > 2)
        self.key('Tab')
        self.assertEqual(self.state()['index'], 1)
        self.key('Return')
        self.assertFalse(self.state()['opened'])
        self.assertTrue(self.state()['launched'])  # captured by the stub; no application runs

    def test_menu_uses_native_editing(self):
        self.call('openMode', 'menu')
        self.wait_for(lambda s: s['opened'])
        self.edit('abcdef')
        self.key('Home')
        self.key('Right')
        self.key('Delete')
        self.assertEqual(self.state()['text'], 'acdef')
        self.key('Right')
        self.assertEqual(self.state()['cursor'], 2)
        self.key('Backspace')
        self.assertEqual(self.state()['text'], 'adef')
        self.key('A', 0x04000000)
        self.assertEqual(self.state()['selected'], 'adef')

    def native(self, route, selected):
        self.call('openMode', 'menu')
        self.wait_for(lambda s: s['opened'])
        self.call('nativeRoute', route, selected)

    def native_state(self):
        return json.loads(self.call('nativeState'))

    def display_state(self):
        return json.loads(self.call('displayState'))

    def display(self):
        route = 'setup.settings.desktop.display'
        self.native(route.rsplit('.', 1)[0], route)
        self.key('Return')
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if self.native_state()['pageLoaded'] and self.display_state().get('monitors') and not self.display_state()['busy']:
                break
            time.sleep(.05)
        self.assertTrue(self.native_state()['pageLoaded'])
        data = [dict(description='TEST Monitor A', model='Monitor A', width=1920, height=1080,
                     x=0, y=0, scale=1, transform=0, refreshRate=144, focused=True, disabled=False,
                     resolutions=['1280x720', '1600x900', '1920x1080', '2560x1440'],
                     modesMap={'1280x720':[60], '1600x900':[60,120], '1920x1080':[60,144], '2560x1440':[60]}),
                dict(description='TEST Monitor B', model='Monitor B', width=1920, height=1080,
                     x=1920, y=0, scale=1, transform=0, refreshRate=60, focused=False, disabled=False,
                     resolutions=['1920x1080'], modesMap={'1920x1080':[60]})]
        self.fake_dir = tempfile.TemporaryDirectory(prefix='bwm-display-test-')
        self.addCleanup(self.fake_dir.cleanup)
        self.capture = Path(self.fake_dir.name) / 'applied.json'
        backend = Path(self.fake_dir.name) / 'monitor.py'
        backend.write_text('import json,sys\nfrom pathlib import Path\n'
                           + f'Path({str(self.capture)!r}).write_text(sys.argv[2])\n'
                           + 'print(json.dumps({"status":"success"}))\n')
        payload = base64.b64encode(json.dumps({'data':data, 'script':str(backend)}).encode()).decode()
        self.assertEqual(self.call('displayFixture', payload), '')
        fixture = self.display_state()
        self.assertEqual(fixture['script'], str(backend))
        self.assertEqual(fixture['monitors'], data)
        return data

    def test_display_arrows_select_rows_and_change_values(self):
        self.display()
        self.assertFalse(self.display_state()['hints'])
        self.key('Down'); self.key('Right')
        self.assertEqual(self.display_state()['selected'], 1)
        self.key('Left'); self.key('Down'); self.key('Left')
        state = self.display_state()
        self.assertEqual(state['row'], 2)
        self.assertEqual(state['monitors'][0]['width'], 1600)
        self.assertEqual(state['monitors'][0]['refreshRate'], 120)
        self.assertFalse(state['editing'])
        self.assertFalse(self.capture.exists())

    def test_display_preview_accounts_for_scale_and_rotation(self):
        self.display()
        for _ in range(4): self.key('Down')
        self.key('Right')
        self.assertEqual(self.display_state()['logicalSizes'][0], {'width':1536, 'height':864})
        self.key('Down'); self.key('Right')
        self.assertEqual(self.display_state()['logicalSizes'][0], {'width':864, 'height':1536})
        self.assertFalse(self.capture.exists())

    def test_display_layout_keys_and_nested_escape(self):
        data = self.display()
        self.key('Space')
        self.assertTrue(self.display_state()['editing'])
        self.assertTrue(self.display_state()['hints'])
        self.key('Down')
        self.assertEqual(self.display_state()['monitors'][0]['y'], 40)
        self.key('Down', 0x02000000)  # Shift: fine movement
        self.assertEqual(self.display_state()['monitors'][0]['y'], 50)
        self.key('Left', 0x04000000)  # Ctrl: previous supported resolution
        self.assertEqual(self.display_state()['monitors'][0]['width'], 1600)
        self.key('Tab')
        self.assertEqual(self.display_state()['selected'], 1)
        self.key('Escape')
        self.assertFalse(self.display_state()['hints'])
        self.assertFalse(self.display_state()['editing'])
        self.assertEqual(self.native_state()['page'], 'display')
        before = self.display_state()['monitors']
        self.key('Down')
        self.assertEqual(self.display_state()['monitors'], before)
        self.assertEqual(self.display_state()['row'], 1)
        self.assertFalse(self.capture.exists())
        self.key('Backspace')
        self.assertEqual(self.native_state()['page'], '')

    def test_display_backspace_finishes_and_enter_reopens_editing(self):
        self.display()
        self.key('Return'); self.key('Backspace')
        self.assertFalse(self.display_state()['editing'])
        self.assertEqual(self.native_state()['page'], 'display')
        self.key('Return')
        self.assertTrue(self.display_state()['hints'])
        self.key('Space')
        self.assertFalse(self.display_state()['hints'])

    def test_display_apply_uses_draft_and_description_with_fake_backend(self):
        self.display()
        self.key('Down'); self.key('Down'); self.key('Left')
        self.assertFalse(self.capture.exists())
        self.key('End'); self.key('Up')
        self.assertEqual(self.display_state()['row'], 11)
        self.key('Return')
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and self.display_state()['dirty']:
            time.sleep(.05)
        state = self.display_state()
        self.assertFalse(state['dirty'], state)
        applied = json.loads(self.capture.read_text())
        self.assertEqual(applied[0]['width'], 1600)
        self.assertEqual(applied[0]['description'], 'TEST Monitor A')
        self.assertEqual(applied[0]['x'], 0)
        self.assertEqual(applied[1]['x'], 1600)

    def test_display_overlapping_layout_is_rejected(self):
        self.display()
        self.key('Return'); self.key('Right'); self.key('Return')
        self.key('End'); self.key('Up')
        self.key('Return')
        state = self.display_state()
        self.assertTrue(state['error'])
        self.assertIn('superponen', state['message'])
        self.assertFalse(self.capture.exists())

    def test_native_complex_pages_use_the_existing_layer(self):
        before = sum(c['pid'] == self.proc.pid for c in json.loads(subprocess.check_output(['hyprctl', 'clients', '-j'])))
        for route, name in [
            ('setup.settings.look.bar.controls', 'bar'), ('setup.settings.look.background.controls', 'background'),
            ('setup.settings.look.interface.controls', 'interface'), ('setup.settings.look.style.controls', 'style'),
            ('setup.settings.desktop.workspaces.controls', 'workspaces'),
            ('setup.settings.system.general.controls', 'general'), ('setup.settings.system.services.controls', 'services'),
            ('setup.settings.look.themes', 'themes'), ('setup.settings.look.cursor', 'cursor'),
            ('setup.settings.desktop.display', 'display'), ('setup.settings.desktop.keybinds', 'keybinds'),
            ('setup.settings.system.autostart', 'autostart'), ('setup.settings.system.defaultapps', 'defaultapps'),
            ('setup.settings.system.plugins', 'plugins'), ('setup.settings.about', 'about')]:
            with self.subTest(page=name):
                self.native(route.rsplit('.', 1)[0], route)
                self.key('Return')
                deadline = time.monotonic() + 5
                while time.monotonic() < deadline and not self.native_state()['pageLoaded']:
                    time.sleep(.05)
                self.assertTrue(self.native_state()['pageLoaded'])
                self.assertEqual(self.native_state()['page'], name)
                after = sum(c['pid'] == self.proc.pid for c in json.loads(subprocess.check_output(['hyprctl', 'clients', '-j'])))
                self.assertEqual(after, before)
                self.key('Escape')
                self.assertEqual(self.native_state()['page'], '')

    def test_native_section_jump_moves_focus_to_new_controls(self):
        route = 'setup.settings.system.general'
        self.native(route, route + '.controls')
        self.key('Return')
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and not self.native_state()['pageLoaded']:
            time.sleep(.05)
        time.sleep(.1)
        self.call('nativeSection', 1)
        time.sleep(.1)
        self.assertEqual(self.native_state()['section'], 1)
        self.assertTrue(self.native_state()['controlFocused'])
        self.key('Escape')
        self.assertEqual(self.native_state()['page'], '')

    def test_apps_entry_calls_native_shell_launcher(self):
        self.native('root', 'apps')
        self.key('Return')
        self.assertEqual(self.state()['summoned'], 'bwm.apps')
        self.assertFalse(self.state()['opened'])

    def test_launcher_menus_have_no_navigation_footer(self):
        self.native('appearance', 'appearance.bar')
        texts = json.loads(self.call('visibleTexts', 'menu'))
        self.assertFalse(any('esc atrás' in t or '↑↓ ↵' in t for t in texts))
        self.call('openMode', 'grid')
        self.wait_for(lambda s: s['opened'] and s['count'] > 0)
        texts = json.loads(self.call('visibleTexts', 'grid'))
        self.assertFalse(any('←↑↓→' in t or 'Tab · ↵' in t for t in texts))

    def test_native_catalog_uses_real_options(self):
        self.assertEqual(json.loads(self.call('missingFields')), [])

    def test_native_toggle_stays_in_menu_without_touching_live_config(self):
        route = 'setup.settings.system.general'
        selected = route + '.time-secondPrecision'
        self.native(route, selected)
        before = self.native_state()
        self.key('Return')
        after = self.native_state()
        self.assertEqual(after['menu'], route)
        self.assertEqual(after['selected'], selected)
        self.assertEqual(after['option'], not before['option'])
        self.assertEqual(after['productionOption'], before['productionOption'])

    def test_native_choice_returns_to_selected_option(self):
        route = 'setup.settings.system.general'
        selected = route + '.time-format'
        self.native(route, selected)
        self.key('Return')
        self.assertEqual(self.native_state()['menu'], selected)
        self.key('Down')
        self.key('Return')
        self.assertEqual(self.native_state()['menu'], route)
        self.assertEqual(self.native_state()['selected'], selected)
        self.assertEqual(self.native_state()['format'], 'h:mm AP')

    def test_native_editor_commits_and_cancels_in_same_menu(self):
        route = 'setup.settings.system.general'
        selected = route + '.time-dateFormat'
        self.native(route, selected)
        self.key('Return')
        self.assertEqual(self.native_state()['editing'], selected)
        self.edit('abcdef')
        self.key('Home'); self.key('Right'); self.key('Delete')
        self.assertEqual(self.native_state()['draft'], 'acdef')
        self.key('Return')
        self.assertEqual(self.native_state()['date'], 'acdef')
        self.assertEqual(self.native_state()['selected'], selected)
        self.key('Return')
        self.edit('discard this')
        self.key('Escape')
        self.assertEqual(self.native_state()['date'], 'acdef')
        self.assertEqual(self.native_state()['editing'], '')

    def test_native_search_context_survives_choice_and_back(self):
        route = 'setup.settings'
        self.native(route, '')
        self.call('nativeSearch', 'Formato de la hora')
        selected = 'setup.settings.system.general.time-format'
        self.assertEqual(self.native_state()['selected'], selected)
        self.key('Return')
        self.key('Down'); self.key('Return')
        self.assertEqual(self.native_state()['menu'], route)
        self.assertEqual(self.native_state()['selected'], selected)
        self.assertEqual(self.state()['text'], 'Formato de la hora')

    def test_native_request_waits_for_menu_sources(self):
        self.native('setup.settings', '')
        self.call('delayedRoute', 'setup.settings.system.general')
        self.assertEqual(self.native_state()['menu'], 'setup.settings.system.general')

    def test_native_link_returns_to_original_entry(self):
        self.native('appearance', 'appearance.bar')
        self.key('Return')
        self.assertEqual(self.native_state()['menu'], 'setup.settings.look.bar')
        self.key('Escape')
        self.assertEqual(self.native_state()['menu'], 'appearance')
        self.assertEqual(self.native_state()['selected'], 'appearance.bar')

    def test_native_number_validates_before_commit(self):
        route = 'setup.settings.system.general.battery'
        selected = route + '.low'
        self.native(route, selected)
        self.key('Return')
        before = self.native_state()['battery']
        self.edit('999')
        self.key('Return')
        self.assertEqual(self.native_state()['editing'], selected)
        self.assertEqual(self.native_state()['battery'], before)
        self.edit('35')
        self.key('Up')
        self.assertEqual(self.native_state()['draft'], '40')
        self.assertEqual(self.native_state()['battery'], before)
        self.key('Return')
        self.assertEqual(self.native_state()['battery'], 40)
        self.assertEqual(self.native_state()['editing'], '')

    def test_z_no_runtime_errors(self):
        for path, content in self.display_files.items():
            self.assertEqual(path.read_bytes(), content, f"Test modified real display configuration: {path}")
        self.log.seek(0)
        self.assertNotRegex(self.log.read(), r'(ReferenceError|TypeError|Binding loop|Unable to assign|Failed to load configuration)')


if __name__ == '__main__':
    unittest.main()
