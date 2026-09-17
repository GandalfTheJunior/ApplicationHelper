from pathlib import Path

import pytest
import yaml

from career_agent.domain.candidate import Career, Preferences
from career_agent.domain.job import JobPosting, LanguageRequirement
from career_agent.matching.matcher import match_job
from career_agent.profile.loader import load_career

CASES = yaml.safe_load(
    (Path(__file__).resolve().parents[1] / "evals/matching_cases.yaml").read_text()
)


@pytest.mark.parametrize("case", CASES, ids=[case["id"] for case in CASES])
def test_evaluation_cases(
    case: dict[str, object],
    career: Career,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CAREER_AGENT_HOME", str(tmp_path))
    career_file = tmp_path / "career.yaml"
    career_file.write_text(yaml.safe_dump(career.model_dump()), encoding="utf-8")
    assert not (tmp_path / "identity.yaml").exists()
    result = match_job(JobPosting.model_validate(case["job"]), load_career())
    expected = case["expected"]
    assert result.required_skill_coverage == expected["required_coverage"]
    assert result.preferred_skill_coverage == expected["preferred_coverage"]
    assert [r.requirement for r in result.matched_requirements] == expected["matched"]
    assert [r.requirement for r in result.unsupported_requirements] == expected[
        "unsupported"
    ]
    assert [
        r.name for r in result.relevant_candidate_evidence if r.kind == "skill"
    ] == expected["selected_skills"]


def test_sample_deterministic_without_input_mutation(
    career: Career, job: JobPosting
) -> None:
    before = (career.model_dump_json(), job.model_dump_json())
    first = match_job(job, career)
    assert first.model_dump_json() == match_job(job, career).model_dump_json()
    assert before == (career.model_dump_json(), job.model_dump_json())
    assert first.required_skill_coverage == 1
    assert first.preferred_skill_coverage == pytest.approx(1 / 3)
    assert first.language_coverage == 1
    assert first.experience_alignment.status == "unknown"


def test_duplicate_skills_preserve_order_and_do_not_inflate_coverage(
    career: Career,
) -> None:
    job = JobPosting(required_skills=["Python", "AWS", "  PYTHON "])
    assert job.required_skills == ["Python", "AWS"]
    assert match_job(job, career).required_skill_coverage == 0.5


def test_empty_career_and_empty_posting() -> None:
    result = match_job(JobPosting(), Career())
    assert result.required_skill_coverage is None
    assert result.preferred_skill_coverage is None
    assert result.language_coverage is None
    assert result.matched_requirements == []


def test_required_preferred_overlap_is_counted_only_as_required(career: Career) -> None:
    job = JobPosting(required_skills=["  PYTHON  "], preferred_skills=["python", "AWS"])
    result = match_job(job, career)
    assert result.required_skill_coverage == 1
    assert result.preferred_skill_coverage == 0
    assert [
        (item.category, item.requirement) for item in result.matched_requirements
    ] == [("required_skill", "PYTHON")]
    assert [item.requirement for item in result.unsupported_requirements] == ["AWS"]


def test_only_overlapping_preferred_skills_means_not_applicable(career: Career) -> None:
    result = match_job(
        JobPosting(required_skills=["Python"], preferred_skills=[" python "]), career
    )
    assert result.required_skill_coverage == 1
    assert result.preferred_skill_coverage is None


@pytest.mark.parametrize(
    ("language", "level", "status"),
    [
        ("English", "B2", "matched"),
        ("English", None, "matched"),
        ("English", "C1", "partial"),
        ("English", "B1", "partial"),
        ("French", "B2", "unsupported"),
    ],
)
def test_language_support_is_conservative(
    career: Career, language: str, level: str | None, status: str
) -> None:
    result = match_job(
        JobPosting(
            language_requirements=[LanguageRequirement(name=language, level=level)]
        ),
        career,
    )
    all_requirements = (
        result.matched_requirements
        + result.partially_matched_requirements
        + result.unsupported_requirements
    )
    assert all_requirements[0].status == status
    assert result.language_coverage == (1.0 if status == "matched" else 0.0)


@pytest.mark.parametrize(
    ("posting", "preferences", "status"),
    [
        ({}, None, "unknown"),
        ({}, {}, "not_applicable"),
        ({"remote_status": "remote"}, {"remote_preference": "remote"}, "aligned"),
        ({"remote_status": "onsite"}, {"remote_preference": "remote"}, "not_aligned"),
        ({}, {"remote_preference": "remote"}, "unknown"),
        (
            {"location": "Example City"},
            {"preferred_locations": ["EXAMPLE CITY"]},
            "aligned",
        ),
        (
            {"location": "Elsewhere"},
            {"preferred_locations": ["Example City"]},
            "not_aligned",
        ),
        (
            {"remote_status": "remote"},
            {"preferred_locations": ["Example City"]},
            "unknown",
        ),
    ],
)
def test_location_alignment(
    posting: dict[str, object], preferences: dict[str, object] | None, status: str
) -> None:
    result = match_job(
        JobPosting.model_validate(posting),
        Career(),
        Preferences.model_validate(preferences) if preferences is not None else None,
    )
    assert result.location_alignment.status == status
