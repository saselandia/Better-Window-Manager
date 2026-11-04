"""Live-bind formatting and Lua metadata resolution; no compositor mutations."""
import importlib.util
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'config/hypr/skins/retro/scripts/keybindings.py'
spec = importlib.util.spec_from_file_location('retro_keybindings', SOURCE)
backend = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backend)


class RetroKeybindingsTests(unittest.TestCase):
    def test_active_records_hide_helpers_preserve_custom_and_avoid_duplicate_super(self):
        rows = backend.records([
            {'key':'Alt_L', 'modmask':0, 'description':''},
            {'key':'SUPER_L', 'modmask':64, 'description':'Mi menú', 'dispatcher':'exec', 'arg':'custom-menu'},
            {'key':'F8', 'modmask':12, 'description':'Personal: Mi comando', 'dispatcher':'exec', 'arg':'echo "a,b"'},
        ], {})
        self.assertEqual(len(rows), 2)
        self.assertIn('SUPER ', rows[0]['label'])
        self.assertNotIn('SUPER + SUPER', rows[0]['label'])
        self.assertEqual(rows[1]['command'], ['hyprctl','dispatch','exec','echo "a,b"'])

    def test_generated_lua_actions_resolve_without_executing_config(self):
        actions = backend.lua_actions('''
hl.bind("CTRL + RETURN", hl.dsp.exec_cmd("kitty --title \\"a,b\\""), { description = "Lanzadores: Terminal" })
hl.bind("ALT + RETURN", hl.dsp.window.fullscreen({ mode = fullscreen_mode, action = "toggle" }), { description = "Ventanas: Fullscreen" })
''')
        rows = backend.records([{'key':'RETURN', 'modmask':8, 'description':'Ventanas: Fullscreen', 'dispatcher':'__lua', 'arg':'42'}], actions)
        self.assertEqual(rows[0]['command'], ['hyprctl','dispatch','hl.dsp.window.fullscreen({ mode = 0, action = "toggle" })'])
        self.assertIn('Lanzadores: Terminal', actions)

    def test_ambiguous_lua_descriptions_and_mouse_bindings_are_reference_only(self):
        source = '''hl.bind("ALT + A", hl.dsp.exec_cmd("first"), { description = "Duplicate" })
hl.bind("ALT + B", hl.dsp.exec_cmd("second"), { description = "Duplicate" })'''
        self.assertNotIn('Duplicate', backend.lua_actions(source))
        rows = backend.records([{'key':'mouse:272', 'modmask':8, 'description':'Drag', 'mouse':True, 'dispatcher':'__lua', 'arg':'1'}], {'Drag':'hl.dsp.window.drag()'})
        self.assertEqual(rows[0]['command'], [])
        self.assertIn('LEFT MOUSE', rows[0]['label'])

    def test_plain_fallback_does_not_treat_false_as_mouse_true(self):
        parsed = backend.parse_plain('bindd\n\tmodmask: 8\n\tkey: A\n\tdescription: Custom\n\tmouse: false\n\tdispatcher: exec\n\targ: echo hello\n')
        self.assertEqual(backend.records(parsed, {})[0]['command'], ['hyprctl','dispatch','exec','echo hello'])
