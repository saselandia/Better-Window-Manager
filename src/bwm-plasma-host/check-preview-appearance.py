#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Native KDE startup appearance, entirely within disposable XDG directories."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile
import zlib


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary',type=Path,required=True)
    parser.add_argument('--probe',type=Path,required=True)
    parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args()
    report={'version':1,'sessionModified':False,'nativeAppearanceVerified':False,'liveThemeFollowing':False}
    def run(command,env,success=True):
        reply=subprocess.run([str(x) for x in command],env=env,capture_output=True,text=True,timeout=10)
        if success and reply.returncode:raise AssertionError(reply.stderr)
        return reply
    def probe(env):return json.loads(run([args.probe],env).stdout)
    def digests(directory):
        return {str(p.relative_to(directory)):hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.rglob('*') if p.is_file()}
    try:
        with tempfile.TemporaryDirectory(prefix='bwm-r4-appearance-') as tmp:
            root=Path(tmp);source=root/'session';source.mkdir();(source/'kdedefaults').mkdir()
            for name in ('config','data','cache','runtime','defaults','assets','system'):(root/name).mkdir(mode=0o700)
            env=dict(os.environ,QT_QPA_PLATFORM='offscreen',QT_QPA_PLATFORMTHEME='kde',QT_QUICK_BACKEND='software',
                XDG_CONFIG_HOME=str(root/'config'),XDG_DATA_HOME=str(root/'data'),XDG_CACHE_HOME=str(root/'cache'),
                XDG_RUNTIME_DIR=str(root/'runtime'),XDG_CONFIG_DIRS=str(root/'defaults'),
                XDG_DATA_DIRS=str(root/'assets')+':/usr/local/share:/usr/share',DBUS_SESSION_BUS_ADDRESS='unix:path='+str(root/'no-bus'),
                BWM_R4_APPEARANCE_CONFIG_DIRS=str(root/'system'))
            for key in ('DISPLAY','WAYLAND_DISPLAY','WAYLAND_SOCKET','HYPRLAND_INSTANCE_SIGNATURE','QT_STYLE_OVERRIDE',
                        'QT_QUICK_CONTROLS_STYLE','KDE_COLOR_SCHEME_PATH','KDESYCOCA'):env.pop(key,None)
            theme='bwm-r4-appearance-fixture';icons=root/'assets/icons'/theme;image=icons/'16x16/apps/bwm-r4-native-appearance-fixture.png'
            image.parent.mkdir(parents=True)
            (icons/'index.theme').write_text('[Icon Theme]\nName=Own native appearance fixture\nDirectories=16x16/apps\n[16x16/apps]\nSize=16\nType=Fixed\nContext=Applications\n')
            def chunk(kind,data):return struct.pack('!I',len(data))+kind+data+struct.pack('!I',zlib.crc32(kind+data)&0xffffffff)
            image.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!2I5B',16,16,8,6,0,0,0))+
                chunk(b'IDAT',zlib.compress((b'\0'+bytes.fromhex('39b574ff')*16)*16))+chunk(b'IEND',b''))
            (root/'system/kdeglobals').write_text('[General]\nsmallestReadableFont=Noto Sans,9,-1,5,50,0,0,0,0,0\n[Unrelated]\nSystemSecret=not-copied\n')
            (source/'kdedefaults/kdeglobals').write_text('[Icons]\nTheme=incorrect-default\n[General]\nColorScheme=BreezeDark\nAccentColor=1,2,3\n[Colors:Window]\nBackgroundNormal=1,2,3\n')
            (source/'kdeglobals').write_text('[Icons]\nTheme='+theme+'\n[General]\nfont=Noto Sans,15,-1,5,50,0,0,0,0,0\nAccentColor[$d]\nPrivatePath=/not/copied\n[Colors:View]\nBackgroundNormal=30,31,32\n[Colors:Window]\nBackgroundNormal=17,34,51\nForegroundNormal=240,241,242\n[KDE]\nwidgetStyle=Fusion\n[KFileDialog Settings]\nRecentFiles=not-copied\n')
            (source/'plasmarc').write_text('[Theme]\nname=breeze-dark\n[Unrelated]\nPrivateValue=not-copied\n')
            before=digests(source);systemBefore=digests(root/'system')
            report['beforeNativeProbe']=probe(env)
            assert report['beforeNativeProbe']['iconNull'] is True
            assert report['beforeNativeProbe']['iconTheme']!=theme
            staged=run([args.binary,'--stage-preview-appearance',source],env)
            report['staging']=json.loads(staged.stdout)
            report['afterNativeProbe']=probe(env);actual=report['afterNativeProbe']
            assert actual['iconTheme']==theme and actual['iconNull'] is False,actual
            assert actual['iconPixel']=='#39b574' and actual['windowColor']=='#112233',actual
            assert actual['fontSize']==15 and actual['plasmaTheme']=='breeze-dark',actual
            globalsFile=root/'config/kdeglobals';snapshot=globalsFile.read_text()
            assert 'not-copied' not in snapshot and 'PrivatePath' not in snapshot
            assert 'smallestReadableFont=' in snapshot and 'ColorScheme=BreezeDark' in snapshot
            assert 'AccentColor' not in snapshot
            assert 'PrivateValue' not in (root/'config/plasmarc').read_text()
            assert digests(source)==before and digests(root/'system')==systemBefore
            report['nativeAppearanceVerified']=True;report['sourceAndSystemUnchanged']=True
            report['unrelatedKeysExcluded']=True;report['nativeDefaultsMerged']=True;report['nativeDeletedValueRespected']=True
            # A later source change cannot silently alter this startup snapshot.
            (source/'kdeglobals').write_text('[Icons]\nTheme=breeze\n')
            assert globalsFile.read_text()==snapshot
            assert probe(env)['iconTheme']==theme
            report['snapshotRemainsIndependent']=True
            previous=digests(root/'config')
            refused=run([args.binary,'--stage-preview-appearance',source],env,False)
            assert refused.returncode==2 and 'overwrite' in refused.stderr
            assert digests(root/'config')==previous
            report['existingPreviewNotOverwritten']=True
            # Immutable defaults win through native KConfig, including over the
            # local value. The snapshot carries the resolved effective value.
            for name in ('kdeglobals','plasmarc'):(root/'config'/name).unlink()
            (source/'kdedefaults/kdeglobals').write_text('[Icons][$i]\nTheme='+theme+'\n')
            run([args.binary,'--stage-preview-appearance',source],env)
            assert probe(env)['iconTheme']==theme
            report['nativeImmutableValueRespected']=True
            bad=dict(env,XDG_CONFIG_HOME=str(source))
            unchanged=digests(source)
            refused=run([args.binary,'--stage-preview-appearance',source],bad,False)
            assert refused.returncode==2 and 'must differ' in refused.stderr
            assert digests(source)==unchanged
            report['sourceDestinationAliasRejected']=True
            report['passed']=True
    except (AssertionError,OSError,ValueError,subprocess.SubprocessError) as error:
        report['passed']=False;report['error']=str(error)
    args.report.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
    return 0 if report['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
