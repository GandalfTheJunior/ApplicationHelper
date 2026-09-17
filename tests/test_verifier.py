import pytest

from career_agent.application.verifier import Claim, verify_claim
from career_agent.domain.candidate import Career


def test_verbatim_cited_description_is_supported(career: Career) -> None:
    evidence = career.skills[0].evidence
    result = verify_claim(
        Claim(statement=evidence[0].description, evidence_ids=[evidence[0].id]),
        evidence,
    )
    assert result.status == "supported"


@pytest.mark.parametrize("citations", [[], ["missing"], ["python-api", "missing"]])
def test_missing_or_unknown_citation_is_unsupported(
    career: Career, citations: list[str]
) -> None:
    result = verify_claim(
        Claim(statement="Built backend APIs.", evidence_ids=citations),
        career.skills[0].evidence,
    )
    assert result.status == "unsupported"


@pytest.mark.parametrize(
    "statement", ["I built APIs in Python.", "Managed Kubernetes for ten years."]
)
def test_citation_alone_never_proves_arbitrary_text(
    career: Career, statement: str
) -> None:
    result = verify_claim(
        Claim(statement=statement, evidence_ids=["python-api"]),
        career.skills[0].evidence,
    )
    assert result.status == "uncertain"


def test_conflicting_evidence_is_rejected(career: Career) -> None:
    first = career.skills[0].evidence[0]
    conflicting = first.model_copy(update={"description": "A different claim."})
    with pytest.raises(ValueError, match="Conflicting"):
        verify_claim(
            Claim(statement=first.description, evidence_ids=[first.id]),
            [first, conflicting],
        )
