# SPDX-License-Identifier: GPL-2.0-or-later
import importlib.util
import json
import os
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('native_tray_probe', ROOT/'src/bwm-plasma-host/check-native-tray.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
spec = importlib.util.spec_from_file_location('native_tray_events', ROOT/'src/bwm-plasma-host/check-native-tray-events.py')
events = importlib.util.module_from_spec(spec)
spec.loader.exec_module(events)


class NativeTrayProbeTest(unittest.TestCase):
    def test_menu_targets_focused_description_independent_of_output_order(self):
        monitors = [
            {'name': 'DP-1', 'description': 'LG Electronics LG ULTRAFINE 405NTVS2J655', 'focused': False},
            {'name': 'DP-2', 'description': "Micro-Star Int'l Co. Ltd. MAG 274Q X24 0x01010101", 'focused': True},
        ]
        for inventory in (monitors, list(reversed(monitors))):
            run = Mock(return_value=subprocess.CompletedProcess([], 0, json.dumps(inventory), ''))
            self.assertEqual(events.focused_output(run), monitors[1]['description'])
            run.assert_called_once_with(['hyprctl', '-j', 'monitors'], capture_output=True, text=True, timeout=3, check=True)

    def test_menu_focus_without_one_usable_description_fails(self):
        valid = {'focused': True, 'description': 'Monitor A'}
        for inventory in ([], [valid, dict(valid, description='Monitor B')], [dict(valid, description=' ')],
                          [{'focused': False, 'description': 'Monitor A'}]):
            run = Mock(return_value=subprocess.CompletedProcess([], 0, json.dumps(inventory), ''))
            with self.assertRaisesRegex(ValueError, 'monitor enfocado'):
                events.focused_output(run)

    def test_exact_mode_needs_no_alias_and_pins_each_unique_object(self):
        items = (':1.42/Icon', ':1.43/Other')
        run = Mock(side_effect=[subprocess.CompletedProcess([],0,text,'') for text in
                               ('as 0', 's ":1.42"', 's ":1.43"')])
        endpoints, direct, reasons = m.property_endpoints(items, run, exact_unique=True)
        self.assertEqual(endpoints, {items[0]:(':1.42','/Icon',':1.42'), items[1]:(':1.43','/Other',':1.43')})
        self.assertEqual(direct,{})
        self.assertEqual(reasons['uniqueExactRuleCount'],2)
        self.assertFalse(any('ListNames' in call.args[0] for call in run.call_args_list))
        self.assertEqual(m.proxy_rules(321,endpoints.values())[-2:], [
            '--call=:1.42=org.freedesktop.DBus.Properties.GetAll@/Icon',
            '--call=:1.43=org.freedesktop.DBus.Properties.GetAll@/Other'])

    def test_local_proxy_only_used_for_properties_and_checks_version(self):
        existing = Mock()
        existing.is_file.return_value = True
        with patch.object(m,'LOCAL_PROXY',existing), patch.object(m.subprocess,'run') as run:
            self.assertEqual(m.choose_proxy(False), ('xdg-dbus-proxy',False))
            run.assert_not_called()
            for old in ('xdg-dbus-proxy 0.1.8', 'xdg-dbus-proxy 0.1.8+bwm-sni-unique-1'):
                run.return_value = subprocess.CompletedProcess([],0,old+'\n','')
                with self.assertRaisesRegex(ValueError,'unexpected-local-tray-proxy-version'):
                    m.choose_proxy(True)
            for supported in ('xdg-dbus-proxy 0.1.8+bwm-sni-unique-2', 'xdg-dbus-proxy 0.1.8+bwm-sni-unique-3'):
                run.return_value = subprocess.CompletedProcess([],0,supported+'\n','')
                self.assertEqual(m.choose_proxy(True),(str(existing),True))

    def test_item_rules_pin_method_and_object_with_alias_owner_readback(self):
        items = (':1.42/StatusNotifierItem', ':1.90/Another', 'org.kde.Fixture/Icon', 'org.kde.Activatable/Icon',
                 ':1.99/Vanished')
        owners = {'org.kde.StatusNotifierItem-80-1':':1.42', 'org.kde.StaleAlias':':1.91',
                  'org.kde.Fixture':':1.43', 'org.kde.Activatable':':1.44', ':1.42':':1.42', ':1.90':':1.90'}
        def response(args, **kwargs):
            if args[-1] == 'ListActivatableNames': value = 'as 1 "org.kde.Activatable"'
            elif args[-1] == 'ListNames': value = 'as 6 "org.kde.StatusNotifierItem-80-1" "org.kde.StaleAlias" "org.kde.Fixture" "org.kde.Activatable" ":1.90" "org.kde.StatusNotifierWatcher"'
            elif args[-1] in owners: value = 's "'+owners[args[-1]]+'"'
            else: return subprocess.CompletedProcess(args,1,'','not owned')
            return subprocess.CompletedProcess(args,0,value,'')
        run = Mock(side_effect=response)
        endpoints, direct, reasons = m.property_endpoints(items, run)
        self.assertEqual(endpoints, {items[0]:('org.kde.StatusNotifierItem-80-1','/StatusNotifierItem',':1.42'),
                                     items[2]:('org.kde.Fixture','/Icon',':1.43')})
        self.assertEqual(direct, {items[1]:(':1.90','/Another'), items[3]:(':1.44','/Icon')})
        self.assertEqual(reasons, {'uniqueNameItemCount':3, 'uniqueWithoutAliasCount':1,
                                   'onlyActivatableNameCount':1, 'ownerUnavailableCount':1})
        self.assertEqual(m.proxy_rules(321, endpoints.values())[len(m.proxy_rules(321)):], [
            '--call=org.kde.Fixture=org.freedesktop.DBus.Properties.GetAll@/Icon',
            '--call=org.kde.StatusNotifierItem-80-1=org.freedesktop.DBus.Properties.GetAll@/StatusNotifierItem'])
        self.assertTrue(all('--auto-start=no' in call.args[0] for call in run.call_args_list))
        self.assertFalse(m.ITEM.fullmatch('org.kde.Fixture/Icon/'))
        self.assertFalse(m.ITEM.fullmatch('org.kde.Fixture/Icon/*'))

    def test_direct_scalar_diagnostic_reports_counts_without_proxy_or_icon_names(self):
        run = Mock(side_effect=[subprocess.CompletedProcess([],0,value,'') for value in
                               ('s "Active"', 's "ApplicationStatus"', 's "secret-icon-name"')])
        result = m.direct_metadata({':1.90/Another':(':1.90','/Another')}, run)
        self.assertEqual(result, {'directMetadataCount':1,'directNamedIconCount':1,'directMetadataTimedOut':False})
        for call, prop in zip(run.call_args_list, ('Status','Category','IconName')):
            self.assertEqual(call.args[0][-5:], ['get-property',':1.90','/Another',m.SNI,prop])
            self.assertIn('--auto-start=no',call.args[0])

    def test_properties_require_all_items_usable_with_unchanged_endpoints(self):
        item = 'org.kde.Fixture/Icon'
        snapshot = (':1.2', (item,))
        native = {'nativeRows':1, 'hostNameOwned':True, 'modelReady':True, 'itemDigest':m.item_digest((item,)),
                  'nativePropertiesCount':1, 'nativeUsableIconCount':1}
        endpoints = {item:('org.kde.Fixture','/Icon',':1.43')}
        for data, permission, unchanged, passed in (
            (native, endpoints, True, True), (native, endpoints, False, False),
            (native, {}, True, False), (dict(native, nativeUsableIconCount=0), endpoints, True, False),
            (dict(native, nativePropertiesCount=0), endpoints, True, False),
        ):
            report = {'passed':False}
            m.complete_observation(report, data, snapshot, snapshot, permission, unchanged)
            self.assertEqual(report['passed'], passed)
            self.assertEqual(report['nativePropertiesVerified'], passed)
            self.assertNotIn(item, json.dumps(report))
    def test_same_count_different_items_or_changed_watcher_cannot_pass(self):
        items = (':1.42/Icon', 'org.kde.Test/StatusNotifierItem')
        snapshot = (':1.2', items)
        native = {'nativeRows': 2, 'hostNameOwned': True, 'modelReady': True, 'itemDigest': m.item_digest(items)}
        for case, after, passed in (
            (native, snapshot, True),
            (dict(native, itemDigest=m.item_digest(items[:1] + (':1.43/Icon',))), snapshot, False),
            (native, (':1.3', items), False),
            (dict(native, hostNameOwned=False), snapshot, False),
        ):
            report = {'passed': False}
            m.complete_observation(report, case, snapshot, after)
            self.assertEqual(report['passed'], passed)
            self.assertNotIn(items[0], json.dumps(report))
            self.assertNotIn(native['itemDigest'], json.dumps(report))

    def test_proxy_installs_exact_child_pid_rule_before_native_exec(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            proxy = root/'xdg-dbus-proxy'
            proxy.write_text(f'#!{sys.executable}\n' + '''
import json, os, sys
from pathlib import Path
fd=int(sys.argv[1].split('=')[1])
Path(os.environ['FIXTURE_RULES']).write_text(json.dumps(sys.argv[4:]))
os.write(fd,b'x')
os.read(fd,1)
''')
            native = root/'native'
            native.write_text(f'#!{sys.executable}\n' + '''
import json, os, sys
from pathlib import Path
rules=json.loads(Path(os.environ['FIXTURE_RULES']).read_text())
assert '--own=org.kde.StatusNotifierHost-'+str(os.getpid()) in rules
assert 'WAYLAND_DISPLAY' not in os.environ
assert os.environ['DBUS_SESSION_BUS_ADDRESS']=='unix:path='+os.environ['XDG_RUNTIME_DIR']+'/tray-bus'
assert sys.argv[1:]==['--probe-native-tray-model','2']
print(json.dumps(dict(version=1,nativeRows=2,hostNameOwned=True)))
''')
            for script in (proxy, native): script.chmod(0o700)
            with patch.dict(os.environ, {'PATH':str(root)+os.pathsep+os.environ['PATH'],
                                         'FIXTURE_RULES':str(root/'rules.json'), 'WAYLAND_DISPLAY':'fake'}):
                result=m.run_native(native, root, 'unix:path=/fixture/no-bus', 2)
            self.assertEqual(result['nativeRows'],2)
            rules=json.loads((root/'rules.json').read_text())
            self.assertIn('--filter',rules)
            self.assertEqual(sum(rule.startswith('--own=') for rule in rules),1)
            self.assertFalse(any('RegisterStatusNotifierItem' in rule or rule.startswith('--talk=') or '*' in rule for rule in rules))


if __name__ == '__main__': unittest.main()
