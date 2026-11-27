#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""T7: decode original cursors and obtain frames from the BWM decoration helper.

Run after native KNS installation and source review. C++ decorations are built
from reviewed source into the work directory, never installed globally. The
review ledger must contain the source-tree digest for each compiled package.
"""
import argparse
import ctypes
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
spec = importlib.util.spec_from_file_location('store_compat', HERE / 'store-compat.py')
store = importlib.util.module_from_spec(spec); spec.loader.exec_module(store)
sys.path.insert(0, str(ROOT / 'tests'))
import bwm_decorator_client as dc


class CursorImage(ctypes.Structure):
    _fields_ = [(name, ctypes.c_uint32) for name in ('version', 'size', 'width', 'height', 'xhot', 'yhot', 'delay')] + [('pixels', ctypes.POINTER(ctypes.c_uint32))]


class CursorImages(ctypes.Structure):
    _fields_ = [('nimage', ctypes.c_int), ('images', ctypes.POINTER(ctypes.POINTER(CursorImage))), ('name', ctypes.c_char_p)]


def prepare(work, decorator):
    review = json.loads((work / 'review.json').read_text())
    cursor = ctypes.CDLL('libXcursor.so.1')
    cursor.XcursorFilenameLoadImages.argtypes = [ctypes.c_char_p, ctypes.c_int]
    cursor.XcursorFilenameLoadImages.restype = ctypes.POINTER(CursorImages)
    cursor.XcursorImagesDestroy.argtypes = [ctypes.POINTER(CursorImages)]
    for item in sorted(work.iterdir()):
        if not (item / 'install.json').exists(): continue
        if item.name.startswith('xcursor-'):
            rows = []
            for path in (item / 'data/icons').glob('*/cursors/left_ptr'):
                for size in (24, 48):
                    images = cursor.XcursorFilenameLoadImages(os.fsencode(path), size)
                    if not images: raise RuntimeError('Native cursor decoding failed: ' + str(path))
                    image = images.contents.images[0].contents
                    raw = ctypes.string_at(image.pixels, image.width * image.height * 4)
                    Image.frombytes('RGBA', (image.width, image.height), raw, 'raw', 'BGRA').save(item / f'cursor-{size}.png')
                    rows.append({'requestedSize': size, 'width': image.width, 'height': image.height,
                                 'frames': images.contents.nimage, 'hotspot': [image.xhot, image.yhot]})
                    cursor.XcursorImagesDestroy(images)
            (item / 'cursor.json').write_text(json.dumps(rows, indent=2))
        if not item.name.startswith(('aurorae-', 'window-decorations-', 'cpp-')): continue
        if item.name.startswith('cpp-'):
            assert review[item.name]['sha256'] == store.tree_hash(item / 'data/aurorae/themes'), 'Stale C++ review'
            themes = [('', review[item.name]['library'])]
        else:
            themes = [('__aurorae__svg__' + p.name, 'org.kde.kwin.aurorae') for p in sorted((item / 'data/aurorae/themes').iterdir())]
        for path in item.glob('decoration-*.png'): path.unlink()
        env = store.environment(item)
        env.update(QT_PLUGIN_PATH=str(item / 'plugins'), LD_LIBRARY_PATH=str(item / 'plugins/org.kde.kdecoration3'))
        (item / 'config/kdeglobals').write_text(Path('/usr/share/color-schemes/BreezeDark.colors').read_text())
        rows = []
        for number, (theme, library) in enumerate(themes):
            (item / 'config/kwinrc').write_text(f'[org.kde.kdecoration2]\nlibrary={library}\ntheme={theme}\nButtonsOnLeft=MS\nButtonsOnRight=HIAX\n')
            socket = item / 'runtime/d'; socket.unlink(missing_ok=True)
            with (item / f'deco-{number}.log').open('w') as log:
                process = subprocess.Popen(store.sandbox(work, item, [decorator, '--socket', socket]), env=env, stdout=log, stderr=subprocess.STDOUT)
                client = None
                try:
                    for _ in range(100):
                        if socket.exists() or process.poll() is not None: break
                        time.sleep(.05)
                    client = dc.Client(str(socket))
                    window = client.create(1, caption='T7 — ' + item.name, app_class='bwm-store-fixture')
                    assert client.wait_frame(1); client.settle(.25)
                    image = dc.frame_image(window.frames[-1])
                    image.crop((0, 0, image.width, min(85, image.height))).save(item / f'decoration-{number}.png')
                    client.update(1, scale=1.5, caption='T7 — escala 1,5', app_class='bwm-store-fixture'); client.settle(.2)
                    assert window.frames[-1].scale == 1.5
                    rows.append({'theme': theme, 'library': library, 'ack': client.ack, 'errors': client.errors,
                                 'scale15': True, 'borders': window.geometry['borders']})
                finally:
                    if client: client.close()
                    process.terminate(); process.wait(timeout=5)
        (item / 'decorations.json').write_text(json.dumps(rows, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--decorator', type=Path, required=True)
    args = parser.parse_args()
    prepare(store.private_root(args.work), args.decorator.resolve())
