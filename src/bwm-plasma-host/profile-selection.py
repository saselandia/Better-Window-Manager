#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Inspect or choose a persistent native profile; never starts or replaces a panel."""
import argparse
import importlib.util
import os
from pathlib import Path
import re
import subprocess
import tempfile


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary',type=Path,required=True)
    actions=parser.add_subparsers(dest='action',required=True)
    actions.add_parser('status')
    choose=actions.add_parser('select');choose.add_argument('name')
    clear=actions.add_parser('clear')
    for action in (choose,clear):action.add_argument('--revision',type=int,required=True,help='Current revision returned by status')
    args=parser.parse_args();binary=args.binary.expanduser().resolve()
    if not binary.is_file() or not os.access(binary,os.X_OK):parser.error(f'No existe un auxiliar ejecutable en {binary}')
    if args.action=='select' and not re.fullmatch(r'[a-z0-9][a-z0-9._-]{0,63}',args.name):parser.error('Nombre de perfil persistente no válido')
    if args.action!='status' and not 0<=args.revision<=2**53-1:parser.error('Revisión de selección no válida')
    command=['--profile-selection-info'] if args.action=='status' else (['--select-profile',args.name,str(args.revision)]
        if args.action=='select' else ['--clear-profile-selection',str(args.revision)])
    with tempfile.TemporaryDirectory(prefix='bwm-r4-selection-') as temporary:
        root=Path(temporary)
        for name in ('config','data','cache','runtime','defaults'):(root/name).mkdir(mode=0o700)
        env={key:value for key,value in os.environ.items() if not key.startswith('BWM_R4_') and key not in
            ('DISPLAY','WAYLAND_DISPLAY','WAYLAND_SOCKET','HYPRLAND_INSTANCE_SIGNATURE','KDESYCOCA')}
        env.update(QT_QPA_PLATFORM='offscreen',QT_QUICK_BACKEND='software',
            XDG_CONFIG_HOME=str(root/'config'),XDG_DATA_HOME=str(root/'data'),XDG_CACHE_HOME=str(root/'cache'),
            XDG_RUNTIME_DIR=str(root/'runtime'),XDG_CONFIG_DIRS=str(root/'defaults'),
            XDG_DATA_DIRS=str(Path(os.environ.get('XDG_DATA_HOME',Path.home()/'.local/share')))+os.pathsep+os.environ.get('XDG_DATA_DIRS','/usr/local/share:/usr/share'),
            DBUS_SESSION_BUS_ADDRESS='unix:path='+str(root/'no-bus'))
        spec=importlib.util.spec_from_file_location('bwm_selection_policy',Path(__file__).resolve().parents[2]/'config/hypr/skins/plasma/scripts/native_launch.py')
        policy=importlib.util.module_from_spec(spec);spec.loader.exec_module(policy);policy.write_host_policy(root/'defaults')
        try:result=subprocess.run([str(binary),*command],env=env,capture_output=True,text=True,timeout=25)
        except (OSError,subprocess.SubprocessError) as error:parser.error(f'No se pudo consultar/cambiar la selección: {error}')
        if result.returncode:parser.error(result.stderr.strip())
        print(result.stdout,end='');return 0


if __name__=='__main__':raise SystemExit(main())
