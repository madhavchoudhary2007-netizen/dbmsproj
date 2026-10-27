"""Application package aliases for both supported import roots."""

import importlib
import sys
from types import ModuleType

_PACKAGE = sys.modules[__name__]
_BACKEND: ModuleType | None
try:
    _BACKEND = importlib.import_module("backend")
except ModuleNotFoundError as error:
    if error.name != "backend":
        raise
    _BACKEND = None
else:
    _existing_package = sys.modules.get("backend.app")
    if _existing_package is not None and _existing_package is not _PACKAGE:
        raise ImportError("backend.app is already loaded as a distinct application package")
    _existing_attribute = vars(_BACKEND).get("app")
    if _existing_attribute is not None and _existing_attribute is not _PACKAGE:
        raise ImportError("backend.app already refers to a distinct application package")
    sys.modules["backend.app"] = _PACKAGE
    vars(_BACKEND)["app"] = _PACKAGE


if __name__ == "backend.app":
    _existing_package = sys.modules.get("app")
    if _existing_package is not None and _existing_package is not _PACKAGE:
        raise ImportError("app is already loaded as a distinct application package")
    sys.modules["app"] = _PACKAGE
