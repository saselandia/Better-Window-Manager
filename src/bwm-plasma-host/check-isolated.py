#!/usr/bin/env python3
"""Exercise installed libplasma with explicitly selected packages in disposable XDG roots."""
import argparse
import importlib.util
import hashlib
import json
import os
import shutil
from pathlib import Path
import subprocess
import tempfile
import time
import signal

p=argparse.ArgumentParser()
p.add_argument('--binary',type=Path,required=True)
p.add_argument('--upstream',type=Path,required=True,help='Extracted libplasma 6.7.5 source')
p.add_argument('--external',type=Path,required=True,help='Explicitly selected third-party applet directory')
p.add_argument('--report',type=Path,required=True)
p.add_argument('--ui-test',type=Path)
a=p.parse_args()
a.report.unlink(missing_ok=True)
with tempfile.TemporaryDirectory(prefix='bwm-r4-check-') as tmp:
    root=Path(tmp)
    env=dict(os.environ,QT_QPA_PLATFORM='offscreen',QT_QUICK_BACKEND='software',
             XDG_CONFIG_HOME=str(root/'config'),XDG_DATA_HOME=str(root/'data'),
             XDG_CACHE_HOME=str(root/'cache'),XDG_RUNTIME_DIR=str(root/'runtime'),
             XDG_CONFIG_DIRS=str(root/'defaults'),XDG_DATA_DIRS='/usr/local/share:/usr/share',
             DBUS_SESSION_BUS_ADDRESS='unix:path='+str(root/'no-bus'))
    env.pop('BWM_R4_DESKTOP_ACTIONS',None);env.pop('BWM_R4_DESKTOP_RUNTIME',None);env.pop('BWM_R4_DESKTOP_CONFIG',None)
    for key in ('BWM_R4_TASK_ACTIONS','BWM_R4_TASK_RUNTIME','BWM_R4_TASK_CONFIG','BWM_R4_NATIVE_DESKTOPS'):env.pop(key,None)
    for name in ('config','data','cache','runtime','defaults'): (root/name).mkdir(mode=0o700)
    (root/'defaults/kdedefaults').mkdir()
    env['XDG_CONFIG_DIRS']=str(root/'defaults/kdedefaults')+os.pathsep+str(root/'defaults')
    packageRoot=root/'data/plasma/plasmoids'
    packageRoot.mkdir(parents=True)
    def run(argv,execution_env=None):
        r=subprocess.run([str(v) for v in argv],env=env if execution_env is None else execution_env,capture_output=True,text=True,timeout=25)
        if r.returncode:
            lines=r.stdout.splitlines()
            failures='\n'.join('\n'.join(lines[i:i+6]) for i,line in enumerate(lines) if 'FAIL!' in line)
            raise RuntimeError(f'{argv}: {r.stderr[-2000:]}\n{failures}\n{r.stdout[-2000:]}')
        return r.stdout
    report={'session_modified':False,'live_panel_integrated':False,'packages':[]}
    invalid=subprocess.run([str(a.binary),'--maximize-fixture','invalid'],env=env,capture_output=True,timeout=5)
    assert invalid.returncode==2
    fixtureProcess=subprocess.Popen([str(a.binary),'--maximize-fixture','org.bwm.r4.maximize.'+'a'*32],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        time.sleep(.25)
        assert fixtureProcess.poll() is None,'The isolated fixture must stay alive for its owner'
    finally:
        if fixtureProcess.poll() is None:fixtureProcess.terminate()
        fixtureProcess.wait(timeout=5)
    # The headless KNS cycle installs third-party code: refused outside disposable XDG roots.
    knsEnv=dict(env,XDG_DATA_HOME=str(Path(__file__).with_name('tests')))
    refused=subprocess.run([str(a.binary),'--kns-search','clock'],env=knsEnv,capture_output=True,text=True,timeout=10)
    assert refused.returncode==2 and 'temporary' in refused.stderr,refused
    report['knsOutsideTemporaryRootsRefused']=True
    report['maximizedFixtureOffscreenLifecycle']={'invalidIdentityRejected':True,'started':True,'ownerStopCompleted':True,'realWindowGeometryVerified':False}
    fixture=Path(__file__).with_name('tests')/'shared-config'
    fixtureId=json.loads((fixture/'metadata.json').read_text())['KPlugin']['Id']
    run(['kpackagetool6','--type','Plasma/Applet','--packageroot',packageRoot,'--install',fixture])
    tests=Path(__file__).with_name('tests')
    moduleRoot=root/'data/qml'
    shutil.copytree(tests/'config-pages-module',moduleRoot/'org/bwm/r4/configpages')
    env['QML_IMPORT_PATH']=str(moduleRoot)+(os.pathsep+env['QML_IMPORT_PATH'] if env.get('QML_IMPORT_PATH') else '')
    moduleFixture=tests/'module-config'
    moduleIds=['org.bwm.r4.module-config']
    run(['kpackagetool6','--type','Plasma/Applet','--packageroot',packageRoot,'--install',moduleFixture])
    cases={
        'missing-module':{'configUiModule':'org.bwm.r4.missing','configUiComponent':'Page','source':'File.qml'},
        'missing-component':{'configUiModule':'org.bwm.r4.configpages','configUiComponent':'MissingPage','source':'File.qml'},
        'non-item':{'configUiModule':'org.bwm.r4.configpages','configUiComponent':'NonItem'},
        'required-extra':{'configUiModule':'org.bwm.r4.configpages','configUiComponent':'RequiredExtra'},
        'incomplete':{'configUiModule':'org.bwm.r4.configpages'},
        'kcm':{'pluginName':'fixture_kcm','source':'File.qml'},
        'fallback':{'configUiModule':'org.bwm.r4.missing','source':'File.qml'},
        'absolute':{'source':str(packageRoot/'org.bwm.r4.module-absolute/contents/ui/File.qml')},
    }
    for name,descriptor in cases.items():
        source=root/('module-'+name);shutil.copytree(moduleFixture,source)
        metadata=json.loads((source/'metadata.json').read_text());plugin='org.bwm.r4.module-'+name
        metadata['KPlugin']['Id']=plugin;(source/'metadata.json').write_text(json.dumps(metadata))
        properties='; '.join(key+': '+json.dumps(value) for key,value in descriptor.items())
        (source/'contents/config/config.qml').write_text('import org.kde.plasma.configuration\nConfigModel { ConfigCategory { name: "Case"; '+properties+' } }\n')
        run(['kpackagetool6','--type','Plasma/Applet','--packageroot',packageRoot,'--install',source])
        moduleIds.append(plugin)
    moduleProbe=json.loads(run([a.binary,'--probe','org.bwm.r4.module-config']))
    assert not moduleProbe['configurationError']
    assert [page['loader'] for page in moduleProbe['pages']]==['source','module']
    report['moduleConfigurationProbe']=moduleProbe
    failedProbe=json.loads(run([a.binary,'--probe','org.bwm.r4.module-missing-module']))
    assert 'org.bwm.r4.missing' in failedProbe['configurationError'] and not failedProbe['pages']
    report['moduleConfigurationFailureProbe']=failedProbe
    panelThemeRoot=root/'data/plasma/desktoptheme';panelThemeRoot.mkdir(parents=True)
    panelThemeIds=[]
    # Own solid-color SVGs make native theme selection/prefix rendering observable.
    for suffix,base in [('a','#22aa55'),('b','#dd2277')]:
        plugin='org.bwm.r4.panel-'+suffix;source=root/('panel-theme-'+suffix)
        (source/'widgets').mkdir(parents=True);(source/'solid/widgets').mkdir(parents=True)
        (source/'metadata.json').write_text(json.dumps({'KPackageStructure':'Plasma/Theme',
            'KPlugin':{'Id':plugin,'Name':'Disposable panel '+suffix,'Version':'1.0','License':'GPL-2.0-or-later'}}))
        cells={'center':(2,2,20,20),'top':(2,0,20,2),'bottom':(2,22,20,2),'left':(0,2,2,20),'right':(22,2,2,20),
            'topleft':(0,0,2,2),'topright':(22,0,2,2),'bottomleft':(0,22,2,2),'bottomright':(22,22,2,2)}
        colors={'':base,'north':'#2255aa','south':base,'west':'#cc6622','east':'#8844cc','floating':base,'thick':base}
        pieces=['<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">']
        for prefix,color in colors.items():
            for name,(x,y,w,h) in cells.items():
                element=(prefix+'-' if prefix else '')+name
                pieces.append(f'<rect id="{element}" x="{x}" y="{y}" width="{w}" height="{h}" fill="{color}"/>')
        svg='\n'.join(pieces+['</svg>'])
        (source/'widgets/panel-background.svg').write_text(svg);(source/'solid/widgets/panel-background.svg').write_text(svg)
        run(['kpackagetool6','--type','Plasma/Theme','--packageroot',panelThemeRoot,'--install',source])
        panelThemeIds.append(plugin)
    builtin='org.kde.plasma.analogclock'
    native=json.loads(run([a.binary,'--exercise',builtin]))
    assert native['itemLoaded'] and native['full'] and native['exercisePassed']
    reopened=json.loads(run([a.binary,'--probe',builtin]))
    assert reopened['valuesBeforeExercise'][native['exercise']['key']]==native['exercise']['expectedValue']
    native['freshProcessReadback']=True
    report['nativeBuiltin']=native
    # Store widgets (e.g. Thermal Monitor) use saveConfig() hooks and cfg_ helpers that are not
    # in main.xml. AppletConfiguration.qml 6.7.5 calls the hook and ignores those helpers.
    callback=Path(__file__).with_name('tests')/'callback-config'
    run(['kpackagetool6','--type','Plasma/Applet','--packageroot',packageRoot,'--install',callback])
    cb=json.loads(run([a.binary,'--exercise','org.bwm.r4.callback-config']))
    assert cb['exercisePassed'] and cb['exercise']['key']=='flag' and not cb['configurationError'],cb
    cbRead=json.loads(run([a.binary,'--probe','org.bwm.r4.callback-config']))
    assert cbRead['valuesBeforeExercise']['flag'] is False and cbRead['valuesBeforeExercise']['derived']=='flag-off',cbRead['valuesBeforeExercise']
    assert 'lastSeenVersion' not in cbRead['valuesBeforeExercise']
    report['callbackPage']={'saveConfigHonoured':True,'unschemedHelperIgnored':True,'freshProcessReadback':True}
    packages=[a.upstream/'examples/applets/compactrepresentation',a.upstream/'examples/applets/config',a.external]
    for source in packages:
        metadata=json.loads((source/'metadata.json').read_text())
        plugin=metadata['KPlugin']['Id']
        run(['kpackagetool6','--type','Plasma/Applet','--packageroot',packageRoot,'--install',source])
        listed=json.loads(run([a.binary,'--catalog']))
        assert any(m['id']==plugin for m in listed)
        mode='--probe' if source.name=='compactrepresentation' else '--exercise'
        result=json.loads(run([a.binary,mode,plugin]))
        assert result['itemLoaded'] and result['full']
        assert result['firstId']!=result['secondId']
        frame=json.loads(run([a.binary,'--probe-panel-frame',plugin]))
        assert frame['nativeViewLoaded'] and frame['nativeContainmentAttached'] and frame['frameReadbackAvailable']
        assert frame['containmentPackage']=='org.kde.panel' and frame['width']==640 and frame['height']==48
        assert not frame['waylandVerified'] and not frame['adaptiveWindowBackend'] and not frame['compositorBlur']
        result['nativePanelFrameProbe']=frame
        if mode=='--exercise':
            assert result['exercisePassed'] and all(page['loaded'] for page in result['pages'])
            reopened=json.loads(run([a.binary,'--probe',plugin]))
            assert reopened['firstId']==result['firstId']
            key=result['exercise']['key']
            assert reopened['valuesBeforeExercise'][key]==result['exercise']['expectedValue']
            result['freshProcessReadback']=True
            if a.ui_test:
                env['BWM_TEST_APPLET']=plugin
                output=run([a.ui_test])
                result['nativePopupAndConfigButtonsPassed']=True
                result['originalPanelConfigureActionPassed']=True
                if plugin=='AndromedaLauncher':
                    result['packageOwnedDialogOffscreenPassed']=True
                    result['packageOwnedDialogLayerRolePrepared']=True
                result['packageWindowBoundaryChecksPassed']=True
                result['viewOutputGeometryChecksPassed']=True
                result['sharedConfigurationTransactionsPassed']=True
                result['sharedConfigurationFreshProcessReadbackOutput']=run([a.ui_test,'sharedConfigurationFreshProcessReadback'])[-1500:]
                result['nativePanelLifecycleAndActionsPassed']=True
                result['nativePanelFreshProcessReadbackOutput']=run([a.ui_test,'nativePanelApiFreshProcessReadback'])[-2000:]
                result['moduleConfigurationTransactionsPassed']=True
                result['originalShellPanelFramePassed']=True
                result['nativePanelThemeAndEdgesPassed']=True
                result['nativePanelPreferencesPassed']=True
                result['nativePanelPreferencesFreshProcessReadbackOutput']=run([a.ui_test,'panelViewPreferencesFreshProcessReadback'])[-2000:]
                result['panelRuntimeLifecyclePassed']=True
                result['panelRuntimeFreshProcessReadbackOutput']=run([a.ui_test,'panelRuntimeFreshProcessReadback'])[-3000:]
                result['registeredSkinHookControlPassed']=True
                result['previewFrameReadinessAndFreshStatusPassed']=True
                result['nativeVisibilityAndReservationRequestsPassed']=True
                result['nativePolicyFreshProcessReadbackOutput']=run([a.ui_test,'nativePanelPolicyFreshProcessReadback'])[-2000:]
                result['persistentProfileTransactionsPassed']=True
                result['persistentProfileFreshProcessReadbackOutput']=run([a.ui_test,'profileStoreFreshProcessReadback'])[-3000:]
                result['xdgStateProfileExportPassed']=True
                result['moduleConfigurationFreshProcessReadbackOutput']=run([a.ui_test,'moduleConfigurationFreshProcessReadback'])[-1500:]
                result['uiTestOutput']=output[-4000:]
                del env['BWM_TEST_APPLET']
            # Test the standalone entry point with no visible output, including
            # lifetime without windows, actual publisher IPC files and clean stop.
            publisher=Path(__file__).resolve().parents[2]/'config/hypr/skins/plasma/scripts/panel-session.py'
            control=Path(tempfile.mkdtemp(prefix='control-',dir=root/'runtime'))
            token=hashlib.sha256(plugin.encode()).hexdigest()
            controlPath=control/'control.json'
            controlPath.write_text(json.dumps({'version':1,'token':token,'revision':0,'command':'skin','skin':'default'}));controlPath.chmod(0o600)
            followEnv=dict(env,BWM_R4_CONTROL_DIR=str(control),BWM_R4_SESSION_TOKEN=token,BWM_R4_OUTPUT='Unavailable fixture output')
            logPath=root/'following-preview.log'
            with logPath.open('w') as log:
                child=subprocess.Popen([str(a.binary),'--follow-panel-preview',plugin],env=followEnv,stdout=log,stderr=log)
                try:
                    deadline=time.monotonic()+5
                    while not (control/'ack.json').exists() and child.poll() is None and time.monotonic()<deadline:time.sleep(.01)
                    assert (control/'ack.json').exists(),logPath.read_text()[-2000:]
                    run(['python3',publisher,'register',control,str(child.pid),token])
                    duplicate=subprocess.run([str(a.binary),'--follow-panel-preview',plugin],env=followEnv,capture_output=True,text=True,timeout=5)
                    assert duplicate.returncode==9 and 'Another preview owns' in duplicate.stderr
                    run(['python3',publisher,'event','after','default','plasma'])
                    ack=json.loads((control/'ack.json').read_text())
                    assert ack['skin']=='plasma' and all(not p['visible'] and p['status']=='output-unavailable' for p in ack['panels'])
                    beforeRevision=ack['revision']
                    live=json.loads(run(['python3',publisher,'status']))
                    assert live['active'] and live['revision']==beforeRevision+1 and live['skin']=='plasma'
                    assert not live['runtime']['renderReady'] and not live['runtime']['replacementReady']
                    assert 'output-unavailable' in live['runtime']['blockers']
                    assert live['runtime']['scope']=='isolated-preview'
                    assert child.poll() is None
                    run(['python3',publisher,'event','before','plasma','retro'])
                    run(['python3',publisher,'stop']);assert child.wait(timeout=5)==0
                    result['followingPreviewProcess']={'startedInactive':True,'aliveWithoutWindows':True,
                        'singletonRejected':True,'skinAppliedWithUnmatchedOutput':ack['panels'],
                        'freshStatus':live,'cleanStop':True}
                finally:
                    if child.poll() is None:
                        child.terminate()
                        try:child.wait(timeout=5)
                        except subprocess.TimeoutExpired:child.kill();child.wait()
                    run(['python3',publisher,'unregister',token])
            if plugin=='org.kde.example.configuration':
                # Exercise the user-facing wrapper itself, including duplicate
                # registration and terminal Ctrl+C with a clean stop transaction.
                wrapper=Path(__file__).with_name('preview-isolated.py')
                registry=root/'runtime/bwm-plasma-host-preview/active.json'
                argv=['python3',str(wrapper),'--binary',str(a.binary),'--package',str(source),
                      '--native-panel','--layer-panel','--follow-skin','--output','Unavailable fixture output']
                for stopMode in ('external-stop','terminal-interrupt','native-policy-stop'):
                    invocation=argv+(['--native-policy'] if stopMode=='native-policy-stop' else [])
                    wrapperEnvironment=dict(env,BWM_R4_NATIVE_PANEL_POLICY='1') # Must not enable the mode without its explicit flag.
                    logPath=root/'wrapper.log'
                    with logPath.open('w') as log:
                        wrapperChild=subprocess.Popen(invocation,env=wrapperEnvironment,stdout=log,stderr=log,start_new_session=True)
                        try:
                            deadline=time.monotonic()+5
                            while 'Prueba R4 registrada' not in logPath.read_text() and wrapperChild.poll() is None and time.monotonic()<deadline:time.sleep(.01)
                            assert registry.exists() and wrapperChild.poll() is None,logPath.read_text()[-2000:]
                            assert 'Prueba R4 registrada' in logPath.read_text()
                            live=json.loads(run(['python3',publisher,'status']))
                            assert live['active'] and live['runtime']['scope']=='isolated-preview'
                            assert not live['runtime']['replacementReady'] and not live['runtime']['renderReady']
                            assert live['runtime']['nativePanelPolicy']==(stopMode=='native-policy-stop')
                            if stopMode!='terminal-interrupt':
                                if stopMode=='external-stop':
                                    duplicate=subprocess.run(invocation,env=env,capture_output=True,text=True,timeout=8)
                                    assert duplicate.returncode==1 and 'Ya hay una prueba' in duplicate.stdout+duplicate.stderr
                                    assert registry.exists() and wrapperChild.poll() is None
                                run(['python3',publisher,'stop']);assert wrapperChild.wait(timeout=5)==0
                            else:
                                os.killpg(wrapperChild.pid,signal.SIGINT);assert wrapperChild.wait(timeout=5)==130
                            assert not registry.exists()
                        finally:
                            if wrapperChild.poll() is None:
                                wrapperChild.send_signal(signal.SIGINT)
                                try:wrapperChild.wait(timeout=7)
                                except subprocess.TimeoutExpired:wrapperChild.kill();wrapperChild.wait()
                result['followingPreviewWrapper']={'registeredInactive':True,'duplicateRejectedBeforeActivation':True,
                    'existingRegistrationPreserved':True,'externalStopConsumedBeforeCleanup':True,
                    'terminalInterruptCleanStopAndUnregister':True,'nativePolicyFlagReachedRuntime':True}
        else: assert result['compact']
        run(['kpackagetool6','--type','Plasma/Applet','--packageroot',packageRoot,'--remove',plugin])
        assert not (packageRoot/plugin).exists()
        assert not any(m['id']==plugin for m in json.loads(run([a.binary,'--catalog'])))
        result['nativeInstallRemove']=True
        report['packages'].append(result)
    run(['kpackagetool6','--type','Plasma/Applet','--packageroot',packageRoot,'--remove',fixtureId])
    for plugin in moduleIds:
        run(['kpackagetool6','--type','Plasma/Applet','--packageroot',packageRoot,'--remove',plugin])
        assert not (packageRoot/plugin).exists()
    report['moduleConfiguration']={'module':'org.bwm.r4.configpages','temporaryPackages':moduleIds,
        'nativeInstallRemove':True,'scope':'Own disposable fixtures; not third-party or KCM acceptance'}
    for plugin in panelThemeIds:
        run(['kpackagetool6','--type','Plasma/Theme','--packageroot',panelThemeRoot,'--remove',plugin])
        assert not (panelThemeRoot/plugin).exists()
    report['panelSvgThemes']={'packages':panelThemeIds,'nativeInstallRemove':True,'scope':'Own disposable SVG assets; not compositor blur/shadow certification'}
    themeId='org.bwm.r4.disposable-theme'
    themeSource=root/'theme-source';(themeSource/'contents/layouts').mkdir(parents=True)
    (themeSource/'metadata.json').write_text(json.dumps({'KPackageStructure':'Plasma/LookAndFeel',
        'KPlugin':{'Id':themeId,'Name':'Disposable theme inventory fixture','Version':'1.0','License':'GPL-2.0-or-later'}}))
    defaults='[plasmarc][Theme]\nname=breeze-dark\n[kwinrc][org.kde.kdecoration2]\nlibrary=org.kde.breeze\n[UnknownFile][Vendor]\nKeep=42\n'
    (themeSource/'contents/defaults').write_text(defaults)
    script='throw new Error("R4_LAYOUT_MUST_NOT_EXECUTE");\n'
    (themeSource/'contents/layouts/org.kde.plasma.desktop-layout.js').write_text(script)
    themeRoot=root/'data/plasma/look-and-feel';themeRoot.mkdir(parents=True)
    run(['kpackagetool6','--type','Plasma/LookAndFeel','--packageroot',themeRoot,'--install',themeSource])
    theme=next(t for t in json.loads(run([a.binary,'--theme-catalog'])) if t['id']==themeId)
    assert theme['valid'] and theme['status']=='inventory-only'
    assert any(e['groups']==['UnknownFile','Vendor'] and e['key']=='Keep' and e['value']=='42' for e in theme['defaults'])
    assert any(e['component']=='decoration-reference' for e in theme['defaults'])
    assert any(e['component']=='desktop-svg-reference' for e in theme['defaults'])
    assert any(s['sha256']==hashlib.sha256(script.encode()).hexdigest() for s in theme['scripts'])
    assert all(not s['executeAllowed'] for s in theme['scripts'])
    assert (themeSource/'contents/defaults').read_text()==defaults
    run(['kpackagetool6','--type','Plasma/LookAndFeel','--packageroot',themeRoot,'--remove',themeId])
    assert not any(t['id']==themeId for t in json.loads(run([a.binary,'--theme-catalog'])))
    report['themeInventory']=dict(theme=theme,nativeInstallRemove=True,sourcePreserved=True,layoutExecutionEnabled=False)
    spec=importlib.util.spec_from_file_location('r4_migration',Path(__file__).with_name('migration.py'))
    migration=importlib.util.module_from_spec(spec);spec.loader.exec_module(migration)
    legacy=json.dumps({'bar':{'plasma':{'widgets':['clock','clock'],'showDate':False,'showSeconds':True,'foreign':{'keep':42}}},'idle':{'screen':300}})+'\n'
    plan=migration.proposal(legacy,['MSI fixture','LG fixture'])
    proposalPath=root/'plan.json';proposalPath.write_text(json.dumps(plan))
    def rejected(argv,execution_env=None):
        result=subprocess.run([str(v) for v in argv],env=env if execution_env is None else execution_env,capture_output=True,text=True,timeout=25)
        assert result.returncode!=0
        return result.stderr.strip()
    broken=migration.proposal(legacy,['MSI fixture']);broken['sourceSha256']='bad'
    badPath=root/'bad.json';badPath.write_text(json.dumps(broken))
    rejected([a.binary,'--stage-migration',badPath])
    missing=migration.proposal(json.dumps({'bar':{'plasma':{'widgets':['uninstalled']}}}),['MSI fixture'])
    badPath.write_text(json.dumps(missing));rejected([a.binary,'--stage-migration',badPath])
    unknown=migration.proposal(legacy,['MSI fixture']);unknown['panels'][0]['widgets'][0]['nativeSettings']['unsupportedLegacySetting']=1
    badPath.write_text(json.dumps(unknown));rejected([a.binary,'--stage-migration',badPath])
    edgeSource=json.dumps({'bar':{'plasma':{'edge':'right','widgets':['clock']}}})
    forged=migration.proposal(edgeSource,['MSI fixture']);forged['panels'][0]['edge']='top'
    badPath.write_text(json.dumps(forged));rejected([a.binary,'--stage-migration',badPath])
    for badBar in ({'plasma':{'edge':'diagonal','widgets':['clock']}},{'bottom':'false','plasma':{'edge':'','widgets':['clock']}}):
        invalid=migration.proposal(edgeSource,['MSI fixture']);invalid['legacyJson']=json.dumps({'bar':badBar})
        invalid['sourceSha256']=hashlib.sha256(invalid['legacyJson'].encode()).hexdigest()
        badPath.write_text(json.dumps(invalid));rejected([a.binary,'--stage-migration',badPath])
    assert not (root/'config/bwm-native-staged').exists()
    assert not list((root/'config').glob('.bwm-migration-*'))
    stage=json.loads(run([a.binary,'--stage-migration',proposalPath]))
    directory=Path(stage['directory'])
    assert (directory/'legacy.json').read_text()==legacy
    assert not list((root/'config').glob('.bwm-migration-*'))
    assert len({w['appletId'] for p in stage['panels'] for w in p['widgets']})==4
    verified=json.loads(run([a.binary,'--verify-stage',directory]))
    assert verified['status']=='verified-native-stage' and not verified['activationAllowed']
    runtimeProbe=json.loads(run([a.binary,'--probe-stage-runtime',directory]))
    assert len(runtimeProbe['panels'])==2 and not runtimeProbe['activationAllowed']
    assert all(p['status']=='output-unavailable' and not p['visible'] for p in runtimeProbe['panels'])
    report['stageRuntimeWithoutMatchingOutputs']=runtimeProbe
    nativePanel=json.loads(run([a.binary,'--probe-stage',directory]))
    assert nativePanel['status']=='original-panel-qml-passed'
    assert len(nativePanel['panels'])==2
    # Original LayoutManager may rewrite AppletOrder; verify it preserved the intended order.
    run([a.binary,'--verify-stage',directory])
    digest=hashlib.sha256((directory/'layout').read_bytes()).hexdigest()
    rejected([a.binary,'--stage-migration',proposalPath])
    assert hashlib.sha256((directory/'layout').read_bytes()).hexdigest()==digest
    (directory/'legacy.json').write_text(legacy+' ')
    rejected([a.binary,'--verify-stage',directory])
    (directory/'legacy.json').write_text(legacy)
    report['migration']=dict(status=verified['status'],activationAllowed=False,panels=verified['panels'],
        archivePreserved=True,enumSecondsMappedToAlways=True,missingPackageRejected=True,
        tamperedArchiveRejected=True,existingDestinationPreserved=True)
    report['originalPanel']=nativePanel
    # Durable test profile: complete native files, output bindings and independent
    # checkpoints. No live configuration or production activation is involved.
    profile=json.loads(run([a.binary,'--import-profile',directory]));profileRoot=Path(profile['directory'])
    assert not profile['activationAllowed'] and len(profile['panels'])==2
    initialLayout=Path(profile['layoutFile']).read_bytes();initialViews=Path(profile['viewSettingsFile']).read_bytes()
    assert initialLayout==(directory/'layout').read_bytes() and initialViews==(directory/'plasmashellrc').read_bytes()
    baseline=json.loads(run([a.binary,'--checkpoint-profile',profileRoot]));snapshot=Path(baseline['directory'])
    rejected([a.binary,'--import-profile',directory]);assert Path(profile['layoutFile']).read_bytes()==initialLayout
    wrapper=Path(__file__).with_name('preview-isolated.py')
    publisher=Path(__file__).resolve().parents[2]/'config/hypr/skins/plasma/scripts/panel-session.py'
    registry=root/'runtime/bwm-plasma-host-preview/active.json'
    for restart in range(2):
        logPath=root/'profile-wrapper.log'
        with logPath.open('w') as log:
            child=subprocess.Popen(['python3',str(wrapper),'--binary',str(a.binary),'--profile',str(profileRoot),'--follow-skin'],
                env=env,stdout=log,stderr=log,start_new_session=True)
            try:
                deadline=time.monotonic()+5
                while 'Prueba R4 registrada' not in logPath.read_text() and child.poll() is None and time.monotonic()<deadline:time.sleep(.01)
                assert registry.exists() and child.poll() is None,logPath.read_text()[-2000:]
                assert 'Prueba R4 registrada' in logPath.read_text()
                busy=subprocess.run([str(a.binary),'--checkpoint-profile',str(profileRoot)],env=env,capture_output=True,text=True,timeout=5)
                assert busy.returncode==7 and 'Another process owns' in busy.stderr
                run(['python3',publisher,'event','after','default','plasma'])
                registration=json.loads(registry.read_text());ack=json.loads((Path(registration['controlDirectory'])/'ack.json').read_text())
                assert len(ack['panels'])==2 and all(not p['visible'] for p in ack['panels'])
                run(['python3',publisher,'event','before','plasma','retro']);run(['python3',publisher,'stop'])
                assert child.wait(timeout=5)==0 and not registry.exists()
            finally:
                if child.poll() is None:
                    child.send_signal(signal.SIGINT)
                    try:child.wait(timeout=7)
                    except subprocess.TimeoutExpired:child.kill();child.wait()
    reopened=json.loads(run([a.binary,'--profile-info',profileRoot]))
    assert reopened['generation']==profile['generation'] and reopened['panels']==profile['panels']
    assert len(list((profileRoot/'snapshots').iterdir()))==3 # initial + two clean stops
    restored=json.loads(run([a.binary,'--restore-profile',snapshot]))
    assert restored['generation']!=profile['generation'] and Path(restored['layoutFile']).read_bytes()==initialLayout
    restored=json.loads(run([a.binary,'--restore-profile',str(snapshot)+os.sep]))
    assert Path(restored['layoutFile']).read_bytes()==initialLayout
    assert Path(profile['layoutFile']).exists() and Path(restored['viewSettingsFile']).read_bytes()==initialViews
    headBefore=(profileRoot/'head.json').read_bytes();savedSnapshot=(snapshot/'plasmashellrc').read_bytes()
    (snapshot/'plasmashellrc').write_bytes(savedSnapshot+b'\n[Foreign]\nTampered=1\n')
    rejected([a.binary,'--restore-profile',snapshot]);assert (profileRoot/'head.json').read_bytes()==headBefore
    (snapshot/'plasmashellrc').write_bytes(savedSnapshot)
    # Invalid bindings or a symlinked native file must not be accepted as a profile.
    bindingsPath=Path(restored['layoutFile']).parent/'bindings.json';originalBindings=bindingsPath.read_bytes()
    broken=json.loads(originalBindings);broken['panels'][0]['containmentId']=0
    bindingsPath.write_text(json.dumps(broken));rejected([a.binary,'--profile-info',profileRoot]);bindingsPath.write_bytes(originalBindings)
    viewsPath=Path(restored['viewSettingsFile']);viewsPath.unlink();viewsPath.symlink_to(directory/'plasmashellrc')
    rejected([a.binary,'--profile-info',profileRoot]);viewsPath.unlink();viewsPath.write_bytes(initialViews)
    run([a.binary,'--profile-info',profileRoot])
    report['persistentProfile']={'initial':profile,'baseline':baseline,'restored':restored,
        'wrapperRestarts':2,'nativeBytesPreserved':True,'bindingsPreserved':True,'autoCheckpointsOnCleanStop':2,
        'singleOwnerEnforced':True,'existingImportRejected':True,'tamperedSnapshotRejected':True,
        'invalidBindingsRejected':True,'symlinkNativeFileRejected':True,'oldGenerationRetained':True,'activationAllowed':False}
    # Exercise the persistent authority physically OUTSIDE /tmp, inside the
    # repository's permitted fixture area. Never use the real user's state home.
    fixtures=Path(__file__).resolve().parents[2]/'tests'
    with tempfile.TemporaryDirectory(prefix='bwm-r4-state-',dir=fixtures) as stateTmp:
        stateHome=Path(stateTmp).resolve();assert Path(tempfile.gettempdir()).resolve() not in stateHome.parents
        stateEnv=dict(env,XDG_STATE_HOME=str(stateHome))
        exported=json.loads(run(['python3',wrapper,'--binary',a.binary,'--profile',profileRoot,'--export-as','kept-profile'],stateEnv))
        assert not registry.exists() # export is metadata/storage only, with no preview registration
        persistent=Path(exported['directory']);assert exported['storage']=='xdg-state' and exported['copiedSnapshots']==3
        assert persistent==stateHome/'bwm/plasma/panel-profiles/kept-profile'
        assert Path(tempfile.gettempdir()).resolve() not in persistent.parents
        assert Path(exported['layoutFile']).read_bytes()==Path(restored['layoutFile']).read_bytes()
        assert Path(exported['viewSettingsFile']).read_bytes()==Path(restored['viewSettingsFile']).read_bytes()
        for sourceSnapshot in (profileRoot/'snapshots').iterdir():
            for file in sourceSnapshot.iterdir():assert (persistent/'snapshots'/sourceSnapshot.name/file.name).read_bytes()==file.read_bytes()
        rejected([a.binary,'--export-profile',profileRoot,'kept-profile'],stateEnv)
        rejected([a.binary,'--export-profile',profileRoot,'../escape'],stateEnv)
        rejected([a.binary,'--export-profile',profileRoot,'--catalog'],stateEnv)
        assert not (stateHome/'bwm/plasma/escape').exists()
        # Delete the entire temporary source; the exported archive and snapshot
        # data must suffice for another host, checkpoint and restore.
        shutil.rmtree(profileRoot)
        logPath=root/'state-profile-wrapper.log'
        with logPath.open('w') as log:
            child=subprocess.Popen(['python3',str(wrapper),'--binary',str(a.binary),'--profile',str(persistent),'--follow-skin'],
                env=stateEnv,stdout=log,stderr=log,start_new_session=True)
            try:
                deadline=time.monotonic()+5
                while 'Prueba R4 registrada' not in logPath.read_text() and child.poll() is None and time.monotonic()<deadline:time.sleep(.01)
                assert registry.exists() and child.poll() is None,logPath.read_text()[-2000:]
                assert 'Prueba R4 registrada' in logPath.read_text()
                run(['python3',publisher,'event','after','default','plasma'],stateEnv)
                busy=subprocess.run([str(a.binary),'--checkpoint-profile',str(persistent)],env=stateEnv,capture_output=True,text=True,timeout=5)
                assert busy.returncode==7 and 'Another process owns' in busy.stderr
                run(['python3',publisher,'stop'],stateEnv);assert child.wait(timeout=5)==0 and not registry.exists()
            finally:
                if child.poll() is None:
                    child.send_signal(signal.SIGINT)
                    try:child.wait(timeout=7)
                    except subprocess.TimeoutExpired:child.kill();child.wait()
        stateInfo=json.loads(run([a.binary,'--profile-info',persistent],stateEnv))
        assert stateInfo['storage']=='xdg-state' and stateInfo['panels']==profile['panels']
        stateRestored=json.loads(run([a.binary,'--restore-profile',persistent/'snapshots'/baseline['snapshot']],stateEnv))
        assert Path(stateRestored['layoutFile']).read_bytes()==initialLayout
        assert len(list((persistent/'snapshots').iterdir()))==4
        report['xdgStateProfile']={'export':exported,'readback':stateInfo,'restore':stateRestored,
            'outsideTmp':True,'temporarySourceRemoved':True,'snapshotHistoryPreserved':True,
            'wrapperReopenedAndCheckpointed':True,'exclusiveLeaseRetained':True,
            'existingNameRejected':True,'traversalRejected':True,'activationAllowed':False}
    shutil.rmtree(directory)
    # Exercise original LayoutManager order on both axes and preserve source bytes.
    orientationCases=[(edge,{'plasma':{'edge':edge,'widgets':['clock','clock']}},edge) for edge in ('top','bottom','left','right')]
    orientationCases += [('legacy-bottom',{'bottom':True,'plasma':{'edge':'','widgets':['clock','clock']}},'bottom'),
                         ('legacy-top',{'bottom':False,'plasma':{'widgets':['clock','clock']}},'top'),
                         ('schema-default',{'plasma':{'widgets':['clock','clock']}},'top')]
    oriented=[]
    for case,bar,expectedEdge in orientationCases:
        archived=json.dumps({'bar':bar,'foreign':{'preserve':42}})+'\n'
        plan=migration.proposal(archived,['MSI fixture','LG fixture'])
        if case=='schema-default':
            # Old proposals did not include edge. Native staging still derives it
            # from the authenticated source, rather than reverting to hardcoded bottom.
            for panel in plan['panels']:panel.pop('edge')
        proposalPath.write_text(json.dumps(plan))
        staged=json.loads(run([a.binary,'--stage-migration',proposalPath]));directory=Path(staged['directory'])
        verified=json.loads(run([a.binary,'--verify-stage',directory]))
        assert verified['orientationContractVersion']==1
        assert all(panel['edge']==expectedEdge for panel in verified['panels'])
        probe=json.loads(run([a.binary,'--probe-stage',directory]))
        expectedAxis='y' if expectedEdge in ('left','right') else 'x'
        assert all(panel['orderAxis']==expectedAxis and all(w['ordered'] for w in panel['widgets']) for panel in probe['panels'])
        assert all(a['location']==b['location'] and a['formFactor']==b['formFactor'] for a,b in zip(probe['panels'],verified['panels']))
        run([a.binary,'--verify-stage',directory])
        assert (directory/'legacy.json').read_text()==archived
        originalReport=(directory/'report.json').read_text()
        incomplete=json.loads(originalReport);incomplete['panels'][0].pop('edge')
        (directory/'report.json').write_text(json.dumps(incomplete));rejected([a.binary,'--verify-stage',directory])
        (directory/'report.json').write_text(originalReport)
        if case=='bottom':
            oldReport=json.loads(originalReport);oldReport.pop('orientationContractVersion')
            for panel in oldReport['panels']:
                for field in ('edge','location','formFactor'):panel.pop(field)
            (directory/'report.json').write_text(json.dumps(oldReport))
            run([a.binary,'--verify-stage',directory])
            (directory/'report.json').write_text(originalReport)
        oriented.append({'case':case,'edge':expectedEdge,'readback':verified,'originalPanel':probe,'archivePreserved':True})
        shutil.rmtree(directory)
    report['orientationMigration']={'cases':oriented,'inconsistentProposalRejected':True,'invalidSourceRejected':True,
        'missingOrientationReportRejected':True,'oldBottomReportReadable':True,'activationAllowed':False}
    # Three native preferences in a separate plasmashellrc staging artifact. Never
    # use/replace the active file; exercise the original frame reading that artifact.
    livePath=root/'config/plasmashellrc'
    rootPreferences=livePath.read_bytes() if livePath.exists() else None
    for key,value in (('thickness',True),('thickness',38.5),('thickness','44'),('floating','false'),('style','unknown')):
        invalid=migration.proposal(json.dumps({'bar':{'plasma':{'widgets':['clock']}}}),['MSI fixture'])
        archived=json.dumps({'bar':{'plasma':{'widgets':['clock'],key:value}}})
        invalid['legacyJson']=archived;invalid['sourceSha256']=hashlib.sha256(archived.encode()).hexdigest()
        badPath.write_text(json.dumps(invalid));rejected([a.binary,'--stage-migration',badPath])
        assert not (root/'config/bwm-native-staged').exists()
    viewCases=[('horizontal-opaque',{'edge':'bottom','style':'opaque','thickness':38}),
               ('vertical-translucent',{'edge':'left','style':'translucent','thickness':60}),
               ('floating-opaque',{'edge':'top','style':'opaque','floating':True,'thickness':40}),
               ('clamp-low',{'style':'translucent','thickness':-10}),
               ('zero-default',{'style':'translucent','thickness':0}),
               ('clamp-high',{'style':'translucent','thickness':300}),
               ('legacy-floating',{'edge':'right','style':'floating','thickness':44}),
               ('adaptive',{'style':'adaptive','thickness':42})]
    migratedViews=[]
    for case,preferences in viewCases:
        source=dict(preferences,widgets=['clock','clock'],length=0.65,alignment='center',
                    visibility='autoHide',floatingGap=12,opacity=0.37,vendor={'preserved':42})
        archived=json.dumps({'bar':{'plasma':source},'foreign':{'keep':13}})+'\n'
        plan=migration.proposal(archived,['MSI fixture','LG fixture'])
        if case=='horizontal-opaque':
            forged=json.loads(json.dumps(plan));forged['panels'][0]['nativeViewSettings']['thickness']=90
            badPath.write_text(json.dumps(forged));rejected([a.binary,'--stage-migration',badPath])
            assert not (root/'config/bwm-native-staged').exists()
            # Older proposals are derived from the authenticated archive as well.
            for panel in plan['panels']:panel.pop('nativeViewSettings')
        proposalPath.write_text(json.dumps(plan))
        staged=json.loads(run([a.binary,'--stage-migration',proposalPath]));directory=Path(staged['directory'])
        nativePath=directory/'plasmashellrc';nativeBytes=nativePath.read_bytes()
        verified=json.loads(run([a.binary,'--verify-stage',directory]))
        assert verified['viewSettingsContractVersion']==1 and verified['viewSettingsFile']=='plasmashellrc'
        expected=migration.native_view_settings(source)
        assert all(p['nativeViewSettings']==expected and not p['viewRuntimeVerified'] for p in verified['panels'])
        assert all({'visibility','alignment','length','floatingGap','opacity'} <= {e['legacyKey'] for e in p['deferredViewSettings']} for p in verified['panels'])
        if expected['panelOpacity']==0:
            frame={'rejected':True,'reason':rejected([a.binary,'--probe-stage-frame',directory])}
            assert 'Adaptive' in frame['reason']
            assert nativePath.read_bytes()==nativeBytes
        else:
            frame=json.loads(run([a.binary,'--probe-stage-frame',directory]))
            assert frame['status']=='original-panel-frame-passed'
            assert all(p['nativeFrameLoaded'] and p['effectiveThickness']>=expected['thickness'] for p in frame['panels'])
            assert all(p['nativeViewSettings']['panelOpacity']==expected['panelOpacity'] and p['nativeViewSettings']['floating']==expected['floating'] for p in frame['panels'])
            assert all(abs(p['floatingness']-expected['floating'])<0.01 for p in frame['panels'])
            assert all(p['isOpaque']==(expected['panelOpacity']==1) for p in frame['panels'])
            assert nativePath.read_bytes()==nativeBytes
        run([a.binary,'--verify-stage',directory])
        assert (directory/'legacy.json').read_text()==archived
        if case=='horizontal-opaque':
            # Changed values and missing contracts must not masquerade as verified data.
            nativePath.write_bytes(nativeBytes.replace(b'thickness=38',b'thickness=39'))
            rejected([a.binary,'--verify-stage',directory]);nativePath.write_bytes(nativeBytes)
            originalReport=(directory/'report.json').read_text()
            for edit in ('view','deferred','contract'):
                changed=json.loads(originalReport)
                if edit=='view':changed['panels'][0]['nativeViewSettings']['thickness']=39
                elif edit=='deferred':changed['panels'][0]['deferredViewSettings']=[]
                else:changed.pop('viewSettingsContractVersion')
                (directory/'report.json').write_text(json.dumps(changed));rejected([a.binary,'--verify-stage',directory])
            (directory/'report.json').write_text(originalReport)
            nativePath.unlink();rejected([a.binary,'--verify-stage',directory]);nativePath.write_bytes(nativeBytes)
            nativePath.write_bytes(nativeBytes+b'\n[ForeignVendor]\nKeep=42\n')
            run([a.binary,'--verify-stage',directory]);assert b'Keep=42' in nativePath.read_bytes()
            nativePath.write_bytes(nativeBytes)
            # True old stages without a view artifact still verify; a frame probe
            # cannot then pretend it has read back migrated view preferences.
            old=json.loads(originalReport);old.pop('viewSettingsContractVersion');old.pop('viewSettingsFile')
            for panel in old['panels']:
                for key in ('nativeViewSettings','deferredViewSettings','viewRuntimeVerified'):panel.pop(key)
            (directory/'report.json').write_text(json.dumps(old));nativePath.unlink()
            run([a.binary,'--verify-stage',directory]);rejected([a.binary,'--probe-stage-frame',directory])
            nativePath.write_bytes(nativeBytes);(directory/'report.json').write_text(originalReport)
        migratedViews.append({'case':case,'nativeReadback':verified,'frame':frame,'archivePreserved':True})
        shutil.rmtree(directory)
        assert (livePath.read_bytes() if livePath.exists() else None)==rootPreferences
        assert not list((root/'config').glob('.bwm-migration-*'))
    report['viewSettingsMigration']={'cases':migratedViews,'activationAllowed':False,'isolatedRootPreferencesUnchanged':True,
        'forgedProposalRejected':True,'invalidArchivedTypesRejected':True,'tamperedNativeFileRejected':True,'missingArtifactRejected':True,
        'tamperedReportRejected':True,'deferredCapabilitiesVerified':True,'oldStageReadbackPreserved':True}
    # Fixture only: never read or migrate the live panel's configuration in a test.
    completeLegacy=json.dumps({'bar':{'plasma':{
        'widgets':['kickoff','tasks','tray','clock','desktop'],
        'kickoff':{'icon':'start-here-kde-symbolic','favorites':['preferred://browser'],
                   'favoritesPortedToKAstats':True,'compactMode':True},
        'taskManager':{'iconSpacing':2,'showOnlyCurrentDesktop':True},
        'clock':{'dateFormat':'custom','customDateFormat':'yyyy-MM-dd'},
        'showDate':False,'showSeconds':False,'foreign':{'keep':42}}}})+'\n'
    completePlan=migration.proposal(completeLegacy,['MSI fixture','LG fixture'])
    proposalPath.write_text(json.dumps(completePlan))
    complete=json.loads(run([a.binary,'--stage-migration',proposalPath]))
    completeVerified=json.loads(run([a.binary,'--verify-stage',complete['directory']]))
    assert all(len(p['widgets'])==5 for p in completeVerified['panels'])
    assert len({w['appletId'] for p in completeVerified['panels'] for w in p['widgets']})==10
    assert (Path(complete['directory'])/'legacy.json').read_text()==completeLegacy
    report['fullPanelDataMigration']=dict(status=completeVerified['status'],panels=completeVerified['panels'],
        activationAllowed=False,runtimeVerified=False,favoritesImportDeferred=True)
    a.report.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    print('3 packages: native install/remove and representations; 2 config transactions and fresh-process readback passed' + ('; 2 native UI suites passed' if a.ui_test else ''))
