"""Repository management tasks powered by `invoke`.
More information on `invoke` can be found at http://www.pyinvoke.org/.
"""
# pylint: disable=import-outside-toplevel
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from invoke import task

if TYPE_CHECKING:  # pragma: no cover
    from typing import Tuple

    from invoke import Context, Result


REPO_PARENT_DIR = Path(__file__).resolve().parent.parent.resolve()


def update_file(filename: Path, sub_line: "Tuple[str, str]", strip: str = None) -> None:
    """Utility function for tasks to read, update, and write files"""
    lines = [
        re.sub(sub_line[0], sub_line[1], line.rstrip(strip))
        for line in filename.read_text(encoding="utf8").splitlines()
    ]
    filename.write_text("\n".join(lines) + "\n", encoding="utf8")


@task(
    help={
        "version": "Version to set.",
        "package-dir": (
            "Relative path to package dir from the repository root, "
            "e.g. 'src/my_package'."
        ),
        "repo-folder": (
            "The folder name of the repository, wherein the package dir is located. "
            "This defaults to 'main', as this will be used in the callable workflows."
        ),
    }
)
def setver(_, package_dir, version, repo_folder="main"):
    """Sets the specified version of specified Python package."""
    match = re.fullmatch(
        (
            r"v?(?P<version>[0-9]+(\.[0-9]+){2}"  # Major.Minor.Patch
            r"(-[0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*)?"  # pre-release
            r"(\+[0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*)?)"  # build metadata
        ),
        version,
    )
    if not match:
        sys.exit(
            "Error: Please specify version as "
            "'Major.Minor.Patch(-Pre-Release+Build Metadata)' or "
            "'vMajor.Minor.Patch(-Pre-Release+Build Metadata)'"
        )
    version = match.group("version")

    init_file: Path = REPO_PARENT_DIR / repo_folder / package_dir / "__init__.py"
    if not init_file.exists():
        sys.exit(
            "Error: Could not find the Python package's root '__init__.py' file at: "
            f"{init_file}"
        )

    update_file(
        init_file,
        (r'__version__ = (\'|").*(\'|")', f'__version__ = "{version}"'),
    )

    print(f"Bumped version for {package_dir} to {version}.")


@task(
    help={
        "fail-fast": (
            "Fail immediately if an error occurs. Otherwise, print and ignore all "
            "non-critical errors."
        ),
        "repo-folder": (
            "The folder name of the repository, wherein the package dir is located. "
            "This defaults to 'main', as this will be used in the callable workflows."
        ),
    }
)
def update_deps(  # pylint: disable=too-many-branches,too-many-locals,too-many-statements
    context, repo_folder="main", fail_fast=False
):
    """Update dependencies in specified Python package's `pyproject.toml`."""
    import tomlkit

    if TYPE_CHECKING:  # pragma: no cover
        context: "Context" = context

    pyproject_path = REPO_PARENT_DIR / repo_folder / "pyproject.toml"
    if not pyproject_path.exists():
        sys.exit(
            "Error: Could not find the Python package repository's 'pyproject.toml' "
            f"file at: {pyproject_path}"
        )

    pyproject = tomlkit.loads(pyproject_path.read_bytes())

    py_version = re.match(
        r"^.*(?P<version>3\.[0-9]+)$",
        pyproject.get("project", {}).get("requires-python", ""),
    ).group("version")

    already_handled_packages = set()
    updated_packages = {}
    dependencies = pyproject.get("project", {}).get("dependencies", [])
    for optional_deps in (
        pyproject.get("project", {}).get("optional-dependencies", {}).values()
    ):
        dependencies.extend(optional_deps)
    for line in dependencies:
        match = re.match(
            r"^(?P<full_dependency>(?P<package>[a-zA-Z0-9-_]+)\S*) "
            r"(?P<operator>>|<|<=|>=|==|!=|~=)"
            r"(?P<version>[0-9]+(?:\.[0-9]+){0,2})"
            r"(?P<extra_op_ver>(?:,(?:>|<|<=|>=|==|!=|~=)"
            r"[0-9]+(?:\.[0-9]+){0,2})*)$",
            line,
        )
        if match is None:
            msg = f"Could not parse package, operator, and version for line:\n  {line}"
            if fail_fast:
                sys.exit(msg)
            print(msg)
        full_dependency_name = match.group("full_dependency")
        package = match.group("package")
        operator = match.group("operator")
        version = match.group("version")
        extra_op_ver = match.group("extra_op_ver")

        # Skip package if already handled
        if package in already_handled_packages:
            continue

        # Check version from PyPI's online package index
        out: "Result" = context.run(
            f"pip index versions --python-version {py_version} {package}",
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
            if fail_fast:
                sys.exit(msg)
            print(msg)

        # Sanity check
        if package != match.group("package"):
            msg = (
                f"Package name parsed from pyproject.toml ({package!r}) does not match"
                " the name returned from 'pip index versions': "
                f"{match.group('package')!r}"
            )
            if fail_fast:
                sys.exit(msg)
            print(msg)

        latest_version = match.group("version").split(".")
        for index, version_part in enumerate(version.split(".")):
            if version_part != latest_version[index]:
                break
        else:
            already_handled_packages.add(package)
            continue

        # Update pyproject.toml
        updated_version = ".".join(latest_version[: len(version.split("."))])
        escaped_full_dependency_name = full_dependency_name.replace(
            "[", "\["  # pylint: disable=anomalous-backslash-in-string
        ).replace(
            "]", "\]"  # pylint: disable=anomalous-backslash-in-string
        )
        update_file(
            pyproject_path,
            (
                rf'"{escaped_full_dependency_name} {operator}.*"',
                f'"{full_dependency_name} {operator}{updated_version}'
                f'{extra_op_ver if extra_op_ver else ""}"',
            ),
        )
        already_handled_packages.add(package)
        updated_packages[full_dependency_name] = f"{operator}{updated_version}"

    if updated_packages:
        print(
            "Successfully updated the following dependencies:\n"
            + "\n".join(
                f"  {package} ({version}{extra_op_ver if extra_op_ver else ''})"
                for package, version in updated_packages.items()
            )
            + "\n"
        )
    else:
        print("No dependency updates available.")
