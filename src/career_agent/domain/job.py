"""Structured posting input for the bootstrap YAML parser."""

import hashlib
import json
from typing import Literal, Self

from pydantic import Field, HttpUrl, field_validator, model_validator

from career_agent.domain.base import Model, Text, normalize


class LanguageRequirement(Model):
    name: Text
    level: Text | None = None


class JobPosting(Model):
    company: Text | None = None
    title: Text | None = None
    location: Text | None = None
    remote_status: Literal["remote", "hybrid", "onsite", "unknown"] = "unknown"
    source_url: HttpUrl | None = None
    description: Text | None = None
    responsibilities: list[Text] = Field(default_factory=list)
    required_skills: list[Text] = Field(default_factory=list)
    preferred_skills: list[Text] = Field(default_factory=list)
    language_requirements: list[LanguageRequirement] = Field(default_factory=list)
    seniority: Text | None = None
    employment_type: Text | None = None

    @field_validator("required_skills", "preferred_skills")
    @classmethod
    def unique_skills(cls, values: list[str]) -> list[str]:
        # Repeated requirements must not inflate either coverage denominator.
        unique: dict[str, str] = {}
        for value in values:
            unique.setdefault(normalize(value), value)
        return list(unique.values())

    @model_validator(mode="after")
    def required_skills_take_precedence(self) -> Self:
        required = {normalize(skill) for skill in self.required_skills}
        # Values already passed field validation. Avoid recursive assignment
        # validation while enforcing this invariant on creation and assignment.
        object.__setattr__(
            self,
            "preferred_skills",
            [
                skill
                for skill in self.preferred_skills
                if normalize(skill) not in required
            ],
        )
        return self

    @field_validator("language_requirements")
    @classmethod
    def unique_languages(
        cls, values: list[LanguageRequirement]
    ) -> list[LanguageRequirement]:
        if len({normalize(value.name) for value in values}) != len(values):
            raise ValueError("Language requirements must have unique names")
        return values


def job_fingerprint(job: JobPosting) -> str:
    """SHA-256 of the complete validated posting in canonical UTF-8 JSON.

    Include defaults and all job fields, even those omitted from generation
    contexts. Preserve the validated text and list order. No candidate data,
    timestamps, object identity, or process-randomized hash() is involved.
    """
    serialized = json.dumps(
        job.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
