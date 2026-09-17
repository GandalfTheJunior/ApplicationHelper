from pathlib import Path

import pytest

from career_agent.domain.candidate import Career
from career_agent.domain.job import JobPosting
from career_agent.jobs.parser import YamlJobParser
from career_agent.profile.loader import load_career

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def isolated_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path / "fake-home"))
    monkeypatch.delenv("CAREER_AGENT_HOME", raising=False)


@pytest.fixture
def examples() -> Path:
    return ROOT / "examples"


@pytest.fixture
def career(examples: Path) -> Career:
    return load_career(examples / "career.example.yaml")


@pytest.fixture
def job(examples: Path) -> JobPosting:
    return YamlJobParser().parse(examples / "job.example.yaml")
