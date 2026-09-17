from pathlib import Path
from typing import Protocol

from career_agent.domain.job import JobPosting
from career_agent.loading import load_yaml_model


class JobParser(Protocol):
    """Future text/HTML implementations parse a local source into the same model."""

    def parse(self, source: Path) -> JobPosting: ...


class YamlJobParser:
    def parse(self, source: Path) -> JobPosting:
        return load_yaml_model(source, JobPosting)
