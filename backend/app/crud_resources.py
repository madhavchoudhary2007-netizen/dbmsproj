from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .api.crud import (
    CRUD_RESOURCES,
    build_crud_router,
    create_crud_router,
    crud_router,
)

__all__ = [
    "CRUD_RESOURCES",
    "build_crud_router",
    "create_crud_router",
    "crud_router",
    "register_resources",
]


def register_resources(crud_routes: Callable[..., Any]) -> None:
    for spec in CRUD_RESOURCES:
        if spec[4] is not None:
            crud_routes(spec[0], spec[1], spec[2], spec[3], spec[4])
        elif spec[3]:
            crud_routes(spec[0], spec[1], spec[2], spec[3])
        else:
            crud_routes(spec[0], spec[1], spec[2])
