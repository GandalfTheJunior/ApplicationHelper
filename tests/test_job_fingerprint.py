import os
import subprocess
import sys

import pytest

from career_agent.domain.candidate import Career
from career_agent.domain.job import JobPosting, job_fingerprint
from career_agent.matching.matcher import match_job


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("company", "Other Example Company"),
        ("title", "Other Example Role"),
        ("location", "Other Example City"),
        ("remote_status", "onsite"),
        ("source_url", "https://jobs.example.invalid/other-job"),
        ("description", "Another fictional job description."),
        ("responsibilities", ["Maintain a fictional service."]),
        ("required_skills", ["Kubernetes"]),
        ("preferred_skills", ["FastAPI"]),
        ("language_requirements", [{"name": "English", "level": "C1"}]),
        ("seniority", "senior"),
        ("employment_type", "part-time"),
    ],
)
def test_fingerprint_changes_for_every_job_field(
    job: JobPosting, field: str, value: object
) -> None:
    data = job.model_dump(mode="json")
    data[field] = value
    assert job_fingerprint(JobPosting.model_validate(data)) != job_fingerprint(job)


def test_equivalent_validated_inputs_have_same_fingerprint() -> None:
    first = JobPosting.model_validate(
        {"title": "  Example Role  ", "required_skills": ["Python", "Python"]}
    )
    second = JobPosting.model_validate(
        {
            "required_skills": ["Python"],
            "title": "Example Role",
            "remote_status": "unknown",
        }
    )
    assert job_fingerprint(first) == job_fingerprint(second)


def test_fingerprint_does_not_depend_on_candidate(
    career: Career, job: JobPosting
) -> None:
    assert (
        match_job(job, career).job_fingerprint
        == match_job(job, Career()).job_fingerprint
    )


@pytest.mark.parametrize("hash_seed", ["1", "42"])
def test_fingerprint_is_stable_across_processes_and_hash_seeds(
    job: JobPosting, hash_seed: str
) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys\n"
            "from career_agent.domain.job import JobPosting, job_fingerprint\n"
            "print(job_fingerprint(JobPosting.model_validate_json(sys.stdin.read())))",
        ],
        input=job.model_dump_json(),
        env={**os.environ, "PYTHONHASHSEED": hash_seed},
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout.strip() == job_fingerprint(job)
