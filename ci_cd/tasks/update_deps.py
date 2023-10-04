"""`update_deps` task.

Update dependencies in a `pyproject.toml` file.
"""
# pylint: disable=duplicate-code
from __future__ import annotations

import logging
import re
import sys
from collections import namedtuple
from pathlib import Path
from typing import TYPE_CHECKING

import tomlkit
from invoke import task

from ci_cd.exceptions import CICDException, InputError
from ci_cd.utils import (
    Emoji,
    ignore_version,
    parse_ignore_entries,
    parse_ignore_rules,
    update_file,
)

if TYPE_CHECKING:  # pragma: no cover
    from typing import Literal

    from invoke import Context, Result


LOGGER = logging.getLogger(__file__)
LOGGER.setLevel(logging.DEBUG)


@task(
    help={
        "fail-fast": (
            "Fail immediately if an error occurs. Otherwise, print and ignore all "
            "non-critical errors."
        ),
        "root-repo-path": (
            "A resolvable path to the root directory of the repository folder."
        ),
        "pre-commit": "Whether or not this task is run as a pre-commit hook.",
        "ignore": (
            "Ignore-rules based on the `ignore` config option of Dependabot. It "
            "should be of the format: key=value...key=value, i.e., an ellipsis "
            "(`...`) separator and then equal-sign-separated key/value-pairs. "
            "Alternatively, the `--ignore-separator` can be set to something else to "
            "overwrite the ellipsis. The only supported keys are: `dependency-name`, "
            "`versions`, and `update-types`. Can be supplied multiple times per "
            "`dependency-name`."
        ),
        "ignore-separator": (
            "Value to use instead of ellipsis (`...`) as a separator in `--ignore` "
            "key/value-pairs."
        ),
    },
    iterable=["ignore"],
)
def update_deps(  # pylint: disable=too-many-branches,too-many-locals,too-many-statements
    context,
    root_repo_path=".",
    fail_fast=False,
    pre_commit=False,
    ignore=None,
    ignore_separator="...",
):
    """Update dependencies in specified Python package's `pyproject.toml`."""
    if TYPE_CHECKING:  # pragma: no cover
        context: "Context" = context  # type: ignore[no-redef]
        root_repo_path: str = root_repo_path  # type: ignore[no-redef]
        fail_fast: bool = fail_fast  # type: ignore[no-redef]
        pre_commit: bool = pre_commit  # type: ignore[no-redef]
        ignore_separator: str = ignore_separator  # type: ignore[no-redef]

    if not ignore:
        ignore: list[str] = []  # type: ignore[no-redef]

    VersionSpec = namedtuple(
        "VersionSpec",
        [
            "full_dependency",
            "package",
            "url_version",
            "operator",
            "version",
            "extra_operator_version",
            "environment_marker",
        ],
    )

    try:
        ignore_rules = parse_ignore_entries(ignore, ignore_separator)
    except InputError as exc:
        sys.exit(
            f"{Emoji.CROSS_MARK.value} Error: Could not parse ignore options.\n"
            f"Exception: {exc}"
        )
    LOGGER.debug("Parsed ignore rules: %s", ignore_rules)

    if pre_commit and root_repo_path == ".":
        # Use git to determine repo root
        result: "Result" = context.run("git rev-parse --show-toplevel", hide=True)
        root_repo_path = result.stdout.strip("\n")

    pyproject_path = Path(root_repo_path).resolve() / "pyproject.toml"
    if not pyproject_path.exists():
        sys.exit(
            f"{Emoji.CROSS_MARK.value} Error: Could not find the Python package "
            f"repository's 'pyproject.toml' file at: {pyproject_path}"
        )

    pyproject = tomlkit.loads(pyproject_path.read_bytes())

    match = re.match(
        r"^.*(?P<version>3\.[0-9]+)$",
        pyproject.get("project", {}).get("requires-python", ""),
    )
    if not match:
        raise CICDException(
            "No minimum Python version requirement given in pyproject.toml!"
        )
    py_version = match.group("version")

    already_handled_packages = set()
    updated_packages = {}
    dependencies = pyproject.get("project", {}).get("dependencies", [])
    for optional_deps in (
        pyproject.get("project", {}).get("optional-dependencies", {}).values()
    ):
        dependencies.extend(optional_deps)

    error = False
    for line in dependencies:
        match = re.match(
            r"^(?P<full_dependency>(?P<package>[a-zA-Z0-9_.-]+)(?:\s*\[.*\])?)\s*"
            r"(?:"
            r"(?P<url_version>@\s*\S+)|"
            r"(?P<operator>>|<|<=|>=|==|!=|~=)\s*"
            r"(?P<version>[0-9]+(?:\.[0-9]+){0,2})"
            r")?\s*"
            r"(?P<extra_operator_version>(?:,(?:>|<|<=|>=|==|!=|~=)\s*"
            r"[0-9]+(?:\.[0-9]+){0,2}\s*)+)*"
            r"(?P<environment_marker>;.+)*$",
            line,
        )
        if match is None:
            msg = (
                f"Could not parse package and version specification for line:\n  {line}"
            )
            LOGGER.warning(msg)
            if fail_fast:
                sys.exit(f"{Emoji.CROSS_MARK.value} {msg}")
            print(msg)
            error = True
            continue

        version_spec = VersionSpec(**match.groupdict())
        LOGGER.debug("version_spec: %s", version_spec)

        # Skip package if already handled
        if version_spec.package in already_handled_packages:
            continue

        # Skip URL versioned dependencies
        if version_spec.url_version:
            msg = (
                f"Dependency {version_spec.full_dependency!r} is pinned to a URL and "
                "will be skipped."
            )
            LOGGER.info(msg)
            print(msg)
            continue

        # Skip and warn if package is not version-restricted
        if not version_spec.operator and not version_spec.url_version:
            msg = (
                f"Dependency {version_spec.full_dependency!r} is not version "
                "restricted and will be skipped. Consider adding version restrictions."
            )
            LOGGER.warning(msg)
            print(msg)
            continue

        # Check version from PyPI's online package index
        out: "Result" = context.run(
            f"pip index versions --python-version {py_version} {version_spec.package}",
            hide=True,
        )
        package_latest_version_line = out.stdout.split(sep="\n", maxsplit=1)[0]
        match = re.match(
            r"(?P<package>[a-zA-Z0-9-_]+) \((?P<version>[0-9]+(?:\.[0-9]+){0,2})\)",
            package_latest_version_line,
        )
        if match is None:
            msg = (
                "Could not parse package and version from 'pip index versions' output "
                f"for line:\n  {package_latest_version_line}"
            )
            LOGGER.warning(msg)
            if fail_fast:
                sys.exit(f"{Emoji.CROSS_MARK.value} {msg}")
            print(msg)
            already_handled_packages.add(version_spec.package)
            error = True
            continue

        # Sanity check
        if version_spec.package != match.group("package"):
            msg = (
                f"Package name parsed from pyproject.toml ({version_spec.package!r}) "
                "does not match the name returned from 'pip index versions': "
                f"{match.group('package')!r}"
            )
            LOGGER.warning(msg)
            if fail_fast:
                sys.exit(f"{Emoji.CROSS_MARK.value} {msg}")
            print(msg)
            already_handled_packages.add(version_spec.package)
            error = True
            continue

        # Check whether pyproject.toml already uses the latest version
        latest_version = match.group("version").split(".")
        for index, version_part in enumerate(version_spec.version.split(".")):
            if version_part != latest_version[index]:
                break
        else:
            already_handled_packages.add(version_spec.package)
            continue

        # Apply ignore rules
        if version_spec.package in ignore_rules or "*" in ignore_rules:
            versions: "list[dict[Literal['operator', 'version'], str]]" = []
            update_types: "dict[Literal['version-update'], list[Literal['major', 'minor', 'patch']]]" = (  # pylint: disable=line-too-long
                {}
            )

            if "*" in ignore_rules:
                versions, update_types = parse_ignore_rules(ignore_rules["*"])

            if version_spec.package in ignore_rules:
                parsed_rules = parse_ignore_rules(ignore_rules[version_spec.package])

                versions.extend(parsed_rules[0])
                update_types.update(parsed_rules[1])

            LOGGER.debug(
                "Ignore rules:\nversions: %s\nupdate_types: %s", versions, update_types
            )

            if ignore_version(
                current=version_spec.version.split("."),
                latest=latest_version,
                version_rules=versions,
                semver_rules=update_types,
            ):
                already_handled_packages.add(version_spec.package)
                continue

        if not error:
            # Update pyproject.toml
            updated_version = ".".join(
                latest_version[: len(version_spec.version.split("."))]
            )
            escaped_full_dependency_name = version_spec.full_dependency.replace(
                "[", r"\["
            ).replace("]", r"\]")
            update_file(
                pyproject_path,
                (
                    rf'"{escaped_full_dependency_name} {version_spec.operator}.*"',
                    f'"{version_spec.full_dependency} '
                    f"{version_spec.operator}{updated_version}"
                    f'{version_spec.extra_operator_version if version_spec.extra_operator_version else ""}'  # pylint: disable=line-too-long
                    f'{version_spec.environment_marker if version_spec.environment_marker else ""}"',  # pylint: disable=line-too-long
                ),
            )
            already_handled_packages.add(version_spec.package)
            updated_packages[version_spec.full_dependency] = (
                f"{version_spec.operator}{updated_version}"
                f"{version_spec.extra_operator_version if version_spec.extra_operator_version else ''}"  # pylint: disable=line-too-long
                f"{' ' + version_spec.environment_marker if version_spec.environment_marker else ''}"  # pylint: disable=line-too-long
            )

    if error:
        sys.exit(
            f"{Emoji.CROSS_MARK.value} Errors occurred! See printed statements above."
        )

    if updated_packages:
        print(
            f"{Emoji.PARTY_POPPER.value} Successfully updated the following "
            "dependencies:\n"
            + "\n".join(
                f"  {package} ({version})"
                for package, version in updated_packages.items()
            )
            + "\n"
        )
    else:
        print(f"{Emoji.CHECK_MARK.value} No dependency updates available.")
