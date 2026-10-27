
"""Application package aliases for both supported import roots."""

import sys


if __name__ == "app":
    sys.modules.setdefault("backend.app", sys.modules[__name__])
elif __name__ == "backend.app":
    sys.modules.setdefault("app", sys.modules[__name__])
