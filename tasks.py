from os import system
from pathlib import Path
from shutil import rmtree

from invoke.context import Context
from invoke.tasks import task


@task(default=True)
def run(_: Context):
    system("uv run python src/main.py")


@task
def lint(_: Context):
    system("uv run ruff check")


@task
def format(_: Context):
    system("uv run ruff format")


@task(pre=[format])
def lintfix(_: Context):
    system("uv run ruff check --fix")


@task
def build(_: Context):
    rmtree("dist", ignore_errors=True)

    system(
        """
            uv run pyinstaller \
                -Fn OthoTimer \
                --add-binary assets/icon.ico;assets \
                --add-binary pyproject.toml;. \
                -i assets/icon.ico \
                -p src \
                src/main.py
        """
    )

    Path("OthoTimer.spec").unlink()
    rmtree("build", ignore_errors=True)
