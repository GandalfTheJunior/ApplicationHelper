from career_agent.domain.base import normalize
from career_agent.domain.candidate import Identity
from career_agent.domain.job import JobPosting
from career_agent.domain.matching import CandidateEvidence, MatchResult
from career_agent.jobs.analyzer import analyze_job


def build_application_context(
    job: JobPosting,
    match: MatchResult,
    candidate_evidence: list[CandidateEvidence],
    *,
    identity: Identity | None = None,
) -> dict[str, object]:
    """Include only selected facts approved by the match, never the whole profile.

    Passing identity is an explicit opt-in for a future final artifact renderer.
    This function performs no loading, storage, or network communication.
    """
    requirements = (
        match.matched_requirements
        + match.partially_matched_requirements
        + match.unsupported_requirements
    )
    expected = {
        (r.category, normalize(r.name), r.level) for r in analyze_job(job).requirements
    }
    actual = {(r.category, normalize(r.requirement), r.level) for r in requirements}
    if expected != actual or len(requirements) != len(expected):
        raise ValueError("Match requirements do not correspond to the supplied job")
    allowed = {
        ("language" if r.category == "language" else "skill", normalize(r.requirement))
        for r in match.matched_requirements + match.partially_matched_requirements
    }
    selected: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    for fact in candidate_evidence:
        key = (fact.kind, normalize(fact.name))
        if (
            key in allowed
            and key not in seen
            and fact in match.relevant_candidate_evidence
        ):
            selected.append(fact.model_dump(mode="json", exclude_none=True))
            seen.add(key)
    context: dict[str, object] = {
        # Omit source boilerplate/description; retain structured generation needs.
        "job": job.model_dump(
            mode="json", exclude_none=True, exclude={"description", "source_url"}
        ),
        "candidate_evidence": selected,
        "unsupported_requirements": [
            r.model_dump(mode="json", exclude_none=True)
            for r in match.unsupported_requirements
        ],
        "partially_matched_requirements": [
            r.model_dump(mode="json", exclude_none=True)
            for r in match.partially_matched_requirements
        ],
        "limitations": analyze_job(job).limitations,
    }
    if identity is not None:
        context["identity"] = identity.model_dump(mode="json", exclude_none=True)
    return context
