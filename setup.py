"""Mock setup.py for use with reusable workflows."""
from pathlib import Path

from setuptools import setup

setup(
    name="ci-cd",
    install_requires=Path("requirements.txt").read_text(encoding="utf8").splitlines(),
    extras_require={
        "dev": Path("requirements_dev.txt").read_text(encoding="utf8").splitlines(),
        "docs": Path("requirements_docs.txt").read_text(encoding="utf8").splitlines(),
    },
)
