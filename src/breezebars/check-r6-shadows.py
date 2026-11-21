#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 BWM
# SPDX-License-Identifier: GPL-2.0-or-later
"""Compare BWM's shadow geometry/raster with the unmodified KWin 6.7.5 method.

No compositor, captures, session configuration or installed binaries are changed.
The reference runs with Qt geometry and real KDecoration3 shadow geometries, outside KWin.
It does not certify OpenGL composition or visual parity in a Plasma session.
"""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SOURCE_SHA256 = "4724271f9314b61f16280a096e32bda6008ba551c5e80230b5066aa5452f92cd"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kwin", type=Path, required=True, help="Extracted kwin-6.7.5 directory")
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--asan", action="store_true")
    parser.add_argument("--native-samples", action="store_true", help="Also build/use the real disposable decorator helper")
    args = parser.parse_args()
    source_path = args.kwin / "src/scene/shadowitem.cpp"
    source = source_path.read_bytes()
    digest = hashlib.sha256(source).hexdigest()
    if digest != SOURCE_SHA256:
        parser.error("KWin shadow reference differs from the reviewed 6.7.5 release")
    source = source.decode()
    oracle = source[:source.index("#include")] + source[source.index("static inline void distributeHorizontally"):source.index("void ShadowItem::preprocess()")]
    env = dict(os.environ)
    env.pop("QT_QPA_PLATFORMTHEME", None)
    os.environ.pop("QT_QPA_PLATFORMTHEME", None)  # The disposable Qt helpers must not start GTK.
    env["ASAN_OPTIONS"] = "detect_leaks=0"
    samples = []
    if args.native_samples:
        sys.path.insert(0, str(ROOT / "tests"))
        import test_bwm_decorator as td
        td.BwmDecoratorTest.setUpClass()
        fixture = td.BwmDecoratorTest()
        fixture.binary = td.BwmDecoratorTest.binary
        for scheme in ("BreezeDark", "BreezeLight"):
            helper = td.Helper(fixture, kdeglobals=td.scheme(scheme))
            try:
                for scale in (1., 1.25, 1.5, 2.):
                    for active in (True, False):
                        wid = len(samples) + 1
                        window = helper.client.create(wid, scale=scale,
                            flags=td.dc.DEFAULT_FLAGS | (td.dc.ACTIVE if active else 0))
                        if not helper.client.wait_frame(wid):
                            raise RuntimeError("Decorator did not provide a frame")
                        helper.client.settle(.2)
                        if not window.shadow or not window.shadow["pixels"]:
                            raise RuntimeError("Decorator did not provide shadow pixels")
                        sample = dict(window.shadow, name=f"{scheme}-{'active' if active else 'inactive'}-{scale}", scale=scale)
                        sample["pixels"] = base64.b64encode(sample["pixels"]).decode()
                        samples.append(sample)
                        helper.client.destroy(wid)
            finally:
                helper.close()
        alternate = td.find_aurorae()
        if alternate:
            data, theme = alternate
            helper = td.Helper(fixture, kdeglobals=td.scheme("BreezeDark"),
                library="org.kde.kwin.aurorae", theme=f"__aurorae__svg__{theme}", data=data)
            try:
                for active in (True, False):
                    wid = len(samples) + 1
                    window = helper.client.create(wid, flags=td.dc.DEFAULT_FLAGS | (td.dc.ACTIVE if active else 0))
                    if not helper.client.wait_frame(wid, timeout=8):
                        raise RuntimeError("Aurorae did not provide a frame")
                    helper.client.settle(.5)
                    if window.shadow and window.shadow["pixels"]:
                        sample = dict(window.shadow, name=f"Aurorae-{theme}-{'active' if active else 'inactive'}", scale=1.)
                        sample["pixels"] = base64.b64encode(sample["pixels"]).decode()
                        samples.append(sample)
                    helper.client.destroy(wid)
            finally:
                helper.close()
    with tempfile.TemporaryDirectory(prefix="bwm-r6-shadow-") as temporary:
        tmp = Path(temporary)
        (tmp / "kwin-shadow-reference.inc").write_text(oracle)
        (tmp / "samples.json").write_text(json.dumps(samples))
        flags = shlex.split(subprocess.check_output(["pkg-config", "--cflags", "--libs", "Qt6Gui"], text=True))
        cmd = [os.environ.get("CXX", "g++"), "-std=c++2b", "-O1", "-g", "-fPIC", "-Wall", "-Wextra",
               "-I" + str(tmp), "-I" + str(ROOT / "src/breezebars"),
               "-I" + str(ROOT / "src/bwm-decorator"), "-I/usr/include/KDecoration3",
               str(ROOT / "tests/r6_shadow_reference.cpp"), "-o", str(tmp / "compare"), "-lkdecorations3", *flags]
        if args.asan:
            cmd += ["-fsanitize=address,undefined", "-fno-omit-frame-pointer", "-no-pie"]
        built = subprocess.run(cmd, env=env, capture_output=True, text=True)
        if built.returncode:
            raise RuntimeError(built.stderr)
        tested = subprocess.run([str(tmp / "compare"), str(tmp / "samples.json")], env=env,
                                capture_output=True, text=True, timeout=90)
        if tested.returncode:
            raise RuntimeError(tested.stdout + tested.stderr)
        report = json.loads(tested.stdout)
    report.update(version=1, passed=True, kwinVersion="6.7.5", referenceSha256=digest,
        asan=args.asan, compositorModified=False, compositorRenderVerified=False,
        asanScope="Comparison harness, ShadowState and both bounded shadow/tile buffer readers; sampled helper is a normal build" if args.asan else "none",
        scope="KWin method on Qt geometry, KDecoration3 geometry, CPU raster and native helper samples")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
