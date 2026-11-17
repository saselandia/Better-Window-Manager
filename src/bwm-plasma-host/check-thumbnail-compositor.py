#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Read-only guard diagnostics on Qt's actual Wayland connection; no preview/capture."""
import argparse
import json
import os
from pathlib import Path
import resource
import subprocess
import tempfile


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary',type=Path,default=Path(__file__).resolve().parents[2]/'build/bwm-plasma-host/bwm-plasma-host')
    args=parser.parse_args();binary=args.binary.expanduser().resolve()
    if not binary.is_file() or not os.access(binary,os.X_OK):parser.error('No hay un auxiliar compilado en '+str(binary))
    runtime=Path(os.environ.get('XDG_RUNTIME_DIR',f'/run/user/{os.getuid()}'))
    display=Path(os.environ.get('WAYLAND_DISPLAY','wayland-0'))
    if not display.is_absolute():display=runtime/display
    inherited=()
    if os.environ.get('WAYLAND_SOCKET'):
        try:
            fd=int(os.environ['WAYLAND_SOCKET']);os.fstat(fd);inherited=(fd,)
        except (OSError,ValueError):parser.error('WAYLAND_SOCKET no corresponde a un descriptor abierto')
    with tempfile.TemporaryDirectory(prefix='bwm-r4-compositor-check-') as tmp:
        root=Path(tmp)
        for name in ('config','data','cache','runtime','defaults'):(root/name).mkdir(mode=0o700)
        env=dict(os.environ,QT_QPA_PLATFORM='wayland',WAYLAND_DISPLAY=str(display),
            XDG_CONFIG_HOME=str(root/'config'),XDG_DATA_HOME=str(root/'data'),XDG_CACHE_HOME=str(root/'cache'),
            XDG_RUNTIME_DIR=str(root/'runtime'),XDG_CONFIG_DIRS=str(root/'defaults'),
            DBUS_SESSION_BUS_ADDRESS='unix:path='+str(root/'no-bus'))
        for key in tuple(env):
            if key.startswith('BWM_R4_'):env.pop(key)
        env['BWM_R4_GUARD_RUNTIME']=str(runtime)
        def no_core():resource.setrlimit(resource.RLIMIT_CORE,(0,0))
        try:
            reply=subprocess.run([str(binary),'--check-thumbnail-compositor'],env=env,capture_output=True,text=True,
                pass_fds=inherited,timeout=10,preexec_fn=no_core)
            report={'version':1,'sessionModified':False,'capturesStarted':False,'clientExit':reply.returncode}
            try:report['guard']=json.loads(reply.stdout)
            except ValueError:report['error']='El auxiliar no devolvió diagnóstico JSON';report['output']=reply.stdout[-1000:]
            if reply.stderr:report['diagnostics']=reply.stderr[-1500:]
        except (OSError,subprocess.SubprocessError) as error:
            report={'version':1,'sessionModified':False,'capturesStarted':False,'error':str(error),'clientExit':1}
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return report['clientExit']


if __name__=='__main__':raise SystemExit(main())
