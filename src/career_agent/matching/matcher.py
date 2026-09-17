from career_agent.domain.base import normalize
from career_agent.domain.candidate import Career, Preferences
from career_agent.domain.job import JobPosting
from career_agent.domain.matching import (
    Alignment,
    Category,
    MatchResult,
    RequirementMatch,
)
from career_agent.jobs.analyzer import analyze_job
from career_agent.profile.evidence import select_evidence


def _location_alignment(job: JobPosting, preferences: Preferences | None) -> Alignment:
    if preferences is None:
        return Alignment(status="unknown", reason="No location preferences supplied.")
    remote = preferences.remote_preference
    if remote == "any" and not preferences.preferred_locations:
        return Alignment(
            status="not_applicable", reason="No location restrictions supplied."
        )
    if (
        remote != "any"
        and job.remote_status != "unknown"
        and remote != job.remote_status
    ):
        return Alignment(
            status="not_aligned", reason="Work arrangement differs from preference."
        )
    # Remote work does not imply permission to work from any country/location.
    if preferences.preferred_locations and job.location:
        if normalize(job.location) not in {
            normalize(p) for p in preferences.preferred_locations
        }:
            return Alignment(
                status="not_aligned",
                reason="Location is not an exact preferred-location match.",
            )
    if (remote != "any" and job.remote_status == "unknown") or (
        preferences.preferred_locations and not job.location
    ):
        return Alignment(
            status="unknown",
            reason="Posting lacks a requested location or work-arrangement field.",
        )
    return Alignment(
        status="aligned", reason="All specified location preferences match exactly."
    )


def match_job(
    job: JobPosting, career: Career, preferences: Preferences | None = None
) -> MatchResult:
    """Name matches only. No synonyms, skill adjacency, or inferred qualifications."""
    evidence = select_evidence(job, career)
    facts = {(fact.kind, normalize(fact.name)): fact for fact in evidence}
    requirements: list[RequirementMatch] = []
    for requirement in analyze_job(job).requirements:
        kind = "language" if requirement.category == "language" else "skill"
        fact = facts.get((kind, normalize(requirement.name)))
        status = "unsupported"
        reason = "No explicitly recorded candidate evidence for this requirement."
        if fact is not None:
            status = "matched"
            reason = "Exact normalized name supported by recorded candidate evidence."
            if requirement.level is not None and (
                fact.level is None
                or normalize(fact.level) != normalize(requirement.level)
            ):
                status = "partial"
                reason = (
                    "Language is evidenced; required proficiency is not an exact match "
                    "and needs review."
                )
        requirements.append(
            RequirementMatch(
                category=requirement.category,
                requirement=requirement.name,
                level=requirement.level,
                status=status,
                reason=reason,
                evidence_ids=[item.id for item in fact.evidence] if fact else [],
            )
        )

    def coverage(category: Category) -> float | None:
        items = [item for item in requirements if item.category == category]
        return (
            sum(item.status == "matched" for item in items) / len(items)
            if items
            else None
        )

    return MatchResult(
        required_skill_coverage=coverage("required_skill"),
        preferred_skill_coverage=coverage("preferred_skill"),
        language_coverage=coverage("language"),
        experience_alignment=Alignment(
            status="unknown",
            reason=(
                "Baseline does not assess seniority, duration, titles "
                "or responsibility alignment."
            ),
        ),
        location_alignment=_location_alignment(job, preferences),
        matched_requirements=[
            item for item in requirements if item.status == "matched"
        ],
        partially_matched_requirements=[
            item for item in requirements if item.status == "partial"
        ],
        unsupported_requirements=[
            item for item in requirements if item.status == "unsupported"
        ],
        relevant_candidate_evidence=evidence,
    )
