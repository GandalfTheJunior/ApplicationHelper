"""Regenerate committed JSON schemas from the single source of truth: models."""

import json
from pathlib import Path

from career_agent.domain.candidate import Career
from career_agent.domain.job import JobPosting
from career_agent.domain.matching import MatchResult


def main() -> None:
    destination = Path(__file__).resolve().parents[1] / "schemas"
    destination.mkdir(exist_ok=True)
    for name, model in (
        ("candidate", Career),
        ("job", JobPosting),
        ("match", MatchResult),
    ):
        schema = model.model_json_schema()
        schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        (destination / f"{name}.schema.json").write_text(
            json.dumps(schema, indent=2) + "\n", encoding="utf-8"
        )


if __name__ == "__main__":
    main()
