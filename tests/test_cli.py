import json
import subprocess
import sys
from pathlib import Path

import pytest

from career_agent.cli import main


@pytest.mark.parametrize("command", ["analyze", "match", "context"])
def test_cli_sample_commands(
    examples: Path, capsys: pytest.CaptureFixture[str], command: str
) -> None:
    args = [command, str(examples / "job.example.yaml")]
    if command != "analyze":
        args.extend(["--career", str(examples / "career.example.yaml")])
    assert main(args) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    result = json.loads(captured.out)
    if command == "match":
        assert result["required_skill_coverage"] == 1
    elif command == "context":
        assert "identity" not in result
        assert len(result["candidate_evidence"]) == 4
    else:
        assert len(result["requirements"]) == 6


def test_check_all_fictional_profiles(
    examples: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert (
        main(
            [
                "check-profile",
                "--career",
                str(examples / "career.example.yaml"),
                "--identity",
                str(examples / "identity.example.yaml"),
                "--preferences",
                str(examples / "preferences.example.yaml"),
            ]
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out) == {
        "career": "valid",
        "identity": "valid",
        "preferences": "valid",
    }


def test_check_profile_does_not_load_identity(
    examples: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert (
        main(["check-profile", "--career", str(examples / "career.example.yaml")]) == 0
    )
    assert json.loads(capsys.readouterr().out)["identity"] == "not_loaded"


def test_cli_missing_file_returns_two(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["match", str(tmp_path / "missing.yaml")]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Cannot read" in captured.err
    assert "Traceback" not in captured.err


def test_module_entrypoint(examples: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "career_agent",
            "context",
            str(examples / "job.example.yaml"),
            "--career",
            str(examples / "career.example.yaml"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert len(json.loads(result.stdout)["unsupported_requirements"]) == 2
