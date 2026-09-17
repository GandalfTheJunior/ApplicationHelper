from pathlib import Path

from career_agent.config import get_data_home
from career_agent.domain.candidate import Career, Identity, Preferences
from career_agent.loading import load_yaml_model


def load_career(path: Path | None = None) -> Career:
    return load_yaml_model(
        path if path is not None else get_data_home() / "career.yaml", Career
    )


def load_identity(path: Path | None = None) -> Identity:
    """Explicit opt-in; matching never calls this function."""
    return load_yaml_model(
        path if path is not None else get_data_home() / "identity.yaml", Identity
    )


def load_preferences(path: Path | None = None) -> Preferences:
    return load_yaml_model(
        path if path is not None else get_data_home() / "preferences.yaml", Preferences
    )
