#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Bounded IPC adapter for the host's native TaskManager source. No daemon or settings."""
import argparse
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys

SCRIPTS=Path(__file__).resolve().parents[3]/'scripts'
sys.path.insert(0,str(SCRIPTS))
import bwm_windows
spec=importlib.util.spec_from_file_location('native_task_manager',Path(__file__).with_name('kwin-window.py'))
manager=importlib.util.module_from_spec(spec);spec.loader.exec_module(manager)
minimizer=manager.minimizer()
launch_spec=importlib.util.spec_from_file_location('bwm_native_launch',Path(__file__).with_name('native_launch.py'))
launch_context=importlib.util.module_from_spec(launch_spec);launch_spec.loader.exec_module(launch_context)


def query(name):
    reply=subprocess.run(['hyprctl','-j',name],capture_output=True,text=True,timeout=2,check=True)
    return json.loads(reply.stdout)


def identity(client):
    address=client.get('address');pid=client.get('pid')
    if not isinstance(address,str) or not re.fullmatch(r'0x[0-9a-fA-F]+',address) or type(pid) is not int or pid<=0:
        return None
    generation=bwm_windows.process_generation(pid)
    return (address,pid,generation) if generation else None


def workspace(client):
    space=client.get('workspace',{})
    if not isinstance(space,dict):return None
    if minimizer.is_minimized(client):return minimizer.origin_workspace(client)
    number=space.get('id');name=space.get('name','')
    if type(number) is int and number>0 and number!=99:return number
    if type(number) is int and number<0 and isinstance(name,str) and name.startswith('special:'):return name
    return None


def record(client,active,monitors):
    ident=identity(client);origin=workspace(client)
    if not ident or origin is None or client.get('mapped') is not True:return None
    minimized=minimizer.is_minimized(client)
    visible_specials={m.get('specialWorkspace',{}).get('id') for m in monitors if isinstance(m,dict)}
    if isinstance(origin,str) and not minimized and client.get('workspace',{}).get('id') not in visible_specials:return None
    if client.get('hidden') and not minimized:return None
    at=client.get('at');size=client.get('size')
    if not all(isinstance(x,list) and len(x)==2 and all(type(n) in (int,float) and math.isfinite(n) for n in x) for x in (at,size)) or min(size)<=0:return None
    address,pid,generation=ident
    monitor=next((m for m in monitors if m.get('id')==client.get('monitor')),None)
    screen=list(bwm_windows.monitor_box(monitor)) if monitor else []
    return {'address':address,'pid':pid,'generation':generation,'title':str(client.get('title',''))[:4096],
            'appId':str(client.get('class',''))[:512],'workspace':str(origin),'geometry':at+size,'screen':screen,
            'active':active.get('address')==address and active.get('pid')==pid,
            'minimized':minimized,'maximized':manager.mode_from_tags(client.get('tags',[]))==manager.FULL or client.get('fullscreen',0)==1,
            'onAllDesktops':isinstance(origin,int) and bool(client.get('pinned',False)),
            'fullscreen':bool(client.get('fullscreen',0)&2),'fullscreenable':manager.native_fullscreen_allowed(client,minimized=minimized),
            # Optional v1 fields (absent = unsupported): common manager move/resize and tags.
            'movable':manager.native_fullscreen_allowed(client,minimized=minimized) and client.get('floating') is True and not client.get('fullscreen',0),
            'windowTagsSettable':manager.native_fullscreen_allowed(client,minimized=minimized),
            'noBorder':manager.has_tag(client,manager.TAG_NO_BORDER),'excludedFromCapture':manager.has_tag(client,manager.TAG_NO_CAPTURE),
            'urgent':bool(client.get('urgent',False))}


def snapshot():
    clients=query('clients');active=query('activewindow');monitors=query('monitors')
    if not isinstance(clients,list) or not isinstance(active,dict) or not isinstance(monitors,list):raise ValueError('Invalid task IPC data')
    rows=[];seen=set()
    # Hyprland 0.56.2 serializes WindowState::windows() bottom-to-top in
    # clientsRequest. Preserve that order, not focusHistoryID (which is MRU).
    for stacking_order,client in enumerate(clients):
        if not isinstance(client,dict):raise ValueError('Invalid task client')
        row=record(client,active,monitors)
        if row:
            if row['address'] in seen:raise ValueError('Duplicate task identity')
            row['stackingOrder']=stacking_order
            seen.add(row['address']);rows.append(row)
    return {'version':1,'windows':rows}


def valid_urls(urls):
    return (isinstance(urls,list) and len(urls)<=128
            and all(isinstance(url,str) and url and len(url)<=4096 and '\0' not in url for url in urls)
            and sum(len(url) for url in urls)<=60000)


def hand_off(launcher, payload):
    # Keep the launching process outside the action helper's kill group. Its
    # own bounded KIO job finishes startup; deleting a job never closes apps.
    reply=subprocess.run([launcher,'--launch-task-application'],input=json.dumps(payload),
        env=launch_context.restore(os.environ),capture_output=True,text=True,timeout=4.5,start_new_session=True)
    result=json.loads(reply.stdout)
    if (reply.returncode or not isinstance(result,dict) or type(result.get('version')) is not int
            or result['version']!=1 or result.get('accepted') is not True or result.get('launchHandedOff') is not True):
        raise ValueError('Native application launch rejected')
    return {'version':1,'accepted':True} # KIO accepted startup, not application readiness.


