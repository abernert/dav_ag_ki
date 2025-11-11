from __future__ import annotations

from fastapi import HTTPException

COBOL_HTTP_MAP: dict[str, tuple[int, str]] = {
    "00": (200, "OK"),
    "01": (404, "Entity not found"),
    "70": (404, "Related entity missing"),
    "88": (503, "Backend temporarily unavailable"),
    "89": (503, "Backend temporarily unavailable"),
    "90": (500, "Backend error"),
    "98": (400, "Invalid request"),
    "99": (400, "Unsupported request"),
}


class CobolError(Exception):
    def __init__(self, code: str, message: str | None = None) -> None:
        self.code = code
        self.message = message or COBOL_HTTP_MAP.get(code, (500, "Unexpected error"))[1]
        super().__init__(f"COBOL {code}: {self.message}")


def http_exception_for(code: str, detail: str | None = None) -> HTTPException:
    status, default_detail = COBOL_HTTP_MAP.get(code, (500, "Unexpected error"))
    return HTTPException(status_code=status, detail=detail or default_detail)
