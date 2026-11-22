"""R7 numeric easing bounds and frame-analysis regression; no session changes."""
import importlib.util
import re
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('r7_measurement',ROOT/'src/breezebars/check-r7-animations.py')
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class AnimationMeasurementTest(unittest.TestCase):
    def curve(self,name):
        source=m.ANIMATIONS.read_text()
        pattern=r'hl.curve\("'+name+r'",.*?points\s*=\s*\{\s*\{\s*([\d.]+),\s*([\d.]+)\s*\},\s*\{\s*([\d.]+),\s*([\d.]+)'
        match=re.search(pattern,source)
        self.assertIsNotNone(match,name)
        return tuple(map(float,match.groups()))

    def test_loaded_beziers_against_kwin_polynomials(self):
        for name,original in (('kwin_out_cubic',lambda x:1-(1-x)**3),
                              ('kwin_in_cubic',lambda x:x**3),
                              ('kwin_out_quart',lambda x:1-(1-x)**4)):
            x1,y1,x2,y2=self.curve(name)
            worst=0
            for i in range(20001):
                u=i/20000
                a,b,c=3*(1-u)**2*u,3*(1-u)*u*u,u**3
                x,y=a*x1+b*x2+c,a*y1+b*y2+c
                worst=max(worst,abs(y-original(x)))
            self.assertLess(worst,1/255,(name,worst))
            if name=='kwin_out_quart':
                # |d(error)/du| <= max|y'| + 4 max|x'| on [0,1].
                # Include half a grid cell, bounding even unsampled extrema.
                derivative_bound=3+12*max(x1,x2-x1,1-x2)
                self.assertLess(worst+derivative_bound/40000,1/255)
        # This would fail the previous .25,1 / .5,1 OutQuart approximation.
        self.assertNotEqual(self.curve('kwin_out_quart'),(.25,1,.5,1))

    def test_duration_estimator_separates_phase_and_length(self):
        for incoming in (True,False):
            samples=[]
            for t in range(0,700,17):
                u=max(0,min(1,(t-19)/400))
                y=1-(1-u)**3 if incoming else 1-u**3
                samples.append((t,y))
            fit=m.fit_cubic(samples,400,incoming)
            self.assertLess(abs(fit['fittedDurationMs']-400),.5)
            self.assertLess(abs(fit['fittedStartAfterEventMs']-19),.5)
            quantized=m.fit_cubic([(t,round(y*128)/128) for t,y in samples],400,incoming)
            # A quantized 17 ms frame stream cannot establish sub-millisecond phase.
            self.assertLess(abs(quantized['fittedDurationMs']-400),17)
            self.assertLess(quantized['maxProgressError'],1/128)

    def test_factor_zero_keeps_raw_frames_without_inventing_a_duration(self):
        frames=[dict(requestedMs=t,receivedMs=t+4,presentationMs=0,box=[],opacity=0) for t in (0,17,34,51,68)]
        report=m.summarize(frames,[dict(action='open',monotonicMs=10)],0)
        self.assertNotIn('opacityFit',report['events'][0])
        self.assertEqual(len(report['events'][0]['samples']),4)
        self.assertEqual(report['maxCaptureBracketMs'],4)

    def test_kwin_spring_motion_vs_continuous_ode_forward_and_reversal(self):
        import math
        # Exact KWin 6.7.5 SpringMotion::integrate (src/plugins/slide/springmotion.cpp):
        # 100 Hz step (dt=0.01) where evaluate() returns dp = state.velocity (not next.velocity),
        # causing a dt/2 = 5 ms position lag relative to the exact second-order ODE solved by Hyprutils.
        def kwin_step(pos, vel, anchor, k, c, dt=0.01):
            def eval_slope(p, v, dp, dv, h):
                np = p + dp * h
                nv = v + dv * h
                return v, (anchor - np) * k - nv * c
            k1p, k1v = eval_slope(pos, vel, 0.0, 0.0, 0.0)
            k2p, k2v = eval_slope(pos, vel, k1p, k1v, 0.5 * dt)
            k3p, k3v = eval_slope(pos, vel, k2p, k2v, 0.5 * dt)
            k4p, k4v = eval_slope(pos, vel, k3p, k3v, dt)
            return (pos + (k1p + 2 * k2p + 2 * k3p + k4p) * dt / 6.0,
                    vel + (k1v + 2 * k2v + 2 * k3v + k4v) * dt / 6.0)

        def exact_step(pos, vel, anchor, k, c, dt=0.001):
            def eval_slope(p, v, dp, dv, h):
                np = p + dp * h
                nv = v + dv * h
                return nv, (anchor - np) * k - nv * c
            k1p, k1v = eval_slope(pos, vel, 0.0, 0.0, 0.0)
            k2p, k2v = eval_slope(pos, vel, k1p, k1v, 0.5 * dt)
            k3p, k3v = eval_slope(pos, vel, k2p, k2v, 0.5 * dt)
            k4p, k4v = eval_slope(pos, vel, k3p, k3v, dt)
            return (pos + (k1p + 2 * k2p + 2 * k3p + k4p) * dt / 6.0,
                    vel + (k1v + 2 * k2v + 2 * k3v + k4v) * dt / 6.0)

        for factor in (0.5, 1.0, 2.0):
            k = 300.0 / factor
            c = 2.0 * math.sqrt(k) * 1.1
            # 1. Forward trajectory (0 -> 1)
            kp, kv = 0.0, 0.0
            ep, ev = 0.0, 0.0
            exact_history = {0: 0.0}
            raw_diff, shifted_diff = 0.0, 0.0
            for step in range(1, int(70 * factor) + 1):
                kp, kv = kwin_step(kp, kv, 1.0, k, c)
                for sub in range(1, 11):
                    ep, ev = exact_step(ep, ev, 1.0, k, c)
                    exact_history[(step - 1) * 10 + sub] = ep
                t_ms = step * 10
                raw_diff = max(raw_diff, abs(kp - exact_history[t_ms]))
                shifted_diff = max(shifted_diff, abs(kp - exact_history[t_ms - 5]))
            self.assertLess(raw_diff, 0.045, factor)
            self.assertLess(shifted_diff, raw_diff, factor)
            self.assertLess(shifted_diff, 0.018 if factor >= 1.0 else 0.025, factor)

            # 2. Mid-flight reversal at 120 ms (0 -> 1, then anchor switched back to 0 preserving velocity)
            kp, kv = 0.0, 0.0
            ep, ev = 0.0, 0.0
            rev_diff = 0.0
            for step in range(1, int(80 * factor) + 1):
                anchor = 1.0 if step <= 12 else 0.0
                kp, kv = kwin_step(kp, kv, anchor, k, c)
                for _ in range(10):
                    ep, ev = exact_step(ep, ev, anchor, k, c)
                rev_diff = max(rev_diff, abs(kp - ep))
            self.assertLess(rev_diff, 0.056, factor)


if __name__=='__main__':
    unittest.main()
