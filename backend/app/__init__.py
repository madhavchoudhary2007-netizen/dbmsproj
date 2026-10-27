
"""Application package aliases for both supported import roots."""

import importlib
import sys


_PACKAGE = sys.modules[__name__]
_BACKEND = importlib.import_module("backend")
setattr(_BACKEND, "app", _PACKAGE)


if __name__ == "app":
    sys.modules["backend.app"] = _PACKAGE
elif __name__ == "backend.app":
    sys.modules["app"] = _PACKAGE
