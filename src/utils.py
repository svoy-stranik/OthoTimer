from functools import cache
from tomllib import load

from constants import PYPROJECT_TOML_PATH


@cache
def reveal_project_version() -> str:
    with PYPROJECT_TOML_PATH.open("rb") as f:
        pyproject_toml = load(f)

    return pyproject_toml["project"]["version"]
