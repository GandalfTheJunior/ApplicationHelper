"""Career facts and identity intentionally have different model boundaries."""

from typing import Literal, Self

from pydantic import Field, model_validator

from career_agent.domain.base import Model, Text, normalize


class Evidence(Model):
    id: Text
    type: Literal[
        "work_experience", "project", "education", "certification", "self_report"
    ]
    reference: Text
    description: Text


class Skill(Model):
    name: Text
    level: Text | None = None
    years: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    evidence: list[Evidence] = Field(min_length=1)


class Achievement(Model):
    """Recorded candidate data; descriptions and tags are not matched as skills."""

    id: Text
    description: Text
    skill_names: list[Text] = Field(default_factory=list)
    tags: list[Text] = Field(default_factory=list)


class WorkExperience(Model):
    id: Text
    employer: Text
    title: Text
    description: Text | None = None
    responsibilities: list[Text] = Field(default_factory=list)
    # Preserve the precision the candidate supplies; do not infer dates/tenure.
    start_period: Text | None = None
    end_period: Text | None = None
    achievements: list[Achievement] = Field(default_factory=list)

    @model_validator(mode="after")
    def unique_achievement_ids(self) -> Self:
        if len({item.id for item in self.achievements}) != len(self.achievements):
            raise ValueError(
                "Achievement IDs must be unique within each work experience"
            )
        return self


class Project(Model):
    id: Text
    name: Text
    description: Text


class Education(Model):
    id: Text
    institution: Text
    qualification: Text


class Certification(Model):
    id: Text
    name: Text
    issuer: Text | None = None


class Language(Model):
    name: Text
    level: Text | None = None
    evidence: list[Evidence] = Field(min_length=1)


class Career(Model):
    skills: list[Skill] = Field(default_factory=list)
    work_experience: list[WorkExperience] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    languages: list[Language] = Field(default_factory=list)
    certifications: list[Certification] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_evidence(self) -> Self:
        records = {
            "work_experience": self.work_experience,
            "project": self.projects,
            "education": self.education,
            "certification": self.certifications,
        }
        for entries in records.values():
            if len({entry.id for entry in entries}) != len(entries):
                raise ValueError("Record IDs must be unique within each record type")
        seen: dict[str, Evidence] = {}
        for facts in (self.skills, self.languages):
            if len({normalize(fact.name) for fact in facts}) != len(facts):
                raise ValueError(
                    "Skill and language names must be unique after normalization"
                )
            for fact in facts:
                for evidence in fact.evidence:
                    if evidence.type != "self_report" and evidence.reference not in {
                        record.id for record in records[evidence.type]
                    }:
                        raise ValueError(
                            "Evidence reference does not point to a career record"
                        )
                    if evidence.id in seen and seen[evidence.id] != evidence:
                        raise ValueError(
                            "An evidence ID cannot refer to different facts"
                        )
                    seen[evidence.id] = evidence
        return self


class Identity(Model):
    """Only a final artifact renderer should need these optional fields."""

    full_name: Text | None = None
    email: Text | None = None
    phone: Text | None = None
    address: Text | None = None


class SalaryExpectations(Model):
    minimum: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    maximum: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    currency: Text
    period: Literal["hour", "month", "year"] = "year"

    @model_validator(mode="after")
    def validate_range(self) -> Self:
        if (
            self.minimum is not None
            and self.maximum is not None
            and self.minimum > self.maximum
        ):
            raise ValueError("Salary minimum must not exceed maximum")
        return self


class Preferences(Model):
    target_roles: list[Text] = Field(default_factory=list)
    preferred_locations: list[Text] = Field(default_factory=list)
    remote_preference: Literal["any", "remote", "hybrid", "onsite"] = "any"
    employment_types: list[Text] = Field(default_factory=list)
    salary_expectations: SalaryExpectations | None = None
    industries: list[Text] = Field(default_factory=list)
    excluded_companies: list[Text] = Field(default_factory=list)
