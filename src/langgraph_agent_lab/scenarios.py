"""Scenario loading."""

from __future__ import annotations

import json
from pathlib import Path

from .state import Scenario


def load_scenarios(path: str | Path | list[str | Path]) -> list[Scenario]:
    scenarios: list[Scenario] = []
    if isinstance(path, list):
        for entry in path:
            scenarios.extend(load_scenarios(entry))
        return scenarios

    with Path(path).open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                scenarios.append(Scenario.model_validate_json(line))
            except Exception as exc:
                raise ValueError(f"Invalid scenario at line {line_no}: {exc}") from exc
    if len(scenarios) < 6:
        raise ValueError("At least 6 scenarios are required for grading")
    return scenarios
