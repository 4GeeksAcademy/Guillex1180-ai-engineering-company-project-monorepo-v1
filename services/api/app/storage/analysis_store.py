from __future__ import annotations

from typing import Any

_last_analysis: dict[str, Any] | None = None


def save_last_analysis(result: dict[str, Any]) -> None:
    global _last_analysis
    _last_analysis = result


def get_last_analysis() -> dict[str, Any] | None:
    return _last_analysis


def clear_last_analysis() -> None:
    global _last_analysis
    _last_analysis = None
