#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Build and check the local R4 SNI proxy from the pinned upstream archive."""
import argparse
import hashlib
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[2]
PATCH_DIR = ROOT/'patches/xdg-dbus-proxy'
SOURCE = 'xdg-dbus-proxy-0.1.8'
SHA256 = 'b6630bd24f8161b0e2546d2acbb014a3b3249f5c0d75f2a863ade898b9034d3d'
DESTINATION = ROOT/'build/bwm-plasma-host/tray-proxy/xdg-dbus-proxy'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, default=Path('/var/cache/distfiles')/f'{SOURCE}.tar.xz')
    args = parser.parse_args()
    if not args.archive.is_file() or hashlib.sha256(args.archive.read_bytes()).hexdigest() != SHA256:
        parser.error(f'Falta el archivo original verificado de {SOURCE}. Indica su ruta con --archive.')
    with tempfile.TemporaryDirectory(prefix='bwm-r4-tray-proxy-build-') as directory:
        work = Path(directory)
        with tarfile.open(args.archive) as archive:
            archive.extractall(work, filter='data')
        source, build = work/SOURCE, work/'build'
        subprocess.run(['patch','-p1','-i',PATCH_DIR/'0.1.8-sni-unique-getall.patch'], cwd=source, check=True)
        subprocess.run(['meson','setup',build,source,'-Dman=disabled','-Dtests=false'],check=True)
        subprocess.run(['meson','compile','-C',build],check=True)
        flags = shlex.split(subprocess.check_output(['pkg-config','--cflags','--libs','gio-unix-2.0'],text=True))
        test = work/'test-unique-sni-policy'
        subprocess.run(['cc','-D_GNU_SOURCE','-I',source,'-I',build,PATCH_DIR/'test-unique-sni-policy.c','-o',test,*flags],check=True)
        subprocess.run([test],check=True)
        binary = build/'xdg-dbus-proxy'
        for rule in ('--call=:1.42=*', '--call=:1.42=org.freedesktop.DBus.Properties.GetAll@/Item/*',
                     '--call=:1.42=org.kde.StatusNotifierItem.Activate@/Item',
                     '--call=:1.42=org.kde.StatusNotifierItem.NewIcon@/Item',
                     '--broadcast=:1.42=org.kde.StatusNotifierItem.NewMenu@/Item',
                     '--broadcast=:1.42=org.kde.StatusNotifierItem.NewStatus@/Item/*',
                     '--broadcast=:1.42.*=org.kde.StatusNotifierItem.NewIcon@/Item'):
            result = subprocess.run([binary,'unix:path=/unused',work/'socket','--filter',rule],capture_output=True,text=True,timeout=3)
            if result.returncode == 0 or 'unique-name rule requires' not in result.stderr:
                raise RuntimeError('El proxy aceptó una regla fuera del alcance del ensayo')
        DESTINATION.parent.mkdir(parents=True,exist_ok=True)
        fd, pending = tempfile.mkstemp(prefix='.proxy-',dir=DESTINATION.parent)
        try:
            with os.fdopen(fd,'wb') as destination, binary.open('rb') as executable:
                shutil.copyfileobj(executable,destination)
                os.fchmod(destination.fileno(),0o755)
            os.replace(pending,DESTINATION)
        finally:
            Path(pending).unlink(missing_ok=True)
    print(DESTINATION)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
