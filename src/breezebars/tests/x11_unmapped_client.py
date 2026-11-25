import ctypes, time, sys
X = ctypes.cdll.LoadLibrary('libX11.so.6')
X.XOpenDisplay.restype = ctypes.c_void_p
X.XDefaultRootWindow.restype = ctypes.c_ulong; X.XDefaultRootWindow.argtypes = [ctypes.c_void_p]
X.XCreateSimpleWindow.restype = ctypes.c_ulong
X.XCreateSimpleWindow.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_int, ctypes.c_int, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint, ctypes.c_ulong, ctypes.c_ulong]
for f in ('XMapWindow', 'XUnmapWindow'): getattr(X, f).argtypes = [ctypes.c_void_p, ctypes.c_ulong]
X.XFlush.argtypes = [ctypes.c_void_p]; X.XStoreName.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_char_p]
d = X.XOpenDisplay(None)
if not d: sys.exit(2)
w = X.XCreateSimpleWindow(d, X.XDefaultRootWindow(d), 0, 0, 300, 200, 0, 0, 0xffffff)
X.XStoreName(d, w, b'bwm-exit-x11'); X.XMapWindow(d, w); X.XFlush(d)
time.sleep(2); X.XUnmapWindow(d, w); X.XFlush(d)
print('unmapped', flush=True); time.sleep(60)
