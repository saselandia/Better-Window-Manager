"""Compatibility, lookup and installation checks without touching the user's config."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location('bwm_addons', SCRIPTS / 'bwm-addons.py')
addons = importlib.util.module_from_spec(spec)
spec.loader.exec_module(addons)
import bwm_omarchy as bwm


class AddonTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='bwm-addons-test-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def plugin(self, **overrides):
        folder = self.root / 'plugin'
        folder.mkdir(exist_ok=True)
        manifest = {'schemaVersion': 1, 'id': 'example.widget', 'name': 'Example',
                    'kinds': ['bar-widget', 'service'],
                    'entryPoints': {'barWidget': 'Widget.qml', 'service': 'Service.qml'}}
        manifest.update(overrides)
        (folder / 'manifest.json').write_text(json.dumps(manifest))
        (folder / 'Widget.qml').write_text('import QtQuick\nItem {}\n')
        (folder / 'Service.qml').write_text('import QtQuick\nQtObject {}\n')
        return folder

    def theme(self, root, name, background='#112233'):
        folder = root / name
        folder.mkdir(parents=True)
        (folder / 'colors.toml').write_text(
            f'background = "{background}"\nforeground = "#eeeeee"\naccent = "#abcdef"\n')
        return folder

    def test_accepts_widget_with_service(self):
        self.assertEqual(addons.validate_plugin(self.plugin())['id'], 'example.widget')

    def test_rejects_replacement_shell_and_reserved_id(self):
        for overrides in ({'kinds': ['bar']}, {'id': 'omarchy.clock'}, {'schemaVersion': 2}):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                addons.validate_plugin(self.plugin(**overrides))

    def test_rejects_missing_entrypoint_traversal_and_symlinks(self):
        folder = self.plugin(entryPoints={'barWidget': '../Widget.qml', 'service': 'Service.qml'})
        with self.assertRaises(ValueError):
            addons.validate_plugin(folder)
        folder = self.plugin()
        (folder / 'Widget.qml').unlink()
        with self.assertRaises(ValueError):
            addons.validate_plugin(folder)
        (folder / 'Widget.qml').symlink_to('/etc/passwd')
        with self.assertRaises(ValueError):
            addons.validate_plugin(folder)

    def test_rejects_unavailable_qml_modules(self):
        folder = self.plugin()
        (folder / 'Widget.qml').write_text('import qs.MissingBWMModule\nItem {}\n')
        with self.assertRaisesRegex(ValueError, 'MissingBWMModule'):
            addons.validate_plugin(folder)

    def test_urls_are_repositories_not_commands_or_github_files(self):
        self.assertEqual(addons.repository_url('https://github.com/author/repo.git'), 'https://github.com/author/repo')
        for url in ('file:///etc', 'https://github.com/a/b/tree/main', 'https://github.com/a/b;id',
                    'https://user:secret@github.com/a/b', 'https://github.com/a/b?arg=x'):
            with self.subTest(url=url), self.assertRaises(ValueError):
                addons.repository_url(url)

    def test_theme_requires_modern_palette(self):
        folder = self.theme(self.root, 'good')
        self.assertEqual(addons.validate_theme(folder)['accent'], '#abcdef')
        (folder / 'colors.toml').write_text('background = "red"\n')
        with self.assertRaises(ValueError):
            addons.validate_theme(folder)

    def test_community_theme_is_listed_and_resolved_for_renderer(self):
        bundled, user = self.root / 'bundled', self.root / 'user'
        self.theme(bundled, 'shared')
        override = self.theme(user, 'shared', '#445566')
        with patch.object(bwm, 'THEMES_DIR', bundled), patch.object(bwm, 'USER_THEMES_DIR', user), \
                patch.object(bwm, 'LEGACY_THEMES_DIR', self.root / 'legacy'):
            themes = bwm.list_omarchy_themes()
            self.assertEqual(len(themes), 1)
            self.assertFalse(themes[0]['builtin'])
            self.assertEqual(bwm.theme_directory('shared'), override)
            with self.assertRaises(ValueError):
                bwm.theme_directory('../shared')

    def test_legacy_symlink_does_not_reclassify_bundled_themes(self):
        bundled, user, legacy = self.root / 'bundled', self.root / 'user', self.root / 'legacy'
        self.theme(bundled, 'bundled')
        legacy.symlink_to(bundled, target_is_directory=True)
        with patch.object(bwm, 'THEMES_DIR', bundled), patch.object(bwm, 'USER_THEMES_DIR', user), \
                patch.object(bwm, 'LEGACY_THEMES_DIR', legacy):
            themes = bwm.list_omarchy_themes()
            self.assertEqual(len(themes), 1)
            self.assertTrue(themes[0]['builtin'])

    def test_theme_install_is_validated_before_exposing_and_does_not_apply(self):
        source = self.theme(self.root, 'source')
        user = self.root / 'installed'
        user.mkdir()
        from contextlib import contextmanager
        @contextmanager
        def clone(url, parent):
            yield source
        with patch.object(addons, 'USER_THEMES', user), patch.object(addons, 'cloned', clone), \
                patch.object(bwm, 'list_omarchy_themes', return_value=[]), patch.object(bwm, 'set_theme') as apply:
            result = addons.install_theme('https://github.com/example/omarchy-example-theme')
            self.assertEqual(result['id'], 'example')
            self.assertTrue((user / 'example/colors.toml').is_file())
            apply.assert_not_called()

    def test_invalid_theme_install_does_not_leave_installed_folder(self):
        source = self.root / 'invalid'
        source.mkdir()
        from contextlib import contextmanager
        @contextmanager
        def clone(url, parent):
            yield source
        with patch.object(addons, 'USER_THEMES', self.root / 'installed'), \
                patch.object(addons, 'cloned', clone), patch.object(bwm, 'list_omarchy_themes', return_value=[]):
            with self.assertRaises(OSError):
                addons.install_theme('https://github.com/example/invalid-theme')
            self.assertFalse((self.root / 'installed/invalid').exists())

    def test_search_parses_theme_links_and_filters_all_words(self):
        parser = addons.ThemeLinks()
        parser.feed('<a href="https://github.com/ignore/repo">Outside</a><ul><li>'
                    '<a href="https://github.com/author/theme">Dark <b>Blue</b></a></li></ul>')
        self.assertEqual(parser.themes[0]['name'], 'Dark Blue')
        self.assertEqual(len(parser.themes), 1)
        with patch.object(addons, 'remote_catalog', return_value=(parser.themes, '')):
            self.assertEqual(addons.discover('themes', 'blue dark')['total'], 1)
            self.assertEqual(addons.discover('themes', 'missing')['total'], 0)

    def test_discovery_paginates_without_dropping_or_repeating_results(self):
        entries = [{'id': str(i), 'name': f'Theme {i}'} for i in range(65)]
        with patch.object(addons, 'remote_catalog', return_value=(entries, '')):
            first = addons.discover('themes', 'theme')
            second = addons.discover('themes', 'theme', offset=first['nextOffset'])
            third = addons.discover('themes', 'theme', offset=second['nextOffset'])
        all_items = first['results'] + second['results'] + third['results']
        self.assertEqual([len(part['results']) for part in (first, second, third)], [30, 30, 5])
        self.assertEqual([item['id'] for item in all_items], [str(i) for i in range(65)])
        self.assertEqual(third['nextOffset'], 65)

    def test_failed_refresh_uses_cached_catalog(self):
        cache = self.root / 'cache'
        cache.mkdir()
        (cache / 'themes.json').write_text('[{"name":"Cached theme"}]')
        with patch.object(addons, 'CACHE', cache), patch.object(addons, 'download', side_effect=OSError('offline')):
            results, message = addons.remote_catalog('themes', refresh=True)
            self.assertEqual(results[0]['name'], 'Cached theme')
            self.assertIn('último catálogo', message)

    def test_moving_plugin_preserves_user_settings_and_disabled_plugins(self):
        builtin = self.root / 'builtins'
        builtin.mkdir()
        self.plugin().rename(builtin / 'example')
        layout = self.root / 'layout.json'
        layout.write_text(json.dumps({'bar': [{'id': 'example.widget', 'section': 'center',
                                               'settings': {'maxLabelWidth': 123}}],
                                      'disabled': ['someone.else']}))
        bin_dir = self.root / 'bin'
        bin_dir.mkdir()
        qs = bin_dir / 'qs'
        qs.write_text('#!/bin/sh\nexit 0\n')
        qs.chmod(0o755)
        env = {**os.environ, 'BWM_BUILTIN_PLUGINS': str(builtin), 'BWM_OMARCHY_LAYOUT': str(layout),
               'XDG_DATA_HOME': str(self.root / 'data'), 'PATH': f'{bin_dir}:' + os.environ['PATH']}
        subprocess.run([str(SCRIPTS / 'bwm-plugin.sh'), 'enable', 'example.widget', '--section', 'centerEnd'],
                       env=env, check=True, capture_output=True)
        result = json.loads(layout.read_text())
        self.assertEqual(result['bar'][0]['settings']['maxLabelWidth'], 123)
        self.assertEqual(result['bar'][0]['section'], 'centerEnd')
        self.assertEqual(result['disabled'], ['someone.else'])


if __name__ == '__main__':
    unittest.main()
