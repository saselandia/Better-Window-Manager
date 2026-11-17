# SPDX-License-Identifier: GPL-2.0-or-later
"""Bounded transaction lock for the two experimental native panel adapters.

Existing daily callers do not participate in this lock. Never unlink a lock file:
doing so while a process holds its inode would create two independent authorities.
"""
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import stat
import time


@contextmanager
def action_lock(timeout=1.0):
    runtime=Path(os.environ['XDG_RUNTIME_DIR']).absolute()
    if runtime.resolve()!=runtime:raise ValueError('Native runtime must be canonical')
    directory=os.open(runtime,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
    fd=None
    try:
        info=os.fstat(directory)
        if info.st_uid!=os.getuid() or stat.S_IMODE(info.st_mode)&0o077:
            raise ValueError('Native runtime must be private and owned')
        fd=os.open('bwm-r4-native-actions.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW|os.O_CLOEXEC,0o600,dir_fd=directory)
        info=os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid!=os.getuid() or info.st_nlink!=1 or stat.S_IMODE(info.st_mode)!=0o600:
            raise ValueError('Invalid native action lock')
        deadline=time.monotonic()+timeout
        while True:
            try:
                fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
                break
            except BlockingIOError:
                remaining=deadline-time.monotonic()
                if remaining<=0:raise TimeoutError('Native action transaction busy')
                time.sleep(min(.01,remaining))
        yield
    finally:
        if fd is not None:os.close(fd)
        os.close(directory)


def require_breeze():
    config=Path(os.environ.get('XDG_CONFIG_HOME',Path.home()/'.config'))/'illogical-impulse/config.json'
    if json.loads(config.read_text()).get('appearance',{}).get('bwmTheme')!='plasma':
        raise ValueError('Breeze no longer active')
