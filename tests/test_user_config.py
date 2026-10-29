"""Configuración en texto del usuario (bwm-user-config): plantillas válidas y quién manda."""
import importlib.machinery
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'config/hypr/scripts/bwm-user-config'
loader = importlib.machinery.SourceFileLoader('bwm_user_config', str(SCRIPT))
spec = importlib.util.spec_from_loader('bwm_user_config', loader)
user = importlib.util.module_from_spec(spec)
loader.exec_module(user)


class UserConfigTests(unittest.TestCase):
    def test_skin_options_win_over_all_and_keep_the_rest(self):
        data = {'bar': {'height': 24, 'bottom': False}, 'time': {'format': 'hh:mm'}}
        overrides = {'all': {'bar': {'height': 30}, 'time': {'format': 'HH:mm'}},
                     'skins': {'retro': {'bar': {'height': 26}}, 'plasma': {'bar': {'height': 50}}}}
        user.apply_shell(data, 'retro', overrides)
        self.assertEqual(data, {'bar': {'height': 26, 'bottom': False}, 'time': {'format': 'HH:mm'}})

    def test_jsonc_comments_and_trailing_commas(self):
        text = '{\n // comentario\n "url": "http://a//b", "l": [1, 2,],\n}'
        self.assertEqual(json.loads(user.strip_jsonc(text)), {'url': 'http://a//b', 'l': [1, 2]})

    def test_templates_are_created_once_and_say_who_writes(self):
        original = dict(user.TEMPLATES)
        self.addCleanup(lambda: (user.TEMPLATES.clear(), user.TEMPLATES.update(original)))
        with tempfile.TemporaryDirectory() as tmp:
            for name, spec in original.items():
                spec = dict(spec, path=Path(tmp) / name / spec['path'].name)
                user.TEMPLATES[name] = spec
                path = user.ensure(name)
                text = path.read_text(encoding='utf-8')
                self.assertIn('EN ESTA ZONA PUEDES ESCRIBIR TÚ', text)
                path.write_text(text + '\nmío\n', encoding='utf-8')
                user.ensure(name)  # no pisa lo del usuario
                self.assertTrue(path.read_text(encoding='utf-8').endswith('mío\n'))
            shell = user.load_shell_overrides(user.TEMPLATES['shell']['path'].with_name('limpio.jsonc'))
            self.assertEqual(shell, {})

    def test_shell_template_parses_to_empty_overrides(self):
        spec = user.TEMPLATES['shell']
        text = user.HEADER.format(c=spec['comment'], what=spec['what'], name='shell') + spec['body']
        data = json.loads(user.strip_jsonc(text))
        self.assertEqual(data['all'], {})
        self.assertEqual(set(data['skins']), {'default', 'retro', 'plasma'})


if __name__ == '__main__':
    unittest.main()
