"""Structured failures with machine-readable recovery information."""
from __future__ import annotations

from collections.abc import Mapping
from typing import TypedDict


class ErrorDocument(TypedDict):
    """The public error wire representation."""

    code: str
    message: str
    details: dict[str, object]


class AstetikError(ValueError):
    """A failed scientific or artifact contract with machine-readable recovery."""

    def __init__(self, code: str, message: str, details: Mapping[str, object] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.details: dict[str, object] = dict(details) if details is not None else {}

    def to_dict(self) -> ErrorDocument:
        return {"code": self.code, "message": str(self), "details": self.details}
