#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Original KDE desktop-provider regression against a private data-only Wayland fixture."""
import argparse
import json
import os
from pathlib import Path
import select
import socket
import subprocess
import tempfile
import sys

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--fixture',type=Path,required=True);p.add_argument('--client',type=Path,required=True)
p.add_argument('--report',type=Path,required=True)
p.add_argument('--arbitrated',action='store_true',help='Select the original KDE consumer test for the server arbitration fixture')
p.add_argument('--memory-render',action='store_true',help='Run the task delegate memory-render test; never session/surface acceptance')
p.add_argument('--thumbnails',action='store_true',help='Run synthetic window-capture fixture with private fake IPC')
a=p.parse_args()
report={'version':1,'sessionModified':False,'hyprlandPluginLoaded':False,'dailyPanelReplaced':False,'renderingVerified':False,'arbitratedProvider':a.arbitrated}
if a.memory_render:report.update(memoryRenderingRequested=True,memoryRenderingVerified=False)
if a.thumbnails:report.update(syntheticWindowCaptureRequested=True,syntheticWindowCaptureVerified=False)
try:
    with tempfile.TemporaryDirectory(prefix='bwm-r4-desktop-protocol-') as tmp:
        root=Path(tmp)
        for name in ('runtime','config','data','cache','defaults'):(root/name).mkdir(mode=0o700)
        env=dict(os.environ,XDG_RUNTIME_DIR=str(root/'runtime'),XDG_CONFIG_HOME=str(root/'config'),
            XDG_DATA_HOME=str(root/'data'),XDG_CACHE_HOME=str(root/'cache'),XDG_CONFIG_DIRS=str(root/'defaults'),
            XDG_DATA_DIRS='/usr/local/share:/usr/share',QT_QPA_PLATFORM='wayland',QT_QUICK_BACKEND='software',
            DBUS_SESSION_BUS_ADDRESS='unix:path='+str(root/'no-bus'),QT_WAYLAND_DISABLE_WINDOWDECORATION='1',
            BWM_R4_DESKTOP_TEST_ROOT=str(root))
        for name in ('DISPLAY','WAYLAND_DISPLAY','WAYLAND_SOCKET','HYPRLAND_INSTANCE_SIGNATURE','QT_WAYLAND_SHELL_INTEGRATION','KDESYCOCA',
                     'BWM_R4_DESKTOP_ACTIONS','BWM_R4_DESKTOP_RUNTIME','BWM_R4_DESKTOP_CONFIG',
                     'BWM_R4_TASK_ACTIONS','BWM_R4_TASK_RUNTIME','BWM_R4_TASK_CONFIG','BWM_R4_NATIVE_DESKTOPS','BWM_R4_ARBITRATED_FIXTURE'):env.pop(name,None)
        if a.arbitrated:env['BWM_R4_ARBITRATED_FIXTURE']='1'
        if a.thumbnails:
            fake=root/'fake-bin';fake.mkdir()
            payload=(Path(__file__).parent/'tests/desktop-hyprctl.py').read_text().split('\n',1)[1]
            executable=fake/'hyprctl';executable.write_text('#!'+sys.executable+'\n'+payload);executable.chmod(0o700)
            clients=root/'fake-clients.json';clients.write_text(json.dumps({'address':'0xabc','pid':os.getpid(),
                'workspace':{'id':1,'name':'1'},'mapped':True,'floating':False,'hidden':False,'tags':[],
                'at':[0,0],'size':[64,48],'monitor':0,'class':'org.bwm.thumbnail.fixture','title':'Own synthetic pixels'}))
            (root/'config/illogical-impulse').mkdir();(root/'config/illogical-impulse/config.json').write_text('{"appearance":{"bwmTheme":"plasma"}}')
            env.update(BWM_R4_FAKE_CLIENTS=str(clients),BWM_R4_FAKE_ACTIONS=str(root/'fake-actions.log'),
                PATH=str(fake)+os.pathsep+os.environ.get('PATH',''))
            helper=Path(__file__).resolve().parents[2]/'config/hypr/skins/plasma/scripts/native-tasks.py'
            prepared=subprocess.run([sys.executable,str(helper),'snapshot'],env=env,capture_output=True,text=True,timeout=5)
            if prepared.returncode or len(json.loads(prepared.stdout).get('windows',[]))!=1:raise ValueError('Synthetic thumbnail task source unavailable')
            report['syntheticTaskSourcePrepared']=True
        # Explicit inherited endpoints: no listening socket or connection to a
        # session compositor. Qt's supported WAYLAND_SOCKET consumes our endpoint.
        server,client=socket.socketpair();server2,client2=socket.socketpair()
        with subprocess.Popen([str(a.fixture),str(server.fileno()),str(server2.fileno())],env=env,pass_fds=(server.fileno(),server2.fileno()),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True) as fixture:
            server.close();server2.close()
            try:
                if not select.select([fixture.stdout],[],[],5)[0]:raise TimeoutError('Fixture did not publish its private display')
                if fixture.stdout.readline().strip()!='ready':
                    fixture.wait(timeout=3)
                    raise ValueError(f'Invalid fixture handshake (exit {fixture.returncode}): '+fixture.stderr.read()[-2000:])
                env.update(WAYLAND_SOCKET=str(client.fileno()),BWM_R4_SECOND_CLIENT_FD=str(client2.fileno()),BWM_R4_DESKTOP_TEST_FD=str(fixture.stdin.fileno()),BWM_R4_FIXTURE_NOTIFY_FD=str(fixture.stdout.fileno()))
                arguments=[str(a.client)]+(['nativeActivationRequiresObservedAbsoluteState','sharedCountMirrorUpdatesOriginalKde','arbitratedProviderFeedsOriginalKdeAndWithdraws'] if a.arbitrated else [])
                result=subprocess.run(arguments,env=env,pass_fds=(fixture.stdin.fileno(),fixture.stdout.fileno(),client.fileno(),client2.fileno()),capture_output=True,text=True,timeout=40)
                client.close();client2.close()
                report.update(clientExit=result.returncode,clientOutput=result.stdout,clientDiagnostics=result.stderr)
                fixture.stdin.close();fixture.wait(timeout=5)
                report['fixtureExit']=fixture.returncode;report['fixtureDiagnostics']=fixture.stderr.read()
                report['fixtureOutput']=fixture.stdout.read()
                if result.returncode or fixture.returncode:raise RuntimeError('Native desktop protocol regression failed')
            finally:
                client.close();client2.close()
                if fixture.poll() is None:fixture.kill();fixture.wait(timeout=3)
        report.update(passed=True,cleanupVerified=True)
        if a.memory_render:report['memoryRenderingVerified']=True
        if a.thumbnails:report['syntheticWindowCaptureVerified']=True
except (OSError,ValueError,TimeoutError,RuntimeError,subprocess.SubprocessError) as error:
    report.update(passed=False,error=str(error))
a.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2));raise SystemExit(0 if report['passed'] else 1)
