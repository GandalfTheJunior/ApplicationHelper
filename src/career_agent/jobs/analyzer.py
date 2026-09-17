"""Analyze declared requirements; do not pretend to extract skills from prose."""

from career_agent.domain.base import Model
from career_agent.domain.job import JobPosting
from career_agent.domain.matching import Category


class AnalyzedRequirement(Model):
    category: Category
    name: str
    level: str | None = None


class JobAnalysis(Model):
    job: JobPosting
    requirements: list[AnalyzedRequirement]
    limitations: list[str]


def analyze_job(job: JobPosting) -> JobAnalysis:
    requirements = (
        [
            AnalyzedRequirement(category="required_skill", name=name)
            for name in job.required_skills
        ]
        + [
            AnalyzedRequirement(category="preferred_skill", name=name)
            for name in job.preferred_skills
        ]
        + [
            AnalyzedRequirement(
                category="language", name=language.name, level=language.level
            )
            for language in job.language_requirements
        ]
    )
    return JobAnalysis(
        job=job,
        requirements=requirements,
        limitations=[
            "Only structured skills and languages are matched; prose is not analyzed.",
            "Seniority, responsibilities and experience alignment require review.",
        ],
    )
