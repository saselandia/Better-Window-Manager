"""F7 policy and geometry tests. No plugin is loaded/unloaded and no real window is moved."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'config/hypr/scripts'))
import bwm_windows as windows
spec=importlib.util.spec_from_file_location('quick_tile_csd',ROOT/'config/hypr/scripts/quick-tile.py')
qt=importlib.util.module_from_spec(spec);spec.loader.exec_module(qt)

class PolicyTests(unittest.TestCase):
    def test_protocol_state_and_properties(self):
        with tempfile.TemporaryDirectory() as folder:
            binary=Path(folder)/'policy'
            result=subprocess.run([os.environ.get('CXX','g++'),'-std=c++23','-Wall','-Wextra','-I',str(ROOT/'src/breezebars'),str(ROOT/'tests/csd_logic_test.cpp'),'-o',str(binary)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            result=subprocess.run([str(binary)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertIn('ack/commit',result.stdout)
    @unittest.skipUnless(shutil.which('Hyprland') and shutil.which('nm'),'Hyprland/binutils unavailable')
    def test_hook_setters_are_exported_by_installed_hyprland(self):
        result=subprocess.run(['nm','-D','--defined-only',os.path.realpath(shutil.which('Hyprland'))],capture_output=True,text=True,check=True)
        for symbol in ['_ZN24CZxdgDecorationManagerV124setGetToplevelDecorationEOSt8functionIFvPS_jP11wl_resourceEE','_ZN34COrgKdeKwinServerDecorationManager9setCreateEOSt8functionIFvPS_jP11wl_resourceEE']:
            self.assertIn(symbol,result.stdout)

class FrameTests(unittest.TestCase):
    def record(self):return {'address':'0xa','pid':10,'visible':True,'ready':True,'borders':{'left':4,'top':28,'right':4,'bottom':4}}
    def test_identity_ignores_duplicate_titles_and_reused_addresses(self):
        record=self.record();data={('0xa',10):record}
        self.assertTrue(windows.has_titlebar({'address':'0xa','pid':10},data))
        self.assertFalse(windows.has_titlebar({'address':'0xa','pid':11},data))
        self.assertFalse(windows.has_titlebar({'address':'0xb','pid':10},data))
    def test_hidden_frame_and_invalid_extents_are_zero(self):
        self.assertEqual(sum(windows.decoration_extents({'address':'0xa','pid':10},set()).values()),0)
        record=self.record();record['visible']=False
        self.assertEqual(sum(windows.decoration_extents(record,{('0xa',10):record}).values()),0)
        self.assertEqual(windows.normalized_extents({'top':float('nan'),'left':-1,'right':3.2}),{'left':0,'top':0,'right':4,'bottom':0})
    def test_json_snapshot_and_no_fixed_bar_fallback(self):
        record=self.record();output=json.dumps({'api':'breezebars-csd','version':1,'windows':[record]})
        with patch.object(windows.subprocess,'run',return_value=subprocess.CompletedProcess([],0,output,'')):
            self.assertEqual(windows.titlebars(),{('0xa',10):record})
        for text in ['old plugin | title | barra=si (kde)','unknown request','{}']:
            with patch.object(windows.subprocess,'run',return_value=subprocess.CompletedProcess([],0,text,'')):
                self.assertEqual(windows.titlebars(),{})
    def test_kde_borders_are_inside_tile_and_traditional_rect(self):
        borders=self.record()['borders'];monitor={'x':0,'y':0,'width':1000,'height':800,'scale':1,'reserved':[0,0,0,0]}
        self.assertEqual(qt.content_geometry(0,0,1000,800,borders),(4,28,992,768))
        self.assertEqual(windows.traditional_box([0,0],[1000,800],monitor,borders,{'edgeMargin':0}), (4,28,992,768))
        self.assertEqual(qt.content_geometry(0,0,1000,800,{}),(0,0,1000,800))
        self.assertEqual(windows.traditional_box([0,0],[1000,800],monitor,{}, {'edgeMargin':0,'titlebar':30}), (0,0,1000,800))

class AuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec=importlib.util.spec_from_file_location('csd_audit',ROOT/'config/hypr/skins/plasma/scripts/csd-audit.py')
        cls.audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.audit)
    def test_legacy_explicit_none_and_client_modes(self):
        record={'ready':True,'observed':{'kde':True,'kdeExplicit':True,'decorate':True},'kdeRequested':1,'sent':1,'applied':1,'visible':False}
        self.assertTrue(self.audit.assess(record).startswith('OK'))
        record.update(kdeRequested=0,sent=0,applied=0)
        self.assertTrue(self.audit.assess(record).startswith('OK'))
        record['observed']['kdeExplicit']=False
        self.assertIn('FALLO',self.audit.assess(record))
    def test_rejects_native_forced_ssd_when_client_requests_csd(self):
        record={'ready':True,'observed':{'xdg':True,'decorate':True},'xdgRequested':1,'sent':2,'applied':2,'visible':False}
        self.assertIn('FALLO',self.audit.assess(record))
        record.update(sent=1,applied=1)
        self.assertTrue(self.audit.assess(record).startswith('OK'))
        record.update(xdgRequested=2,sent=2)
        self.assertIn('transición',self.audit.assess(record))
    def test_never_labels_absent_apps_as_tested(self):
        report=self.audit.report({'windows':[]})
        self.assertIn('No observada',report)
        self.assertNotIn('| OK',report)
