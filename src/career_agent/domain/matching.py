"""Explainable matching results and a minimal evidence transfer object."""

from typing import Literal

from pydantic import Field

from career_agent.domain.base import Model, Text
from career_agent.domain.candidate import Evidence

Category = Literal["required_skill", "preferred_skill", "language"]


class CandidateEvidence(Model):
    kind: Literal["skill", "language"]
    name: Text
    level: Text | None = None
    evidence: list[Evidence] = Field(min_length=1)


class RequirementMatch(Model):
    category: Category
    requirement: Text
    level: Text | None = None
    status: Literal["matched", "partial", "unsupported"]
    reason: Text
    evidence_ids: list[Text] = Field(default_factory=list)


class Alignment(Model):
    status: Literal["aligned", "not_aligned", "unknown", "not_applicable"]
    reason: Text


class MatchResult(Model):
    required_skill_coverage: float | None = Field(default=None, ge=0, le=1)
    preferred_skill_coverage: float | None = Field(default=None, ge=0, le=1)
    language_coverage: float | None = Field(default=None, ge=0, le=1)
    experience_alignment: Alignment
    location_alignment: Alignment
    matched_requirements: list[RequirementMatch] = Field(default_factory=list)
    partially_matched_requirements: list[RequirementMatch] = Field(default_factory=list)
    unsupported_requirements: list[RequirementMatch] = Field(default_factory=list)
    relevant_candidate_evidence: list[CandidateEvidence] = Field(default_factory=list)
