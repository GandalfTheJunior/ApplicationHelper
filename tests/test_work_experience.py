from pathlib import Path

import pytest
from pydantic import ValidationError

from career_agent.domain.candidate import Achievement, Career, WorkExperience
from career_agent.domain.job import JobPosting
from career_agent.matching.matcher import match_job
from career_agent.profile.loader import load_career


def test_existing_work_experience_remains_valid() -> None:
    experience = WorkExperience(
        id="example-work", employer="Example Company", title="Example Role"
    )
    assert experience.start_period is None
    assert experience.end_period is None
    assert experience.achievements == []


def test_achievement_metadata_is_optional() -> None:
    achievement = Achievement(
        id="example-achievement", description="Completed the fictional report."
    )
    assert achievement.skill_names == []
    assert achievement.tags == []


def test_period_precision_and_missing_end_are_preserved() -> None:
    experience = WorkExperience(
        id="example-work",
        employer="Example Company",
        title="Example Role",
        start_period="2020",
    )
    assert experience.start_period == "2020"
    assert experience.end_period is None


def test_fictional_example_loads_periods_and_structured_achievements(
    examples: Path,
) -> None:
    career = load_career(examples / "career.example.yaml")
    experience = career.work_experience[0]
    assert experience.start_period == "2020-01"
    assert experience.end_period == "2024-12"
    assert experience.achievements[0].id == "example-reporting-queries"
    assert experience.achievements[0].skill_names == ["PostgreSQL"]
    assert experience.achievements[0].tags == ["internal-reporting"]
    assert Career.model_validate_json(career.model_dump_json()) == career


def test_achievement_prose_and_tags_do_not_create_skill_matches(career: Career) -> None:
    career.work_experience[0].achievements = [
        Achievement(
            id="example-cloud",
            description="Fictional work mentions AWS.",
            skill_names=["AWS"],
            tags=["Kubernetes"],
        )
    ]
    result = match_job(JobPosting(required_skills=["AWS", "Kubernetes"]), career)
    assert result.required_skill_coverage == 0
    assert result.relevant_candidate_evidence == []
    assert [item.requirement for item in result.unsupported_requirements] == [
        "AWS",
        "Kubernetes",
    ]


@pytest.mark.parametrize(
    "payload",
    [
        {"id": "", "description": "Fictional achievement."},
        {"id": "example-achievement", "description": " "},
        {
            "id": "example-achievement",
            "description": "Fictional achievement.",
            "skill_names": [" "],
        },
    ],
)
def test_invalid_achievements_are_rejected(payload: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        Achievement.model_validate(payload)


def test_duplicate_achievement_ids_are_rejected() -> None:
    achievement = Achievement(id="example-achievement", description="Fictional report.")
    with pytest.raises(ValidationError, match="Achievement IDs must be unique"):
        WorkExperience(
            id="example-work",
            employer="Example Company",
            title="Example Role",
            achievements=[achievement, achievement],
        )
