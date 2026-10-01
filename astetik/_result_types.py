"""Publication verification and canonical evidence domains."""
from __future__ import annotations

from typing import NotRequired, TypedDict

from ._types import JsonObject


class VerificationCheck(TypedDict):
    """One bounded artifact check with its measured evidence."""

    check: str
    passed: bool
    width_mm: NotRequired[float]
    height_mm: NotRequired[float]
    minimum_pt: NotRequired[float]
    issues: NotRequired[list[JsonObject]]
    recovery: NotRequired[str]
    checksum_passed: NotRequired[bool]
    fonts: NotRequired[list[JsonObject]]


class VerificationReport(TypedDict):
    """Publication readiness of the retained rendered artifact."""

    passed: bool
    checks: list[VerificationCheck]
    limitations: list[str]
