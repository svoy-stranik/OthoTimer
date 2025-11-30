from functools import cache
from tomllib import loads

from packaging.version import Version

from constants import PYPROJECT_TOML_PATH


def get_version_from_pyproject_toml(raw_pyproject_toml: str) -> Version:
    pyproject_toml = loads(raw_pyproject_toml)

    return Version(pyproject_toml["project"]["version"])


@cache
def reveal_project_version() -> Version:
    return get_version_from_pyproject_toml(PYPROJECT_TOML_PATH.read_text(encoding="utf-8"))
