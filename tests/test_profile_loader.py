from pathlib import Path

import pytest
from pydantic import ValidationError

from career_agent.domain.candidate import Career, Identity, SalaryExpectations, Skill
from career_agent.loading import DataLoadError
from career_agent.profile.loader import load_career, load_identity, load_preferences


def test_identity_and_career_load_separately(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CAREER_AGENT_HOME", str(tmp_path))
    (tmp_path / "career.yaml").write_text("skills: []\n", encoding="utf-8")
    # A broken identity must not stop a valid career from loading.
    (tmp_path / "identity.yaml").write_text("full_name: [", encoding="utf-8")
    assert load_career() == Career()
    with pytest.raises(DataLoadError, match="Malformed YAML"):
        load_identity()
    (tmp_path / "identity.yaml").write_text(
        "full_name: Example Candidate\n", encoding="utf-8"
    )
    (tmp_path / "career.yaml").write_text("skills: [", encoding="utf-8")
    assert load_identity().full_name == "Example Candidate"


@pytest.mark.parametrize(
    ("content", "message"),
    [
        ("skills: [", "Malformed YAML"),
        ("- item", "Expected a YAML mapping"),
        ("", "Expected a YAML mapping"),
        ("skills: wrong-type", "Invalid Career"),
        ("full_name: Example Candidate", "Invalid Career"),
        ("skills: [{name: Python}]", "evidence"),
        ("!!python/object/apply:os.system ['echo unsafe']", "Malformed YAML"),
    ],
)
def test_clear_input_errors(tmp_path: Path, content: str, message: str) -> None:
    path = tmp_path / "career.yaml"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(DataLoadError, match=message):
        load_career(path)


def test_error_does_not_echo_private_values(tmp_path: Path) -> None:
    path = tmp_path / "career.yaml"
    path.write_text("skills: SECRET_EXAMPLE_VALUE", encoding="utf-8")
    with pytest.raises(DataLoadError) as error:
        load_career(path)
    assert "SECRET_EXAMPLE_VALUE" not in str(error.value)


def test_missing_and_non_utf8_file(tmp_path: Path) -> None:
    path = tmp_path / "career.yaml"
    with pytest.raises(DataLoadError, match="Cannot read"):
        load_career(path)
    path.write_bytes(b"\xff")
    with pytest.raises(DataLoadError, match="UTF-8"):
        load_career(path)


def test_optional_identity_and_preferences(examples: Path) -> None:
    assert Identity().model_dump(exclude_none=True) == {}
    assert (
        load_identity(examples / "identity.example.yaml").full_name
        == "Example Candidate"
    )
    preferences = load_preferences(examples / "preferences.example.yaml")
    assert preferences.remote_preference == "remote"
    assert preferences.salary_expectations is not None
    assert preferences.salary_expectations.currency == "EUR"


def test_dangling_evidence_is_rejected(career: Career) -> None:
    data = career.model_dump()
    data["skills"][0]["evidence"][0]["reference"] = "nonexistent-project"
    with pytest.raises(ValidationError, match="reference"):
        Career.model_validate(data)


def test_conflicting_evidence_ids_are_rejected(career: Career) -> None:
    data = career.model_dump()
    data["skills"][1]["evidence"][0]["id"] = data["skills"][0]["evidence"][0]["id"]
    with pytest.raises(ValidationError, match="evidence ID"):
        Career.model_validate(data)


def test_duplicate_names_are_rejected(career: Career) -> None:
    data = career.model_dump()
    extra = data["skills"][0].copy()
    extra["name"] = "  PYTHON  "
    data["skills"].append(extra)
    with pytest.raises(ValidationError, match="unique"):
        Career.model_validate(data)


def test_negative_years_and_inverted_salary_are_rejected(career: Career) -> None:
    skill = career.skills[0].model_dump()
    skill["years"] = -1
    with pytest.raises(ValidationError):
        Skill.model_validate(skill)
    with pytest.raises(ValidationError, match="minimum"):
        SalaryExpectations(minimum=2, maximum=1, currency="EUR")