def check_launcher(launcher):
    if not launcher or not Path(launcher).is_absolute() or not os.access(launcher, os.X_OK):
        raise ValueError('Native application launcher unavailable')


def launch_application(request, launcher):
    check_launcher(launcher)
    urls=request.get('urls', [])
    if (not valid_urls(urls) or (request['action']=='new-instance' and urls)
            or (request['action']=='open-urls' and not urls)):
        raise ValueError('Invalid launch URLs')
    from native_guard import action_lock,require_breeze
    with action_lock():
        require_breeze()
        expected=(request.get('address'),request.get('pid'),request.get('generation'))
        clients=query('clients')
        if not isinstance(clients,list):raise ValueError('Invalid client snapshot')
        matches=[client for client in clients if isinstance(client,dict) and identity(client)==expected
                 and client.get('mapped') is True and workspace(client) is not None]
        if len(matches)!=1:raise ValueError('Task vanished or identity changed')
        client=matches[0]
        return hand_off(launcher,{'version':1,'action':request['action'],'appId':client.get('class'),'pid':client['pid'],'urls':urls})


LAUNCHER_SCHEMES=('applications:','preferred:','file:')
ACTION_NAME=re.compile(r'[A-Za-z0-9-]{1,256}')


def launch_launcher(request, launcher):
    """Pinned launcher (no window) or a .desktop Action from KDE's task menu.

    The host only names the launcher URL (and Action); the native helper resolves
    the service again with the caller's restored environment and starts KDE's own
    KIO::ApplicationLauncherJob. No window identity exists to revalidate.
    """
    check_launcher(launcher)
    url=request.get('launcherUrl')
    if (not isinstance(url,str) or not url or len(url)>4096 or '\0' in url
            or not url.startswith(LAUNCHER_SCHEMES)):
        raise ValueError('Invalid launcher URL')
    payload={'version':1,'action':request['action'],'launcherUrl':url}
    if request['action']=='launcher':
        urls=request.get('urls',[])
        if not valid_urls(urls) or set(request)-{'version','action','launcherUrl','urls'}:raise ValueError('Invalid launcher request')
        payload['urls']=urls
    else:
        name=request.get('serviceAction')
        if (not isinstance(name,str) or not ACTION_NAME.fullmatch(name)
                or set(request)-{'version','action','launcherUrl','serviceAction'}):
            raise ValueError('Invalid service action request')
        payload['serviceAction']=name
    from native_guard import action_lock,require_breeze
    with action_lock():
        require_breeze()
        return hand_off(launcher,payload)


def action(request,launcher=None):
    if not isinstance(request,dict) or type(request.get('version')) is not int or request.get('version')!=1 or request.get('action') not in ('focus','toggle-minimize','maximize','close','fullscreen','new-instance','open-urls','launcher','service-action',
                                                                                                 'move','resize','no-border','no-capture'):
        raise ValueError('Unsupported task request')
    if request['action'] in ('launcher','service-action'):return launch_launcher(request,launcher)
    if request['action'] in ('fullscreen','no-border','no-capture') and type(request.get('state')) is not bool:
        raise ValueError('State changes require a desired boolean state')
    expected=(request.get('address'),request.get('pid'),request.get('generation'))
    if type(expected[1]) is not int or not isinstance(expected[2],str) or not expected[2]:raise ValueError('Invalid task identity')
    if request['action'] in ('new-instance','open-urls'):return launch_application(request,launcher)
    config=Path(os.environ.get('XDG_CONFIG_HOME',Path.home()/'.config'))/'illogical-impulse/config.json'
    if json.loads(config.read_text()).get('appearance',{}).get('bwmTheme')!='plasma':raise ValueError('Breeze no longer active')
    clients=query('clients')
    if not isinstance(clients,list):raise ValueError('Invalid client snapshot')
    matches=[c for c in clients if isinstance(c,dict) and identity(c)==expected and c.get('mapped') is True and workspace(c) is not None]
    if len(matches)!=1:raise ValueError('Task vanished or identity changed')
    if request['action'] in ('fullscreen','no-border','no-capture','move','resize') and not manager.native_fullscreen_allowed(matches[0]):
        raise ValueError('Action not available for this task')
    # Common manager rechecks address/PID in Lua immediately before applying.
    operation=[request['action']]
    if request['action'] in ('move','resize'):operation=['interactive',request['action']]
    if request['action'] in ('fullscreen','no-border','no-capture'):operation+=['--state','on' if request['state'] else 'off']
    reply=subprocess.run([sys.executable,str(Path(__file__).with_name('kwin-window.py')),
                          '--native-serialized','--expected-generation',expected[2],
                          '--pid',str(expected[1]),*operation,expected[0]],
                         capture_output=True,text=True,timeout=4)
    if reply.returncode:raise ValueError('Common task manager rejected action')
    return {'version':1,'accepted':True} # Acceptance is not a certificate of final geometry/state.


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('operation',choices=('snapshot','action'))
    parser.add_argument('--launcher',type=Path,help='Native host executable, supplied only by the task bridge for application startup')
    args=parser.parse_args()
    try:
        if args.operation=='snapshot':result=snapshot()
        else:
            raw=sys.stdin.read(65537)
            if len(raw)>65536:raise ValueError('Task request too large')
            result=action(json.loads(raw),args.launcher)
        print(json.dumps(result,ensure_ascii=False));return 0
    except (OSError,ValueError,TypeError,KeyError,subprocess.SubprocessError):
        print('BWM native tasks: IPC unavailable or request rejected',file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
