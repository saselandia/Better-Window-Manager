#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Run thumbnail bounds/QML tests with temporary native XDG stores."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile
import resource
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--binary',type=Path,required=True);p.add_argument('--report',type=Path,required=True)
p.add_argument('--host',type=Path,required=True)
a=p.parse_args()
with tempfile.TemporaryDirectory(prefix='bwm-r4-thumbnail-local-') as tmp:
    root=Path(tmp)
    for name in ('config','data','cache','runtime','defaults'):(root/name).mkdir(mode=0o700)
    env=dict(os.environ,QT_QPA_PLATFORM='offscreen',QT_QUICK_BACKEND='software',XDG_CONFIG_HOME=str(root/'config'),
        XDG_DATA_HOME=str(root/'data'),XDG_CACHE_HOME=str(root/'cache'),XDG_RUNTIME_DIR=str(root/'runtime'),
        XDG_CONFIG_DIRS=str(root/'defaults'),XDG_DATA_DIRS='/usr/local/share:/usr/share',
        DBUS_SESSION_BUS_ADDRESS='unix:path='+str(root/'no-bus'),BWM_R4_THUMBNAIL_LOCAL_ROOT=str(root))
    for key in ('DISPLAY','WAYLAND_DISPLAY','WAYLAND_SOCKET','HYPRLAND_INSTANCE_SIGNATURE','KDESYCOCA',
                'BWM_R4_TASK_ACTIONS','BWM_R4_TASK_THUMBNAILS'):env.pop(key,None)
    def no_core():resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    reply=subprocess.run([str(a.binary)],env=env,capture_output=True,text=True,timeout=20,preexec_fn=no_core)
    report={'version':1,'sessionModified':False,'nativeWindowCaptureVerified':False,
        'passed':reply.returncode==0,'clientExit':reply.returncode,'clientOutput':reply.stdout,'clientDiagnostics':reply.stderr}
    probe=subprocess.run([str(a.host),'--check-thumbnail-compositor'],env=env,capture_output=True,text=True,timeout=10,preexec_fn=no_core)
    try:
        state=json.loads(probe.stdout)
        good=probe.returncode==2 and state.get('verified') is False and state.get('reason')=='no-native-wayland-display' and state.get('capturesStarted') is False
        report.update(readOnlyGuardCliVerified=good,readOnlyGuardCli=state)
    except ValueError:good=False;report['readOnlyGuardCliError']=probe.stderr[-1000:]
    report['passed']=report['passed'] and good
    a.report.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
    raise SystemExit(0 if report['passed'] else 1)
