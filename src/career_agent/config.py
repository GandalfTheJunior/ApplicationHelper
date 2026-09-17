"""Resolve local storage without reading or creating personal files."""

import os
from pathlib import Path


def get_data_home() -> Path:
    """An explicit environment path takes precedence; blank values use the default."""
    configured = os.environ.get("CAREER_AGENT_HOME", "").strip()
    return (
        Path(configured).expanduser().resolve()
        if configured
        else Path.home() / ".career-agent"
    )
