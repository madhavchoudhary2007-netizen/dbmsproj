
"""Application package aliases for both supported import roots."""

import importlib
import sys


_PACKAGE = sys.modules[__name__]
try:
    _BACKEND = importlib.import_module("backend")
except ModuleNotFoundError as error:
    if error.name != "backend":
        raise
    _BACKEND = None
else:
    setattr(_BACKEND, "app", _PACKAGE)


if __name__ == "app":
    if _BACKEND is not None:
        sys.modules["backend.app"] = _PACKAGE
elif __name__ == "backend.app":
    sys.modules["app"] = _PACKAGE
