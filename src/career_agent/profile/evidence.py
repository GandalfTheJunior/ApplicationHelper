"""Select declared facts by exact normalized name, never by inferred synonyms."""

from typing import Protocol

from career_agent.domain.base import normalize
from career_agent.domain.candidate import Career
from career_agent.domain.job import JobPosting
from career_agent.domain.matching import CandidateEvidence


class EvidenceSelector(Protocol):
    def __call__(self, job: JobPosting, career: Career) -> list[CandidateEvidence]: ...


def select_evidence(job: JobPosting, career: Career) -> list[CandidateEvidence]:
    skill_names = {
        normalize(name) for name in job.required_skills + job.preferred_skills
    }
    language_names = {normalize(item.name) for item in job.language_requirements}
    result = [
        CandidateEvidence(kind="skill", name=skill.name, evidence=skill.evidence)
        for skill in career.skills
        if normalize(skill.name) in skill_names
    ]
    result.extend(
        CandidateEvidence(
            kind="language",
            name=language.name,
            level=language.level,
            evidence=language.evidence,
        )
        for language in career.languages
        if normalize(language.name) in language_names
    )
    return result
