"""A shared YAML boundary with actionable errors that omit private input values."""

from pathlib import Path

import yaml
from pydantic import ValidationError

from career_agent.domain.base import Model


class DataLoadError(ValueError):
    """An unreadable file, malformed YAML, or invalid domain model."""


def load_yaml_model[T: Model](path: Path, model: type[T]) -> T:
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        raise DataLoadError(f"Cannot read UTF-8 file: {path}") from None
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as error:
        mark = getattr(error, "problem_mark", None)
        position = f" at line {mark.line + 1}, column {mark.column + 1}" if mark else ""
        raise DataLoadError(f"Malformed YAML in {path}{position}") from None
    if not isinstance(data, dict):
        raise DataLoadError(f"Expected a YAML mapping in {path}")
    try:
        return model.model_validate(data)
    except ValidationError as error:
        # ValidationError.__str__ includes input values; do not leak them to logs.
        fields = ", ".join(
            f"{'.'.join(map(str, item['loc'])) or '<root>'} ({item['type']})"
            for item in error.errors(include_input=False, include_context=False)
        )
        raise DataLoadError(f"Invalid {model.__name__} in {path}: {fields}") from None
