import json
from pathlib import Path

from jsonschema import Draft202012Validator

from career_agent.domain.candidate import Career
from career_agent.domain.job import JobPosting
from career_agent.domain.matching import MatchResult
from career_agent.matching.matcher import match_job


def test_schemas_match_models_and_validate_sample_flow(
    career: Career, job: JobPosting
) -> None:
    root = Path(__file__).resolve().parents[1]
    for name, model, instance in (
        ("candidate", Career, career),
        ("job", JobPosting, job),
        ("match", MatchResult, match_job(job, career)),
    ):
        schema = json.loads((root / "schemas" / f"{name}.schema.json").read_text())
        expected = model.model_json_schema()
        expected["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        assert schema == expected
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(instance.model_dump(mode="json"))
