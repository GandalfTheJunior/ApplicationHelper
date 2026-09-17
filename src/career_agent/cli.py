"""Small argparse CLI; JSON goes to stdout, safe errors go to stderr."""

import argparse
import json
import sys
from pathlib import Path

from career_agent.application.context import build_application_context
from career_agent.domain.base import Model
from career_agent.jobs.analyzer import analyze_job
from career_agent.jobs.parser import YamlJobParser
from career_agent.loading import DataLoadError
from career_agent.matching.matcher import match_job
from career_agent.profile.loader import load_career, load_identity, load_preferences


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Local evidence-first career application agent"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser(
        "check-profile", help="Validate career data; identity/preferences are opt-in"
    )
    check.add_argument("--career", type=Path)
    check.add_argument(
        "--identity", type=Path, help="Explicitly validate this identity file"
    )
    check.add_argument("--preferences", type=Path)
    analyze = commands.add_parser("analyze", help="Analyze a structured YAML posting")
    analyze.add_argument("job", type=Path)
    for name in ("match", "context"):
        command = commands.add_parser(name, help=f"Build deterministic {name} JSON")
        command.add_argument("job", type=Path)
        command.add_argument("--career", type=Path)
        command.add_argument("--preferences", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result: Model | dict[str, object]
        if args.command == "check-profile":
            load_career(args.career)
            if args.identity is not None:
                load_identity(args.identity)
            if args.preferences is not None:
                load_preferences(args.preferences)
            result = {
                "career": "valid",
                "identity": "valid" if args.identity is not None else "not_loaded",
                "preferences": "valid"
                if args.preferences is not None
                else "not_loaded",
            }
        else:
            job = YamlJobParser().parse(args.job)
            if args.command == "analyze":
                result = analyze_job(job)
            else:
                career = load_career(args.career)
                preferences = (
                    load_preferences(args.preferences)
                    if args.preferences is not None
                    else None
                )
                match = match_job(job, career, preferences)
                result = (
                    match
                    if args.command == "match"
                    else build_application_context(
                        job, match, match.relevant_candidate_evidence
                    )
                )
    except (DataLoadError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    if isinstance(result, Model):
        print(result.model_dump_json(indent=2))
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0
