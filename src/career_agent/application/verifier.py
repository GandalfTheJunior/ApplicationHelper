"""A provenance check, NOT production-ready natural-language claim verification.

Future workflow: split generated text into atomic factual claims, retrieve their
candidate evidence, and classify each as supported / unsupported / uncertain.
Only a verbatim evidence description is supported here. Even semantically valid
paraphrases are uncertain and need human review. Candidate records themselves
are user-supplied assertions, not independently verified credentials.
"""

from typing import Literal, Protocol

from pydantic import Field

from career_agent.domain.base import Model, Text
from career_agent.domain.candidate import Evidence


class Claim(Model):
    statement: Text
    evidence_ids: list[Text] = Field(default_factory=list)


class VerificationResult(Model):
    claim: Claim
    status: Literal["supported", "unsupported", "uncertain"]
    reason: Text


class ClaimVerifier(Protocol):
    def __call__(
        self, claim: Claim, evidence: list[Evidence]
    ) -> VerificationResult: ...


def verify_claim(claim: Claim, evidence: list[Evidence]) -> VerificationResult:
    index = {item.id: item for item in evidence}
    if any(index[item.id] != item for item in evidence):
        raise ValueError("Conflicting evidence IDs cannot be verified")
    if not claim.evidence_ids or any(key not in index for key in claim.evidence_ids):
        return VerificationResult(
            claim=claim,
            status="unsupported",
            reason="Claim has no citation or cites evidence absent from the context.",
        )
    if any(claim.statement == index[key].description for key in claim.evidence_ids):
        return VerificationResult(
            claim=claim,
            status="supported",
            reason="Statement exactly copies a cited candidate evidence description.",
        )
    return VerificationResult(
        claim=claim,
        status="uncertain",
        reason="Citations alone cannot establish support; review this claim.",
    )
