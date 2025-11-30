from os import _exit, environ
from pathlib import Path
from subprocess import Popen

from httpx import Client
from packaging.version import Version

from constants import REPOSITORY_RAW_FS
from logger import logger
from utils import get_version_from_pyproject_toml


class Updater:
    def __init__(self, executable_path: Path):
        self.client = Client(base_url=REPOSITORY_RAW_FS)
        self.executable_path = executable_path
        self.new_executable_path = executable_path.with_suffix(".exe.new")
        self.old_executable_path = executable_path.with_suffix(".exe.old")

    def cleanup(self):
        self.old_executable_path.unlink(missing_ok=True)

    def get_latest_version(self) -> Version:
        res = self.client.get("/pyproject.toml")
        res.raise_for_status()
        version = get_version_from_pyproject_toml(res.text)
        logger.info("Latest version is %s", version)

        return version

    def update(self):
        logger.info("Updating")
        self._download_executable()
        self._swap_executables()
        self._restart()

    def _restart(self):
        logger.debug("Restarting")
        Popen([self.executable_path], env={**environ, "PYINSTALLER_RESET_ENVIRONMENT": "1"})
        _exit(0)

    def _download_executable(self):
        logger.debug("Downloading executable")
        res = self.client.get("/dist/OthoTimer.exe")
        res.raise_for_status()

        with Path(self.new_executable_path).open("wb") as new_file:
            new_file.write(res.read())

    def _swap_executables(self):
        self.executable_path.rename(self.old_executable_path)
        self.new_executable_path.rename(self.executable_path)
