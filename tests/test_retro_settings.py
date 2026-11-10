"""Native Retro rows and routing, with every mutation replaced by a recorder."""
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('retro_settings', ROOT / 'config/hypr/skins/retro/scripts/settings.py')
settings = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(settings)


def bind(**kwargs):
    return dict(id='test', description='Terminal', key='RETURN', mods=['CTRL'], action_type='exec',
                exec='/usr/bin/kitty', enabled=True, is_default=True, **kwargs)


class RetroSettingsTests(unittest.TestCase):
    def field(self, data, key, **matches):
        return next(f for f in data['fields'] if f['key'] == key and all(f.get(k) == v for k, v in matches.items()))

    def test_dispatcher_bind_keeps_its_action_and_filters_other_skins(self):
        b = bind(); b.update(action_type='dispatcher', dispatcher='window.close', dispatcher_arg='')
        hidden = bind(); hidden.update(id='breeze', skins=['plasma'])
        data = settings.keybind_rows([b, hidden])
        names = [e['label'] for e in data['entries']]
        self.assertEqual(names.count('Terminal'), 1)
        self.assertEqual(self.field(data, 'dispatcher', item='test')['value'], 'window.close')
        self.assertFalse(any(f.get('item') == 'test' and f['key'] == 'exec' for f in data['fields']))

    def test_cursor_current_choice_is_preserved_and_uses_the_existing_manager(self):
        data = settings.cursor_rows({'theme':'Custom', 'size':28}, [{'name':'Bibata', 'id':'Bibata'}])
        theme = self.field(data, 'theme')
        self.assertEqual(theme['choices'][0], {'label':'Custom', 'value':'Custom'})
        with patch.object(settings, 'run', return_value='{"theme":"Custom","size":28}') as run:
            settings.save(self.field(data, 'size'), 32, {})
        self.assertEqual(run.call_args.args, ('cursor-manager.py', 'apply', 'Custom', 32))

    def test_applications_use_the_common_defaults_manager(self):
        with patch.object(settings, 'run') as run:
            settings.save({'category':'defaultapps', 'key':'browser'}, 'firefox.desktop', {})
        run.assert_called_once_with('default-apps.py', 'set', 'browser', 'firefox.desktop')

    def test_autostart_offers_installed_apps_once_and_does_not_run_them(self):
        data = settings.autostart_rows(
            [{'file':'a.desktop', 'name':'A', 'enabled':True, 'workspace':'3'}],
            [{'id':'a.desktop', 'name':'A'}, {'id':'b.desktop', 'name':'B'}])
        field = self.field(data, 'add')
        self.assertEqual(field['choices'], [{'label':'B', 'value':'b.desktop'}])
        with patch.object(settings, 'run') as run:
            settings.save(field, 'b.desktop', {})
        run.assert_called_once_with('autostart-manager.py', 'add-app', 'b.desktop')

    def test_keybind_edit_routes_to_json_manager_without_shell_evaluation(self):
        field = self.field(settings.keybind_rows([bind()]), 'combo', item='test')
        with patch.object(settings, 'run') as run:
            settings.save(field, 'Super + Ctrl + K', {})
        run.assert_called_once_with('keybinds-manager.py', 'update', '--id', 'test', '--mods', 'SUPER,CTRL', '--key', 'K')
        with patch.object(settings, 'run') as run:
            with self.assertRaises(ValueError):
                settings.save(field, 'Super +', {})
            run.assert_not_called()

    def test_creating_a_bind_is_a_single_commit_and_can_be_a_dispatcher(self):
        field = self.field(settings.keybind_rows([]), 'save')
        with patch.object(settings, 'run') as run:
            with self.assertRaises(ValueError):
                settings.save(field, None, {'description':'Incomplete'})
            run.assert_not_called()
            settings.save(field, None, {'description':'Close', 'combo':'Super + X', 'action_type':'dispatcher', 'dispatcher':'window.close'})
        run.assert_called_once_with('keybinds-manager.py', 'add', '--desc', 'Close', '--mods', 'SUPER', '--key', 'X', '--type', 'dispatcher', '--dispatcher', 'window.close', '--dispatcher-arg', '')

    def test_custom_binds_can_be_removed_and_defaults_can_be_reset(self):
        a, b = bind(), bind(); a.update(is_default=False); b.update(id='default', is_modified=True)
        data = settings.keybind_rows([a, b])
        with patch.object(settings, 'run') as run:
            settings.save(self.field(data, 'confirm', item='test'), None, {})
            self.assertEqual(run.call_args.args, ('keybinds-manager.py', 'purge', '--id', 'test'))
            settings.save(self.field(data, 'reset', item='default'), None, {})
            self.assertEqual(run.call_args.args, ('keybinds-manager.py', 'reset', '--id', 'default'))

    def test_plugin_positions_keep_all_six_native_sections(self):
        plugin = dict(id='clock', name='Clock', enabled=True, canDisable=True, kinds=['bar-widget'])
        for section in ('left', 'centerBegin', 'center', 'centerEnd', 'tray', 'right'):
            data = settings.plugin_rows([plugin], {section:[{'id':'clock', 'format':'HH:mm'}]})
            field = self.field(data, 'section')
            self.assertEqual(field['value'], section)
            with patch.object(settings, 'command') as command:
                settings.save(field, section, {})
            self.assertEqual(command.call_args.args[0][-3:], ['clock', '--section', section])
        plugin['enabled'] = False
        self.assertFalse(any(f['key'] == 'section' for f in settings.plugin_rows([plugin], {})['fields']))

    def test_catalog_has_no_install_action_for_existing_repositories(self):
        url = 'https://github.com/user/omarchy-test'
        data = settings.addon_rows('themes', [{'url':url, 'name':'Test'}], {url})
        self.assertFalse(any(f.get('operation') == 'install' for f in data['fields']))
        self.assertTrue(any(f.get('operation') == 'open' for f in data['fields']))

    def test_native_field_ids_are_unique_even_for_similar_names(self):
        entries = [bind(), bind()]; entries[1]['id'] = 'test-2'
        data = settings.keybind_rows(entries)
        ids = [x['id'] for x in data['entries'] + data['fields']]
        self.assertEqual(len(ids), len(set(ids)))

    def test_catalog_search_reaches_beyond_the_first_page(self):
        catalog = [dict(name=f'Theme {i}', url=f'https://github.com/user/theme-{i}', author='Author') for i in range(75)]
        first = settings.addon_rows('themes', catalog, set())
        self.assertEqual(len(first['entries']), 61)
        self.assertTrue(any(f.get('operation') == 'more' for f in first['fields']))
        search = settings.addon_rows('themes', catalog, set(), query='Theme 74')
        self.assertEqual([e['label'] for e in search['entries']], ['Desde URL', 'Theme 74'])
        self.assertFalse(any(f.get('operation') == 'more' for f in search['fields']))

    def test_manager_json_failure_is_not_reported_as_a_success(self):
        with patch.object(settings, 'command', return_value='Saved?\n{"success":false}\n'):
            with self.assertRaisesRegex(ValueError, 'No se pudo guardar'):
                settings.run('keybinds-manager.py', 'update')


if __name__ == '__main__':
    unittest.main()
