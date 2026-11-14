"""Migration proposal keeps all original bytes; no appletsrc or user config is written."""
import importlib.util
import json
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('r4_migration',Path(__file__).resolve().parents[1]/'src/bwm-plasma-host/migration.py')
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

class MigrationTest(unittest.TestCase):
    def test_lossless_unknowns_and_independent_panel_proposals(self):
        text='{"bar":{"plasma":{"widgets":["clock","external","clock"],"foreign":{"x":42}}}, "idle":{"screen":300}}\n'
        plan=m.proposal(text,['MSI monitor','LG monitor'])
        self.assertEqual(plan['legacyJson'],text)
        self.assertEqual(len(plan['panels']),2)
        widgets=plan['panels'][0]['widgets']
        self.assertEqual(widgets[1]['status'],'unmapped-preserve')
        self.assertNotEqual(widgets[0]['legacyIndex'],widgets[2]['legacyIndex'])
        plan['panels'][0]['widgets'][0]['status']='changed'
        self.assertNotEqual(plan['panels'][1]['widgets'][0]['status'],'changed')
        self.assertFalse(plan['commitAllowed'])
    def test_repeatable_and_does_not_modify_source(self):
        text=json.dumps({'bar':{'plasma':{'widgets':['kickoff']}}})
        self.assertEqual(m.proposal(text,['Display']),m.proposal(text,['Display']))
        self.assertEqual(json.loads(text)['bar']['plasma']['widgets'],['kickoff'])
    def test_connector_identity_is_rejected(self):
        with self.assertRaises(ValueError): m.proposal('{}',['DP-2'])

    def test_seconds_boolean_preserves_existing_clock_enum_mapping(self):
        for value,expected in ((False,1),(True,2)):
            text=json.dumps({'bar':{'plasma':{'widgets':['clock'],'showSeconds':value}}})
            self.assertEqual(m.proposal(text,['Display'])['panels'][0]['widgets'][0]['nativeSettings']['showSeconds'],expected)

    def test_invalid_seconds_is_rejected_instead_of_casting_to_enum(self):
        text=json.dumps({'bar':{'plasma':{'widgets':['clock'],'showSeconds':'false'}}})
        with self.assertRaises(ValueError): m.proposal(text,['Display'])

    def test_native_sections_and_new_favorites_client(self):
        text=json.dumps({'bar':{'plasma':{'widgets':['kickoff','tasks','tray','clock'],
            'kickoff':{'favorites':['preferred://browser'],'favoritesPortedToKAstats':True,'foreignKey':42},
            'taskManager':{'iconSpacing':2},'systemTray':{'scaleIconsToFit':True},
            'clock':{'customDateFormat':'yyyy','showDate':False},'showDate':True}}})
        plan=m.proposal(text,['Display','Second display'])
        panel=plan['panels'][0];widgets=panel['widgets']
        self.assertEqual(panel['containmentPackage'],'org.kde.panel')
        self.assertFalse(widgets[0]['nativeSettings']['favoritesPortedToKAstats'])
        self.assertEqual(widgets[0]['nativeSettings']['foreignKey'],42)
        self.assertTrue(widgets[0]['deferredRuntime'])
        self.assertEqual(widgets[1]['nativeSettings'],{'iconSpacing':2})
        self.assertEqual(widgets[2]['nativeSettings'],{'scaleIconsToFit':True})
        self.assertEqual(widgets[3]['nativeSettings'],{'customDateFormat':'yyyy','showDate':True})
        self.assertEqual(plan['legacyJson'],text)
        widgets[0]['nativeSettings']['favorites'].append('kitty.desktop')
        self.assertEqual(plan['panels'][1]['widgets'][0]['nativeSettings']['favorites'],['preferred://browser'])

    def test_non_object_configuration_is_rejected(self):
        text=json.dumps({'bar':{'plasma':{'widgets':['kickoff'],'kickoff':[]}}})
        with self.assertRaises(ValueError): m.proposal(text,['Display'])

    def test_four_panel_edges_preserved_with_archive(self):
        for edge in ('top','bottom','left','right'):
            text=json.dumps({'bar':{'plasma':{'edge':edge,'widgets':['clock','clock'],'foreign':42}}})+'\n'
            plan=m.proposal(text,['First display','Second display'])
            self.assertEqual([p['edge'] for p in plan['panels']],[edge,edge])
            self.assertEqual(plan['legacyJson'],text)
            self.assertFalse(plan['commitAllowed'])

    def test_edge_empty_or_missing_uses_old_bottom_and_schema_default(self):
        for bar,expected in (({'plasma':{}},'top'),({'bottom':False,'plasma':{'edge':''}},'top'),
                             ({'bottom':True,'plasma':{'edge':''}},'bottom'),({'bottom':True,'plasma':{}},'bottom')):
            self.assertEqual(m.proposal(json.dumps({'bar':bar}),['Display'])['panels'][0]['edge'],expected)

    def test_explicit_edge_overrides_unused_old_bottom(self):
        text=json.dumps({'bar':{'bottom':'unused invalid old value','plasma':{'edge':'right'}}})
        self.assertEqual(m.proposal(text,['Display'])['panels'][0]['edge'],'right')

    def test_invalid_edge_and_fallback_type_rejected(self):
        for value in ('diagonal',None,42,[],{}):
            with self.subTest(edge=value), self.assertRaises(ValueError):
                m.proposal(json.dumps({'bar':{'plasma':{'edge':value}}}),['Display'])
        for value in ('false',0,1,None):
            with self.subTest(bottom=value), self.assertRaises(ValueError):
                m.proposal(json.dumps({'bar':{'bottom':value,'plasma':{'edge':''}}}),['Display'])

    def test_non_object_root_bar_and_panel_rejected(self):
        for value in ([],{'bar':[]},{'bar':None},{'bar':{'plasma':None}}):
            with self.subTest(config=value), self.assertRaises(ValueError):
                m.proposal(json.dumps(value),['Display'])

    def test_native_view_defaults_and_independent_values(self):
        plan=m.proposal('{}',['Display','Second'])
        self.assertEqual(plan['panels'][0]['nativeViewSettings'],{'thickness':44,'floating':0,'panelOpacity':2})
        plan['panels'][0]['nativeViewSettings']['thickness']=80
        self.assertEqual(plan['panels'][1]['nativeViewSettings']['thickness'],44)

    def test_native_thickness_matches_legacy_geometry_clamp_and_zero_default(self):
        for source,expected in ((0,44),(-10,24),(10,24),(38,38),(128,128),(300,128)):
            with self.subTest(thickness=source):
                plan=m.proposal(json.dumps({'bar':{'plasma':{'thickness':source}}}),['Display'])
                self.assertEqual(plan['panels'][0]['nativeViewSettings']['thickness'],expected)

    def test_opacity_styles_preserve_original_enum_and_legacy_floating(self):
        for style,opacity,floating in (('adaptive',0,0),('opaque',1,0),('translucent',2,0),('floating',0,1)):
            with self.subTest(style=style):
                value={'style':style,'floating':False,'opacity':0.37,'floatingGap':12}
                text=json.dumps({'bar':{'plasma':value}})
                plan=m.proposal(text,['Display'])
                self.assertEqual(plan['panels'][0]['nativeViewSettings'],{'thickness':44,'floating':floating,'panelOpacity':opacity})
                self.assertEqual(plan['legacyJson'],text)

    def test_floating_flag_does_not_change_fixed_opacity_mode(self):
        value=m.native_view_settings({'style':'opaque','floating':True})
        self.assertEqual(value,{'thickness':44,'floating':1,'panelOpacity':1})

    def test_invalid_view_types_rejected_without_coercion(self):
        for key,values in (('thickness',(True,'44',None,[],38.5,float('nan'),float('inf'),10**400)),
                           ('floating',('false',0,1,None)),('style',('',False,None,[], 'unknown'))):
            for value in values:
                with self.subTest(key=key,value=value),self.assertRaises(ValueError):
                    m.proposal(json.dumps({'bar':{'plasma':{key:value}}}),['Display'])

    def test_deferred_geometry_not_guessed_as_native_lengths_or_color(self):
        text=json.dumps({'bar':{'plasma':{'length':0.65,'alignment':'center','visibility':'autoHide','color':'red','opacity':0.2,'vendor':42}}})
        plan=m.proposal(text,['Display'])
        self.assertEqual(set(plan['panels'][0]['nativeViewSettings']),{'thickness','floating','panelOpacity'})
        self.assertEqual(plan['legacyJson'],text)
        self.assertFalse(plan['commitAllowed'])
