"""Retro's native Nautilus appearance and non-destructive XDG templates."""
import importlib.util
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'config/hypr/scripts'
sys.path.insert(0, str(SCRIPTS))
import bwm_icons as icons
import bwm_omarchy as omarchy


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


setup = load('nautilus_setup', ROOT / 'config/hypr/skins/retro/scripts/setup-nautilus.py')
persistent = load('nautilus_persistent', SCRIPTS / 'toggle-float-persistent.py')


class AppearanceTests(unittest.TestCase):
    def test_templates_enable_disabled_xdg_directory_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            with mock.patch.object(setup.subprocess, 'run', return_value=mock.Mock(stdout=str(home) + '\n')) as run:
                setup.setup_templates(home, home / 'state')
                run.assert_any_call(['xdg-user-dirs-update', '--set', 'TEMPLATES', str(home / 'Templates')], check=True, timeout=5)
                for source in setup.SOURCE.iterdir():
                    self.assertEqual((home / 'Templates' / source.name).read_bytes(), source.read_bytes())
                # A later user deletion stays deleted, including on skin changes.
                target = home / 'Templates/Archivo de texto.txt'
                target.unlink()
                run.reset_mock()
                setup.setup_templates(home, home / 'state')
                run.assert_not_called()
                self.assertFalse(target.exists())

    def test_existing_template_directory_and_user_files_are_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            folder = home / 'Mis plantillas'
            folder.mkdir()
            custom = folder / 'Archivo de texto.txt'
            custom.write_text('Mi plantilla')
            with mock.patch.object(setup.subprocess, 'run', return_value=mock.Mock(stdout=str(folder) + '\n')) as run:
                setup.setup_templates(home, home / 'state')
                self.assertEqual(run.call_count, 1)
            self.assertEqual(custom.read_text(), 'Mi plantilla')
            self.assertTrue((folder / 'Documento Markdown.md').exists())

    def test_retro_icons_use_adwaita_and_honor_installed_original_theme(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            theme = home / '.local/state/bwm/omarchy/theme'
            theme.mkdir(parents=True)
            data = home / 'data'
            with mock.patch.object(icons, 'HOME', home), mock.patch.dict(os.environ, {'XDG_DATA_HOME': str(data), 'XDG_DATA_DIRS': str(home / 'system')}):
                self.assertEqual(icons.icon_theme_for('retro'), 'Adwaita')
                (theme / 'icons.theme').write_text('Yaru-magenta\n')
                self.assertEqual(icons.icon_theme_for('retro'), 'Adwaita')
                index = data / 'icons/Yaru-magenta/index.theme'
                index.parent.mkdir(parents=True)
                index.write_text('[Icon Theme]\nName=Yaru-magenta\n')
                self.assertEqual(icons.icon_theme_for('retro'), 'Yaru-magenta')
                (theme / 'icons.theme').write_text('../../private')
                self.assertEqual(icons.icon_theme_for('retro'), 'Adwaita')

    def test_gtk4_keeps_native_widgets_and_accepts_theme_css_without_hooks(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / 'config'
            state = Path(tmp) / 'state'
            base = config / 'hypr/skins/retro/gtk/gtk4.css'
            base.parent.mkdir(parents=True)
            base.write_text('/* native libadwaita */\n')
            theme = state / 'theme/gtk.css'
            theme.parent.mkdir(parents=True)
            theme.write_text('window { color: red; }\n')
            source = config / 'material.css'
            source.write_text('button { border-radius: 20px; }')
            destination = config / 'gtk-4.0/gtk.css'
            matugen = config / 'matugen/config.toml'
            matugen.parent.mkdir()
            matugen.write_text('[templates.gtk4]\ninput_path = ' + json.dumps(str(source)) + '\noutput_path = ' + json.dumps(str(destination)) + '\n')
            with mock.patch.object(omarchy, 'CONFIG_DIR', config), mock.patch.object(omarchy, 'STATE_DIR', state), \
                    mock.patch.object(omarchy, 'm3_roles', return_value={}), mock.patch.object(omarchy, 'render_matugen') as render, \
                    mock.patch.object(omarchy, '_detached') as hook:
                self.assertEqual(omarchy.apply_matugen_apps({}, ''), {'gtk4'})
                render.assert_not_called()
                hook.assert_not_called()
            self.assertEqual(destination.read_text(), base.read_text() + '\n' + theme.read_text())

    def test_persistent_float_can_be_excluded_only_in_retro(self):
        lua = shutil.which('lua') or shutil.which('luajit')
        if not lua:
            self.skipTest('requires Lua interpreter')
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'rules.lua'
            rules = {'nautilus': {'match': {'class': '^org.gnome.Nautilus$'}, 'float': True, 'excludeSkins': ['retro']}}
            with mock.patch.object(persistent, 'LUA_PATH', str(path)):
                persistent.generate_lua(rules)
            for skin, count in [('retro', 0), ('default', 1), ('plasma', 1), ('future', 1)]:
                code = 'package.preload["modules.theme"]=function() return {name=' + json.dumps(skin) + '} end; local count=0; hl={window_rule=function(r) count=count+1; assert(r.float==true) end}; dofile(' + json.dumps(str(path)) + '); print(count)'
                result = subprocess.run([lua, '-e', code], capture_output=True, text=True, check=True)
                self.assertEqual(result.stdout.strip(), str(count))

    def test_workspace_float_requests_are_idempotent(self):
        lua = shutil.which('lua') or shutil.which('luajit')
        if not lua:
            self.skipTest('requires Lua interpreter')
        source = (ROOT / 'config/hypr/skins/retro/hypr/workspace-modes.lua').read_text()
        function = re.search(r'local function set_floating\(window, floating\).*?\nend', source, re.S).group()
        # Hyprland 0.56 treats unknown actions (including on/off) as toggle.
        fixture = '''
local window = {floating=false}
hl = {dispatch=function(command) command() end, dsp={window={float=function(args)
return function()
 if args.action == "enable" then args.window.floating=true
 elseif args.action == "disable" then args.window.floating=false
 else args.window.floating=not args.window.floating end
end end}}}
FUNCTION
set_floating(window,true); set_floating(window,true); assert(window.floating)
set_floating(window,false); set_floating(window,false); assert(not window.floating)
'''.replace('FUNCTION', function)
        subprocess.run([lua, '-e', fixture], check=True, capture_output=True, text=True)


if __name__ == '__main__':
    unittest.main()
