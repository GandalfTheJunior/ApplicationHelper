"""Shared strict validation and conservative name normalization."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


def normalize(value: str) -> str:
    """Ignore only whitespace and case; preserve punctuation (C != C++)."""
    return " ".join(value.split()).casefold()
