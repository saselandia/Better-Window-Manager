"""Política común durante un cambio de skin, heredada también por los hooks separados."""
import os
from contextlib import contextmanager


def switching():
    return os.environ.get("BWM_SKIN_SWITCH") == "1"


@contextmanager
def skin_change():
    previous = os.environ.get("BWM_SKIN_SWITCH")
    os.environ["BWM_SKIN_SWITCH"] = "1"
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("BWM_SKIN_SWITCH", None)
        else:
            os.environ["BWM_SKIN_SWITCH"] = previous
