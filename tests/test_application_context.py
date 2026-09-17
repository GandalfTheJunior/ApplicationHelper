import json

import pytest

from career_agent.application.context import build_application_context
from career_agent.domain.candidate import Career, Identity
from career_agent.domain.job import JobPosting, LanguageRequirement
from career_agent.domain.matching import CandidateEvidence
from career_agent.matching.matcher import match_job


def test_context_has_only_relevant_facts_and_no_identity(
    career: Career, job: JobPosting
) -> None:
    match = match_job(job, career)
    context = build_application_context(job, match, match.relevant_candidate_evidence)
    assert "identity" not in context
    encoded = json.dumps(context)
    for field in (
        "full_name",
        "email",
        "phone",
        "address",
        "years",
        "education",
        "certifications",
    ):
        assert field not in encoded
    assert "FastAPI" not in encoded
    assert "description" not in context["job"]
    assert "source_url" not in context["job"]
    assert [r["requirement"] for r in context["unsupported_requirements"]] == [
        "Kubernetes",
        "AWS",
    ]


def test_identity_requires_explicit_opt_in(career: Career, job: JobPosting) -> None:
    match = match_job(job, career)
    context = build_application_context(
        job,
        match,
        match.relevant_candidate_evidence,
        identity=Identity(full_name="Example Candidate"),
    )
    assert context["identity"] == {"full_name": "Example Candidate"}


def test_unrelated_or_modified_evidence_cannot_enter_context(
    career: Career, job: JobPosting
) -> None:
    match = match_job(job, career)
    unrelated = CandidateEvidence(
        kind="skill", name="FastAPI", evidence=career.skills[1].evidence
    )
    changed = match.relevant_candidate_evidence[0].model_copy(deep=True)
    changed.evidence[0].description = "Invented outcome not present in the profile."
    context = build_application_context(
        job, match, [unrelated, changed, *match.relevant_candidate_evidence]
    )
    encoded = json.dumps(context)
    assert "FastAPI" not in encoded
    assert "Invented outcome" not in encoded
    assert len(context["candidate_evidence"]) == 4


def test_context_preserves_partial_language_warning(career: Career) -> None:
    job = JobPosting(
        language_requirements=[LanguageRequirement(name="English", level="C1")]
    )
    match = match_job(job, career)
    context = build_application_context(job, match, match.relevant_candidate_evidence)
    assert context["candidate_evidence"][0]["level"] == "B2"
    assert context["partially_matched_requirements"][0]["level"] == "C1"


def test_context_rejects_match_for_different_requirements(
    career: Career, job: JobPosting
) -> None:
    match = match_job(job, career)
    with pytest.raises(ValueError, match="do not correspond"):
        build_application_context(
            JobPosting(required_skills=["AWS"]),
            match,
            match.relevant_candidate_evidence,
        )
