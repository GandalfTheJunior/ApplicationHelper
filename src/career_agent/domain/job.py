"""Structured posting input for the bootstrap YAML parser."""

from typing import Literal

from pydantic import Field, HttpUrl, field_validator

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

    @field_validator("language_requirements")
    @classmethod
    def unique_languages(
        cls, values: list[LanguageRequirement]
    ) -> list[LanguageRequirement]:
        if len({normalize(value.name) for value in values}) != len(values):
            raise ValueError("Language requirements must have unique names")
        return values
