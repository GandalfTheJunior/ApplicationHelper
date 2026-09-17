from career_agent.domain.candidate import Career
from career_agent.domain.job import JobPosting
from career_agent.profile.evidence import select_evidence


def test_only_relevant_evidence_and_original_provenance(
    career: Career, job: JobPosting
) -> None:
    selected = select_evidence(job, career)
    assert [fact.name for fact in selected] == [
        "Python",
        "PostgreSQL",
        "Docker",
        "English",
    ]
    assert selected[0].evidence == career.skills[0].evidence
    assert "FastAPI" not in str([fact.model_dump() for fact in selected])


def test_no_related_technology_inference(career: Career) -> None:
    assert (
        select_evidence(JobPosting(required_skills=["Kubernetes", "AWS"]), career) == []
    )


def test_no_requirements_selects_nothing(career: Career) -> None:
    assert select_evidence(JobPosting(), career) == []


def test_case_whitespace_and_punctuation(career: Career) -> None:
    assert len(select_evidence(JobPosting(required_skills=["  pYtHoN  "]), career)) == 1
    assert select_evidence(JobPosting(required_skills=["Python++"]), career) == []


def test_requirement_in_both_categories_does_not_duplicate_evidence(
    career: Career,
) -> None:
    selected = select_evidence(
        JobPosting(required_skills=["Python"], preferred_skills=["python"]), career
    )
    assert len(selected) == 1


def test_selected_skill_preserves_level_and_years(career: Career) -> None:
    selected = select_evidence(JobPosting(required_skills=["Python"]), career)
    assert selected[0].level == "advanced"
    assert selected[0].years == 4


def test_zero_years_is_preserved(career: Career) -> None:
    career.skills[0].years = 0
    selected = select_evidence(JobPosting(required_skills=["Python"]), career)
    assert selected[0].years == 0
