#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Exercise native KDE application startup using only a disposable recording application."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

ROOT=Path(__file__).resolve().parents[2]
SKIN=ROOT/'config/hypr/skins/plasma/scripts'
spec=importlib.util.spec_from_file_location('launch_context',SKIN/'native_launch.py')
context=importlib.util.module_from_spec(spec);spec.loader.exec_module(context)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary',type=Path,required=True);parser.add_argument('--sycoca',type=Path,required=True)
    parser.add_argument('--report',type=Path,required=True);args=parser.parse_args()
    report={'version':1,'sessionModified':False,'userApplicationsLaunched':False,'applicationReadinessVerified':False}
    try:
        with tempfile.TemporaryDirectory(prefix='bwm-r4-task-launch-') as temporary:
            root=Path(temporary)
            for name in ('config','data','cache','runtime','defaults','preview-config','preview-data','preview-cache'):(root/name).mkdir(mode=0o700)
            (root/'config/illogical-impulse').mkdir();(root/'config/illogical-impulse/config.json').write_text('{"appearance":{"bwmTheme":"plasma"}}')
            original=dict(os.environ,QT_QPA_PLATFORM='offscreen',XDG_CONFIG_HOME=str(root/'config'),XDG_DATA_HOME=str(root/'data'),
                XDG_CACHE_HOME=str(root/'cache'),XDG_RUNTIME_DIR=str(root/'runtime'),XDG_CONFIG_DIRS=str(root/'defaults'),
                XDG_DATA_DIRS='/usr/local/share:/usr/share',DBUS_SESSION_BUS_ADDRESS='unix:path='+str(root/'no-bus'))
            for key in tuple(original):
                if key in ('DISPLAY','WAYLAND_DISPLAY','WAYLAND_SOCKET','HYPRLAND_INSTANCE_SIGNATURE','KDESYCOCA') or key.startswith('BWM_R4_'):original.pop(key,None)
            appid='org.bwm.r4.launch.fixture';applications=root/'data/applications';applications.mkdir()
            log=root/'record.json';program=root/'record.py'
            program.write_text('import json,os,sys,time\nfrom pathlib import Path\n'
                +'Path(sys.argv[1]).write_text(json.dumps({"args":sys.argv[2:],"pid":os.getpid(),"session":os.getsid(0),'
                +'"config":os.environ.get("XDG_CONFIG_HOME"),"data":os.environ.get("XDG_DATA_HOME"),"cache":os.environ.get("XDG_CACHE_HOME"),'
                +'"dbus":os.environ.get("DBUS_SESSION_BUS_ADDRESS"),"nativeFlagsInherited":any(k.startswith("BWM_R4_") for k in os.environ),'
                +'"skinSwitchInherited":"BWM_SKIN_SWITCH" in os.environ}))\n'
                +'print("Own fixture stdout",flush=True)\nprint("Own fixture stderr",file=sys.stderr,flush=True)\n'
                +'if len(sys.argv)==2:\n deadline=time.monotonic()+6\n while not Path(sys.argv[1]+".release").exists() and time.monotonic()<deadline:time.sleep(.02)\n')
            desktop=applications/(appid+'.desktop')
            def entry(extra=''):
                desktop.write_text('[Desktop Entry]\nType=Application\nName=BWM launch recording fixture\nExec='+sys.executable+' '+str(program)+' '+str(log)+' %U\nStartupNotify=false\nX-KDE-Protocols=file,https\n'+extra)
                reply=subprocess.run([str(args.sycoca),'--noincremental'],env=original,capture_output=True,text=True,timeout=10)
                assert reply.returncode==0,reply.stderr[-1500:]
            entry()
            # The real action helper validates a real process generation against fake IPC.
            current=os.getpid();generation=Path(f'/proc/{current}/stat').read_text().rpartition(')')[2].split()[19]
            clients=root/'clients.json';clients.write_text(json.dumps([{'address':'0xabc','pid':current,'class':appid,'mapped':True,'workspace':{'id':1,'name':'1'},'tags':[]}]))
            fake=root/'bin';fake.mkdir();hyprctl=fake/'hyprctl'
            hyprctl.write_text('#!'+sys.executable+'\nimport sys\nfrom pathlib import Path\n'
                +'assert sys.argv[1:]==["-j","clients"]\nprint(Path('+repr(str(clients))+').read_text())\n');hyprctl.chmod(0o700)
            (root/'preview-defaults').mkdir(mode=0o700);context.write_host_policy(root/'preview-defaults')
            helper_env=dict(original,XDG_DATA_HOME=str(root/'preview-data'),XDG_CACHE_HOME=str(root/'preview-cache'),
                XDG_CONFIG_DIRS=str(root/'preview-defaults'),
                DBUS_SESSION_BUS_ADDRESS='unix:path='+str(root/'preview-no-bus'),BWM_R4_TASK_ACTIONS='1',BWM_SKIN_SWITCH='1',
                PATH=str(fake)+os.pathsep+original.get('PATH',''))
            helper_env[context.VARIABLE]=context.capture(original)
            def action(kind,urls=(),gen=generation):
                log.unlink(missing_ok=True)
                request={'version':1,'action':kind,'address':'0xabc','pid':current,'generation':gen}
                if kind=='open-urls':request['urls']=list(urls)
                reply=subprocess.run([sys.executable,str(SKIN/'native-tasks.py'),'action','--launcher',str(args.binary.resolve())],
                    input=json.dumps(request),env=helper_env,cwd=root,capture_output=True,text=True,timeout=8)
                return reply
            def recording(reply):
                assert reply.returncode==0,(reply.stdout,reply.stderr)
                assert json.loads(reply.stdout)=={'version':1,'accepted':True}
                end=time.monotonic()+3
                while not log.exists() and time.monotonic()<end:time.sleep(.01)
                packet=json.loads(log.read_text())
                for name in ('config','data','cache'):assert packet[name]==str(root/name),packet
                assert packet['dbus']==original['DBUS_SESSION_BUS_ADDRESS']
                assert packet['nativeFlagsInherited'] is False and packet['skinSwitchInherited'] is False
                assert packet['session']!=os.getsid(0)
                return packet
            first=recording(action('new-instance'));assert first['args']==[]
            os.kill(first['pid'],0);Path(str(log)+'.release').write_text('release own fixture')
            report['launchReturnsBeforeApplicationExits']=True
            filename=root/'file with spaces; $(touch unexpected) ñ.txt';filename.write_text('Own fixture')
            urls=[filename.as_uri(),'https://example.invalid/document?a=one%20two&x=%24HOME']
            second=recording(action('open-urls',urls));assert second['args']==[str(filename),urls[1].replace('%20',' ')],second
            assert not (root/'unexpected').exists()
            report['newInstanceAccepted']=True;report['nativeUrlExpansionVerified']=True
            report['callerEnvironmentRestored']=True;report['launchOutsideActionProcessGroup']=True
            for kind,urls_,gen in [('open-urls',[] ,generation),('new-instance',[], 'stale')]:
                reply=action(kind,urls_,gen);assert reply.returncode!=0 and not log.exists()
            report['staleIdentityAndEmptyUrlsRejected']=True
            # Pinned launchers and .desktop Actions carry no window identity: the
            # host names the launcher URL (and Action) only; the helper resolves it
            # again with the restored caller environment.
            def launch(kind,url,**extra):
                log.unlink(missing_ok=True)
                request={'version':1,'action':kind,'launcherUrl':url,**extra}
                return subprocess.run([sys.executable,str(SKIN/'native-tasks.py'),'action','--launcher',str(args.binary.resolve())],
                    input=json.dumps(request),env=helper_env,cwd=root,capture_output=True,text=True,timeout=8)
            def rejected(reply):
                time.sleep(.3);return reply.returncode!=0 and not log.exists()
            actions=('Actions=compose;hidden;separator-before;\n[Desktop Action compose]\nName=Compose && send\n'
                +'Exec='+sys.executable+' '+str(program)+' '+str(log)+' --compose\n'
                +'[Desktop Action hidden]\nName=Hidden fixture action\nNoDisplay=true\nExec='+sys.executable+' '+str(program)+' '+str(log)+' --hidden\n'
                +'[Desktop Action separator-before]\nName=After separator\nExec='+sys.executable+' '+str(program)+' '+str(log)+' --after\n')
            entry(actions)
            packet=recording(launch('launcher','applications:'+appid+'.desktop',urls=[]));assert packet['args']==[],packet
            packet=recording(launch('launcher',desktop.as_uri(),urls=[filename.as_uri()]));assert packet['args']==[str(filename)],packet
            (root/'config/kdeglobals').write_text('[General]\nTerminalApplication='+appid+'.desktop\n')
            packet=recording(launch('launcher','preferred://terminal',urls=[]));assert packet['args']==[],packet
            (root/'config/kdeglobals').unlink()
            report['pinnedLauncherApplicationsFileAndPreferredUrlsVerified']=True
            packet=recording(launch('service-action','applications:'+appid+'.desktop',serviceAction='compose'));assert packet['args']==['--compose'],packet
            packet=recording(launch('service-action',desktop.as_uri(),serviceAction='separator-before'));assert packet['args']==['--after'],packet
            report['desktopServiceActionsVerified']=True
            for reply in (launch('service-action','applications:'+appid+'.desktop',serviceAction='hidden'),
                          launch('service-action','applications:'+appid+'.desktop',serviceAction='missing'),
                          launch('service-action','applications:'+appid+'.desktop',serviceAction='compose',urls=[]),
                          launch('service-action','applications:'+appid+'.desktop',serviceAction='../compose'),
                          launch('launcher','https://example.invalid/app',urls=[]),
                          launch('launcher','applications:'+appid+'.desktop',urls=[],pid=current),
                          launch('launcher','applications:missing.bwm.fixture.desktop',urls=[]),
                          launch('launcher','preferred://terminal',urls=[])): # no configured terminal, no fallback installed
                assert rejected(reply),(reply.stdout,reply.stderr)
            report['hiddenUnknownAndMalformedLauncherRequestsRejected']=True
            # The disposable host itself is denied by KDE KIOSK even for a valid
            # request: only the restored caller environment may start the job.
            denied=subprocess.run([str(args.binary.resolve()),'--launch-task-application'],
                input=json.dumps({'version':1,'action':'launcher','launcherUrl':'applications:'+appid+'.desktop','urls':[]}),
                env=dict(original,XDG_CONFIG_DIRS=str(root/'preview-defaults')),capture_output=True,text=True,timeout=6)
            time.sleep(.3)
            assert denied.returncode==2 and json.loads(denied.stdout)=={'version':1,'accepted':False,'reason':'native-launch-job-rejected'},denied.stdout
            assert not log.exists()
            report['hostKioskPolicyDeniesInProcessLaunch']=True
            entry()
            for key in ('SingleMainWindow=true\n','X-GNOME-SingleWindow=true\n','NoDisplay=true\n','Actions=new-window;\n[Desktop Action new-window]\nName=Native new window\nExec=/usr/bin/false\n'):
                entry(key);packet=recording(action('new-instance'));assert packet['args']==[],key
            report['nativeMenuVisibilityPolicyDoesNotBlockExplicitRequests']=True
            desktop.unlink();subprocess.run([str(args.sycoca),'--noincremental'],env=original,capture_output=True,text=True,timeout=10,check=True)
            reply=action('new-instance');assert reply.returncode!=0 and not log.exists()
            report['unregisteredExecutableFallbackRejected']=True
            # CLI input is bounded and cannot create views/captures on malformed input.
            reply=subprocess.run([str(args.binary.resolve()),'--launch-task-application'],input='{}',env=original,capture_output=True,text=True,timeout=6)
            assert reply.returncode==2 and json.loads(reply.stdout)['accepted'] is False
            report.update(passed=True,originalKdeApplicationLauncherJobVerified=True)
    except (OSError,ValueError,AssertionError,subprocess.SubprocessError) as error:report.update(passed=False,error=str(error))
    args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2));return 0 if report.get('passed') else 1
if __name__=='__main__':raise SystemExit(main())
