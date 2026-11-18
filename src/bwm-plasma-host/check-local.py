#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Reproducible native configuration regression using only repository fixtures.

No store access or selected third-party sources; does not replace the external-widget gate.
All native clients run offscreen with disposable XDG roots and no session bus.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from unittest.mock import patch


def verify_preview_session_exit(binary, wrapper, profile, env, reservation):
    """Exercise the wrapper and native host with an isolated compositor identity."""
    instance_env = dict(env, HYPRLAND_INSTANCE_SIGNATURE='bwm-r4-exit-fixture')
    hook = Path(__file__).resolve().parents[2]/'config/hypr/skins/plasma/scripts/panel-session.py'
    registration_file = Path(env['XDG_RUNTIME_DIR'])/'bwm-plasma-host-preview/active.json'
    assert not registration_file.exists()
    snapshots = Path(profile)/'snapshots'
    before = set(snapshots.iterdir())
    for stop_mode in ('crash', 'session-exit', 'reservation'):
        crash = stop_mode == 'crash'
        with subprocess.Popen([sys.executable, str(wrapper), '--binary', str(binary), '--selected-profile', '--follow-skin'],
                              env=instance_env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) as preview:
            host_pid = None
            try:
                deadline = time.monotonic()+7
                while time.monotonic() < deadline and preview.poll() is None:
                    if registration_file.is_file():
                        registration = json.loads(registration_file.read_text())
                        control = Path(registration['controlDirectory'])
                        host_pid = registration['pid']
                        ack = json.loads((control/'ack.json').read_text())
                        if ack['command']=='skin' and ack['revision']==1:
                            break
                    time.sleep(.025)
                else:
                    raise AssertionError('Selected preview did not acknowledge startup')
                if crash:
                    os.kill(host_pid, signal.SIGKILL)
                elif stop_mode == 'reservation':
                    with patch.dict(os.environ, {key: instance_env[key] for key in
                                                 ('XDG_RUNTIME_DIR', 'HYPRLAND_INSTANCE_SIGNATURE')}):
                        receipt = reservation.confirm_fixture_exit(preview)
                    assert receipt == {'status':'stopped','revision':2,'exitConfirmed':True}
                else:
                    result = subprocess.run([sys.executable, str(hook), 'session-exit'], env=instance_env,
                                            capture_output=True, text=True, timeout=8, check=True)
                    assert json.loads(result.stdout) == {'status':'stopped','revision':2,'exitConfirmed':True}
                stdout, stderr = preview.communicate(timeout=5)
                assert (preview.returncode != 0) == crash, (stdout, stderr)
                assert not registration_file.exists() and not control.exists()
                after = set(snapshots.iterdir())
                if crash:
                    assert after == before
                else:
                    assert len(after-before)==1 and before <= after
                    checkpoint = json.loads((next(iter(after-before))/'snapshot.json').read_text())
                    assert checkpoint['sourceGeneration']==json.loads((Path(profile)/'head.json').read_text())['generation']
                    before = after
            finally:
                if preview.poll() is None:
                    preview.send_signal(signal.SIGINT)
                    try:
                        preview.communicate(timeout=5)
                    except subprocess.TimeoutExpired:
                        preview.kill()
                        preview.communicate()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--ui-test', type=Path, required=True)
    parser.add_argument('--desktop-test', type=Path)
    parser.add_argument('--tasks-test', type=Path)
    parser.add_argument('--menu-test', type=Path)
    parser.add_argument('--metadata-test', type=Path)
    parser.add_argument('--panel-tasks-test', type=Path)
    parser.add_argument('--lua', type=Path, help='Test-only Lua interpreter for the fake compositor')
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    report = {'version': 1, 'sessionModified': False, 'externalWidgetGateVerified': False,
              'networkUsed': False, 'packages': [], 'ui': []}
    args.report.unlink(missing_ok=True)
    try:
        with tempfile.TemporaryDirectory(prefix='bwm-r4-local-') as tmp:
            root = Path(tmp)
            for name in ('config', 'data', 'cache', 'runtime', 'defaults'):
                (root / name).mkdir(mode=0o700)
            # Same KIOSK host policy as preview-isolated.py: the disposable host never
            # starts applications itself (pinned launchers/.desktop Actions are routed).
            policy_spec=importlib.util.spec_from_file_location('bwm_host_launch_policy',Path(__file__).resolve().parents[2]/'config/hypr/skins/plasma/scripts/native_launch.py')
            policy=importlib.util.module_from_spec(policy_spec);policy_spec.loader.exec_module(policy)
            policy.write_host_policy(root/'defaults')
            env = dict(os.environ, QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software',
                       XDG_CONFIG_HOME=str(root/'config'), XDG_DATA_HOME=str(root/'data'),
                       XDG_CACHE_HOME=str(root/'cache'), XDG_RUNTIME_DIR=str(root/'runtime'),
                       XDG_CONFIG_DIRS=str(root/'defaults'), XDG_DATA_DIRS='/usr/local/share:/usr/share',
                       DBUS_SESSION_BUS_ADDRESS='unix:path='+str(root/'no-bus'))
            env.pop('BWM_R4_DESKTOP_ACTIONS', None);env.pop('BWM_R4_DESKTOP_RUNTIME', None);env.pop('BWM_R4_DESKTOP_CONFIG', None)
            env.pop('KDESYCOCA',None)
            env['BWM_R4_LOCAL_TEST_ROOT']=str(root)
            for key in ('BWM_R4_TASK_ACTIONS','BWM_R4_TASK_RUNTIME','BWM_R4_TASK_CONFIG','BWM_R4_NATIVE_DESKTOPS'):env.pop(key,None)
            for key in ('DISPLAY', 'WAYLAND_DISPLAY', 'HYPRLAND_INSTANCE_SIGNATURE'):
                env.pop(key, None)
            fixtures = Path(__file__).with_name('tests')
            qml = root/'data/qml/org/bwm/r4/configpages'
            shutil.copytree(fixtures/'config-pages-module', qml)
            env['QML_IMPORT_PATH'] = str(root/'data/qml')
            packages = root/'data/plasma/plasmoids'
            packages.mkdir(parents=True)

            def run(*argv):
                reply = subprocess.run([str(v) for v in argv], env=env, capture_output=True,
                                       text=True, timeout=25)
                if reply.returncode:
                    raise RuntimeError(f'{Path(argv[0]).name}: exit {reply.returncode}\n'
                                       +reply.stdout[-4000:]+'\n'+reply.stderr[-2000:])
                return reply.stdout

            for name in ('callback-config', 'shared-config', 'module-config'):
                source = fixtures/name
                plugin = json.loads((source/'metadata.json').read_text())['KPlugin']['Id']
                run('kpackagetool6', '--type', 'Plasma/Applet', '--packageroot', packages,
                    '--install', source)
                if name == 'module-config':
                    # This fixture has string/numeric options; its real transactions are
                    # exercised by QtTest below, not by the CLI's boolean-only exercise.
                    probe = json.loads(run(args.binary, '--probe', plugin))
                    assert probe['itemLoaded'] and not probe['configurationError']
                    assert [page['loader'] for page in probe['pages']] == ['source', 'module']
                    report['packages'].append({'id': plugin, 'moduleAndSourcePagesLoaded': True})
                    continue
                before = json.loads(run(args.binary, '--exercise', plugin))
                assert before['exercisePassed'] and not before['configurationError'], before
                after = json.loads(run(args.binary, '--probe', plugin))
                key = before['exercise']['key']
                assert after['valuesBeforeExercise'][key] == before['exercise']['expectedValue']
                assert before['firstId'] == after['firstId'] and before['secondId'] == after['secondId']
                if name == 'callback-config':
                    assert after['valuesBeforeExercise']['flag'] is False
                    assert after['valuesBeforeExercise']['derived'] == 'flag-off'
                    assert 'lastSeenVersion' not in after['valuesBeforeExercise']
                if name == 'shared-config':
                    frame = json.loads(run(args.binary, '--probe-panel-frame', plugin))
                    assert frame['nativeViewLoaded'] and frame['nativeContainmentAttached']
                    assert frame['containmentPackage'] == 'org.kde.panel'
                    report['defaultSessionFixtureNativePanelVerifiedOffscreen'] = True
                report['packages'].append({'id': plugin, 'exercise': before['exercise'],
                                           'freshProcessReadback': True})
            tray_child = root/'data/plasma/plasmoids/org.bwm.r4.tray-child'
            shutil.copytree(fixtures/'shared-config', tray_child)
            tray_metadata = json.loads((tray_child/'metadata.json').read_text())
            tray_metadata['KPlugin']['Id'] = 'org.bwm.r4.tray-child'
            tray_metadata['X-Plasma-NotificationAreaCategory'] = 'ApplicationStatus'
            (tray_child/'metadata.json').write_text(json.dumps(tray_metadata))
            for test in ('liveCatalogRefreshAndNativeMetadata', 'backendInventoryUsesLiveInstancesAndNativeMetadata',
                         'nativeTrayPropertyRoles', 'nativeTrayInventoryAndProfileCheckpoint', 'nativeTrayChildFreshProcessReadback',
                         'previewStatusRequiresRenderedFrameAndFreshAcknowledgement', 'sharedConfigurationTransactions',
                         'sharedConfigurationFreshProcessReadback', 'moduleConfigurationTransactions',
                         'moduleConfigurationFreshProcessReadback', 'profileRecoveryFromExplicitSnapshot',
                         'profileRecoveryFreshProcessReadback', 'profileRecoveryUsesXdgAuthorityAndChildLease',
                         'profileSelectionTransactionsAndSelectedServer', 'originalPanelSettingsEditMode'):
                output = run(args.ui_test, test)
                assert 'FAIL!' not in output and 'SKIP' not in output, output
                report['ui'].append({'test': test, 'passed': True})
            profile=root/'config/bwm-ui-recovery-profile'
            snapshot=(root/'config/bwm-recovery-snapshot.txt').read_text()
            head=profile/'head.json'
            head.write_text('{broken-cli-head')
            recovered=json.loads(run(args.binary,'--recover-profile',profile/'snapshots'/snapshot))
            assert recovered['status']=='native-profile-recovered' and recovered['activationAllowed'] is False
            assert (Path(recovered['recoveryDirectory'])/'head.json').read_text()=='{broken-cli-head'
            run(args.ui_test,'profileRecoveryFreshProcessReadback')
            head.unlink()
            # The wrapper must bypass --profile-info on a missing head and finish
            # without a preview registration, Wayland connection, or window.
            wrapper=Path(__file__).with_name('preview-isolated.py')
            recovered=json.loads(run(sys.executable,wrapper,'--binary',args.binary,
                                     '--profile',profile,'--recover-snapshot',snapshot))
            assert recovered['previousHeadPresent'] is False and recovered['activationAllowed'] is False
            run(args.ui_test,'profileRecoveryFreshProcessReadback')
            assert not (root/'runtime/bwm-plasma-host-preview/active.json').exists()
            report['nativeProfileRecovery']={'explicitSnapshotVerified':True,'cliBrokenHeadRecovered':True,
                'wrapperMissingHeadRecovered':True,'freshProcessNativeReadback':True,
                'activationAllowed':False,'dailyPanelSelected':False}
            reservation_script = Path(__file__).resolve().parents[2]/'config/hypr/skins/plasma/scripts/r4-reservation-smoke.py'
            reservation_spec = importlib.util.spec_from_file_location('r4_reservation_fixture', reservation_script)
            reservation = importlib.util.module_from_spec(reservation_spec)
            reservation_spec.loader.exec_module(reservation)
            previous_state=env.get('XDG_STATE_HOME');env['XDG_STATE_HOME']=str(root/'selection-state')
            try:
                exported=json.loads(run(args.binary,'--export-profile',profile,'selected-fixture'))
                selection=Path(__file__).with_name('profile-selection.py')
                initial=json.loads(run(sys.executable,selection,'--binary',args.binary,'status'))
                assert initial['selectedProfile'] is None and initial['revision']==0
                chosen=json.loads(run(sys.executable,selection,'--binary',args.binary,'select','selected-fixture','--revision','0'))
                assert chosen['selectedProfile']=='selected-fixture' and chosen['revision']==1 and chosen['activationAllowed'] is False
                fresh=json.loads(run(sys.executable,selection,'--binary',args.binary,'status'))
                assert fresh['profileValidated'] is True and fresh['profile']['directory']==exported['directory']
                verify_preview_session_exit(args.binary, wrapper, exported['directory'], env, reservation)
                report['nativePreviewSessionExit']={'crashReopenPassed':True,'exitReceiptVerified':True,
                    'reservationFixtureExitVerified':True,'checkpointVerified':True,'registryCleanupVerified':True,'physicalLogoutTested':False}
                cleared=json.loads(run(sys.executable,selection,'--binary',args.binary,'clear','--revision','1'))
                assert cleared['revision']==2 and cleared['selectedProfile'] is None
                report['nativeProfileSelection']={'wrapperSelectStatusClearPassed':True,'revisionChecksPassed':True,
                    'selectedServerLeaseAndCleanStopPassed':True,'activationAllowed':False,'dailyPanelActivated':False}
            finally:
                if previous_state is None:env.pop('XDG_STATE_HOME',None)
                else:env['XDG_STATE_HOME']=previous_state
            descriptions = ('BWM Test Reservation A A', 'BWM Test Reservation B B')
            for edge in ('left', 'top', 'right', 'bottom'):
                with tempfile.TemporaryDirectory(prefix='bwm-r4-reservation-layout-') as temporary:
                    profile, _ = reservation.prepare_profile(Path(temporary), args.binary, fixtures/'shared-config', descriptions, edge)
                    assert profile['activationAllowed'] is False
                    assert {p['outputDescription'] for p in profile['panels']} == set(descriptions)
                    generated = json.loads(Path(profile['layoutFile']).with_name('report.json').read_text())
                    assert all(p['edge']==edge and p['nativeViewSettings']['thickness']==48 for p in generated['panels'])
                    # Reopen with the existing local fixture package in a fresh host.
                    reopened = json.loads(run(args.binary, '--profile-info', profile['directory']))
                    assert reopened['panels']==profile['panels'] and reopened['generation']==profile['generation']
            report['nativeReservationProfiles'] = {'edges':['left','top','right','bottom'], 'outputsPerProfile':2,
                'freshProcessReadback':True, 'compositorReservationsVerified':False}
            if args.desktop_test:
                desktop_widget=json.loads(run(args.binary,'--probe','org.kde.plasma.showdesktop'))
                # This original applet paints directly in its root PlasmoidItem;
                # unlike expandable widgets it has no separate fullRepresentation.
                assert desktop_widget['itemLoaded'] and len(desktop_widget['actions'])==2, desktop_widget
                report['nativeDesktopWidgetLoads']=True
                fake=root/'fake-bin';fake.mkdir()
                executable=fake/'hyprctl'
                payload=(fixtures/'desktop-hyprctl.py').read_text().split('\n',1)[1]
                executable.write_text('#!'+sys.executable+'\n'+payload);executable.chmod(0o700)
                clients=root/'fake-clients.json';clients.write_text(json.dumps({'address':'0xabc','pid':os.getpid(),
                    'workspace':{'id':1,'name':'1'},'mapped':True,'floating':False,'hidden':False,'tags':[]}))
                env.update(BWM_R4_DESKTOP_ACTIONS='1',BWM_R4_DESKTOP_RUNTIME=str(root/'runtime'),
                    BWM_R4_FAKE_CLIENTS=str(clients),BWM_R4_FAKE_ACTIONS=str(root/'fake-actions.log'),
                    BWM_R4_FAKE_BIN=str(fake),PATH=str(fake)+os.pathsep+os.environ.get('PATH',''))
                config=root/'config/illogical-impulse';config.mkdir(exist_ok=True)
                (config/'config.json').write_text('{"appearance":{"bwmTheme":"plasma"}}')
                report['nativeDesktopControllerOutput']=run(args.desktop_test)
                report['desktopFakeActions']=(root/'fake-actions.log').read_text()
                report['desktopFakeFinalClient']=json.loads(clients.read_text())
                assert json.loads(clients.read_text())['workspace']['id']==1, 'Common desktop action did not finish restoration'
                report['nativeDesktopControllerWithFakeIpcPassed']=True
                env.pop('BWM_R4_DESKTOP_ACTIONS');env.pop('BWM_R4_DESKTOP_RUNTIME')
                if args.tasks_test:
                    lua=str(args.lua.resolve()) if args.lua else shutil.which('lua')
                    if not lua:raise RuntimeError('Lua interpreter required for native full-screen IPC fixture')
                    env['BWM_R4_TEST_LUA']=lua
                    client=json.loads(clients.read_text());client.update(title='Native task fixture',
                        **{'class':'native-task-fixture','at':[10,20],'size':[800,600],'monitor':0,'fullscreen':0})
                    clients.write_text(json.dumps(client))
                    config=root/'config/illogical-impulse';config.mkdir(exist_ok=True)
                    (config/'config.json').write_text('{"appearance":{"bwmTheme":"plasma"}}')
                    report['nativeTasksModelOutput']=run(args.tasks_test)
                    assert json.loads(clients.read_text())['workspace']['id']==1
                    report['nativeTasksModelWithFakeIpcPassed']=True
            if args.menu_test:
                report['nativeTaskMenuOutput']=run(args.menu_test)
                report['nativeTaskMenuPassed']=True
            if args.panel_tasks_test:
                report['nativePanelTaskRegistrationOutput']=run(args.panel_tasks_test)
                report['nativePanelTaskRegistrationPassed']=True
            if args.metadata_test:
                report['nativeTaskMetadataOutput']=run(args.metadata_test)
                report['nativeTaskMetadataPassed']=True
            for package in report['packages']:
                run('kpackagetool6', '--type', 'Plasma/Applet', '--packageroot', packages,
                    '--remove', package['id'])
                assert not (packages/package['id']).exists()
            report['cleanupVerified'] = True
        report['passed'] = True
    except (OSError, ValueError, KeyError, AssertionError, subprocess.SubprocessError, RuntimeError) as exc:
        report['passed'] = False
        report['error'] = str(exc)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
