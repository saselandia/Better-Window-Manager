# SPDX-License-Identifier: GPL-2.0-or-later
import argparse
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('r4_geometry',ROOT/'config/hypr/skins/plasma/scripts/r4-geometry-check.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


class GeometryCheckTest(unittest.TestCase):
    def test_cases_require_clean_logical_sizes(self):
        self.assertEqual(m.parse_case('1920x1200:1.25:1'),('1920x1200',1.25,1))
        self.assertEqual(m.parse_case('1920x1080:1.5:3'),('1920x1080',1.5,3))
        for bad in ('1921x1081:1.5:1','1920x1080:1.5:8','1920x1080','DP-1:1:0','1920x1080:9:0'):
            with self.assertRaises(argparse.ArgumentTypeError):m.parse_case(bad)
        for case in m.DEFAULT_CASES:self.assertEqual(m.parse_case('%s:%s:%s'%case),case)

    def test_rule_only_targets_the_named_output_and_resets_reservation(self):
        rule=m.lua_rule('BWMR4-1234abcd','1920x1200',1.25,5)
        self.assertIn('output="BWMR4-1234abcd"',rule);self.assertIn('reserved=0',rule)
        self.assertIn('transform=5',rule);self.assertNotIn('desc:',rule)
        self.assertIn('reserved={top=48}',m.lua_rule('BWMR4-1234abcd','1920x1200',1.25,5,m.RESERVED))

    def test_fixture_keeps_description_selector_by_default(self):
        self.assertEqual(m.maximized.Fixture(Path('/fixture'),'Exact output').selector,'desc:Exact output')
        self.assertEqual(m.maximized.Fixture(Path('/fixture'),'BWMR4-x',selector='BWMR4-x').selector,'BWMR4-x')

    def test_configured_predicate_compares_mode_scale_and_transform(self):
        ok=m.configured('1920x1200',1.25,1)
        self.assertTrue(ok({'width':1920,'height':1200,'scale':1.25,'transform':1}))
        self.assertFalse(ok({'width':1920,'height':1200,'scale':1.5,'transform':1}))
        self.assertFalse(ok({'width':1920,'height':1200,'scale':1.25,'transform':3}))

    def test_requires_explicit_run(self):
        with self.assertRaises(SystemExit):m.main([])


if __name__=='__main__':unittest.main()
