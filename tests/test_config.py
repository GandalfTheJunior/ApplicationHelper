from pathlib import Path

import pytest

from career_agent.config import get_data_home


def test_default_home_does_not_create_files() -> None:
    assert get_data_home() == Path.home() / ".career-agent"
    assert not get_data_home().exists()


def test_environment_override(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "custom-profile"
    monkeypatch.setenv("CAREER_AGENT_HOME", str(target))
    assert get_data_home() == target
    assert not target.exists()


def test_tilde_expansion(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CAREER_AGENT_HOME", "~/custom-profile")
    assert get_data_home() == Path.home() / "custom-profile"


def test_relative_override(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("CAREER_AGENT_HOME", "local-profile")
    assert get_data_home() == tmp_path / "local-profile"


def test_blank_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CAREER_AGENT_HOME", "  ")
    assert get_data_home() == Path.home() / ".career-agent"
