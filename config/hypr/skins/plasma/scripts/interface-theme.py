#!/usr/bin/env python3
"""F12: resolve original KDE configuration and package entry points without editing the installed packages."""
import configparser
import json
import os
import hashlib
import shutil
import re
import tempfile
from pathlib import Path


def config(name):
    home = Path(os.environ.get('XDG_CONFIG_HOME', Path.home()/'.config'))
    dirs = [Path(p) for p in os.environ.get('XDG_CONFIG_DIRS','/etc/xdg').split(':') if p]
    parser = configparser.ConfigParser(interpolation=None, strict=False)
    parser.optionxform = str
    parser.read([str(p/name) for p in reversed(dirs)] + [str(home/'kdedefaults'/name),str(home/name)], encoding='utf-8')
    return parser


def package(kind, identifier):
    if not identifier or identifier in ('.','..') or '/' in identifier or '\\' in identifier:
        return None
    roots = [Path(os.environ.get('XDG_DATA_HOME',Path.home()/'.local/share'))]
    roots += [Path(p) for p in os.environ.get('XDG_DATA_DIRS','/usr/local/share:/usr/share').split(':') if p]
    return next((p/kind/identifier for p in roots if (p/kind/identifier).is_dir()),None)


def adapt_switcher(source):
    if not source:
        return ''
    source=Path(source)
    origin=next((p.parent for p in source.parents if p.name=='contents'),source.parent)
    signature='adapter-v3:'+str(source)
    for item in sorted(origin.rglob('*')):
        if item.is_file():
            stat=item.stat();signature+=str(item.relative_to(origin))+str(stat.st_mtime_ns)+str(stat.st_size)
    fingerprint=hashlib.sha256(signature.encode()).hexdigest()[:20]
    dest=Path(os.environ.get('XDG_CACHE_HOME',Path.home()/'.cache'))/'bwm/plasma/tabbox'/fingerprint
    if not dest.exists():
        dest.parent.mkdir(parents=True,exist_ok=True)
        temporary=Path(tempfile.mkdtemp(prefix='.theme-',dir=dest.parent))
        try:
            shutil.copytree(origin,temporary,dirs_exist_ok=True,symlinks=True)
            compat=(Path.home()/'.config/quickshell/ii/modules/plasma/switcher/compat').as_uri()
            for item in temporary.rglob('*.qml'):
                if item.is_symlink():continue
                text=item.read_text()
                text=re.sub(r'import org\.kde\.kwin(?:\s+[0-9.]+)?(?P<alias>\s+as\s+\w+)?',lambda m:'import "'+compat+'"'+(m['alias'] or ''),text)
                text=re.sub(r'(?m)^(?=[ \t]*import\b)',lambda m:'import "'+compat+'" as BwmCompat\n',text,count=1)
                text=text.replace('PlasmaCore.Dialog {','BwmCompat.Dialog {')
                text=text.replace('import org.kde.plasma.workspace.osd','// BWM: OsdWindow is hosted by layer-shell')
                text=text.replace('OsdWindow {','BwmCompat.Dialog {')
                item.write_text(text)
            try:os.replace(temporary,dest)
            except OSError:
                if not dest.exists():raise
        finally:
            if temporary.exists():shutil.rmtree(temporary)
    return str(dest/source.relative_to(origin))


def snapshot():
    globals_, kwin = config('kdeglobals'), config('kwinrc')
    look = globals_.get('KDE','LookAndFeelPackage',fallback='org.kde.breeze.desktop')
    layout = kwin.get('TabBox','LayoutName',fallback='thumbnail_grid')
    theme = package('plasma/look-and-feel',look)
    switcher = package('kwin/tabbox',layout)
    def source(root, *names):
        return next((str(root/name) for name in names if (root/name).is_file()),'') if root else ''
    return dict(lookAndFeel=look,layout=layout,
                userImage=next((str(p) for p in (Path.home()/".face.icon",Path.home()/".face") if p.is_file()),""),
                switcherSource=adapt_switcher(source(switcher,'contents/ui/main.qml')),
                lockSource=source(theme,'contents/lockscreen/LockScreenUi.qml','contents/lockscreen/main.qml'),
                osdSource=adapt_switcher(source(theme,'contents/osd/Osd.qml','contents/osd/main.qml')))

if __name__=='__main__':
    print(json.dumps(snapshot()))
