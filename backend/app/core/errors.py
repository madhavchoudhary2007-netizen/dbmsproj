from fastapi import Request
from fastapi.responses import JSONResponse


async def conflict_handler(_: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=409, content={"detail": "Resource conflicts with an existing record"}
    )


async def reference_conflict_handler(_: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=409, content={"detail": "Resource is referenced by official records"}
    )


async def integrity_handler(_: Request, exc: Exception) -> JSONResponse:
    code = getattr(exc, "sqlstate", None)
    if code in {"23502", "23514", "22001", "22003"}:
        status, detail = 422, "Record violates a required field or value constraint"
    else:
        status, detail = 409, "Record conflicts with existing data"
    return JSONResponse(status_code=status, content={"detail": detail})


async def database_unavailable_handler(_: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=503, content={"detail": "PostgreSQL is unavailable"})
