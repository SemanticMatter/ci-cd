"""Test `ci_cd.tasks.update_deps()`."""
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path


def test_update_deps(tmp_path: "Path", caplog: pytest.LogCaptureFixture) -> None:
    """Check update_deps runs with defaults."""
    import re

    from invoke import MockContext

    from ci_cd.tasks.update_deps import update_deps

    original_dependencies = {
        "invoke": "1.7",
        "tomlkit": "0.11.4",
        "mike": "1.1",
        "pytest": "7.1",
        "pytest-cov": "3.0",
        "pre-commit": "2.20",
        "pylint": "2.13",
    }

    pyproject_file = tmp_path / "pyproject.toml"
    pyproject_file.write_text(
        data=f"""
[project]
requires-python = "~=3.7"

dependencies = [
    "invoke ~={original_dependencies['invoke']}",
    "tomlkit[test,docs] ~={original_dependencies['tomlkit']}",
]

[project.optional-dependencies]
docs = [
    "mike >={original_dependencies['mike']},<3",
]
testing = [
    "pytest ~={original_dependencies['pytest']}",
    "pytest-cov ~={original_dependencies['pytest-cov']},!=3.1",
]
dev = [
    "mike >={original_dependencies['mike']},<3",
    "pytest ~={original_dependencies['pytest']}",
    "pytest-cov ~={original_dependencies['pytest-cov']},!=3.1",
    # "pre-commit ~={original_dependencies['pre-commit']},!=2.21.*",
    "pylint ~={original_dependencies['pylint']}",
]

# List from https://peps.python.org/pep-0508/#complete-grammar
pep_508 = [
    "A",
    "A.B-C_D",
    "aa",
    "name",
    "name1<=1",
    "name2>=3",
    "name3>=3,<2",
    "name4@http://foo.com",
    "name5 [fred,bar] @ http://foo.com ; python_version=='2.7'",
    "name6[quux, strange];python_version<'2.7' and platform_version=='2'",
    "name7; os_name=='a' or os_name=='b'",
    # Should parse as (a and b) or c
    "name8; os_name=='a' and os_name=='b' or os_name=='c'",
    # Overriding precedence -> a and (b or c)
    "name9; os_name=='a' and (os_name=='b' or os_name=='c')",
    # should parse as a or (b and c)
    "name10; os_name=='a' or os_name=='b' and os_name=='c'",
    # Overriding precedence -> (a or b) and c
    "name11; (os_name=='a' or os_name=='b') and os_name=='c'",
]
""",
        encoding="utf8",
    )

    context = MockContext(
        run={
            **{
                re.compile(r".*invoke$"): "invoke (1.7.1)\n",
                re.compile(r".*tomlkit$"): "tomlkit (1.0.0)",
                re.compile(r".*mike$"): "mike (1.1.1)",
                re.compile(r".*pytest$"): "pytest (7.1.0)",
                re.compile(r".*pytest-cov$"): "pytest-cov (3.1.5)",
                re.compile(r".*pre-commit$"): "pre-commit (2.21.5)",
                re.compile(r".*pylint$"): "pylint (2.14.0)",
                re.compile(r".* A$"): "A (1.2.3)",
                re.compile(r".*A.B-C_D$"): "A.B-C_D (1.2.3)",
                re.compile(r".*aa$"): "aa (1.2.3)",
                re.compile(r".*name$"): "name (1.2.3)",
            },
            **{re.compile(rf".*name{i}$"): f"name{i} (3.2.1)" for i in range(1, 12)},
        }
    )

    # Expected changes:
    # - Extras should be sorted alphabetically (tomlkit).
    # - Original white space between name and specifiers should be respected
    #   (pep_508 vs. the rest)
    # - All name# with a version specifier should be updated to include the latest
    #   version (explicit change in name1)
    # - Similar formatting, even if the dependency is otherwise skipped
    #   (name4 to name11)
    # - Acknowledge that !=3.1 expands to !=3.1.0, so 3.1.5 is allowed (pytest-cov)
    # - TODO: Acknowledge that !=2.21.* includes not wanting *all* sub-versions of 2.21,
    #   so 2.21.5 is excluded and should not be part of the updated specifier set
    #   (pre-commit)
    expected_updated_pyproject_file = f"""
[project]
requires-python = "~=3.7"

dependencies = [
    "invoke ~={original_dependencies['invoke']}",
    "tomlkit[docs,test] >={original_dependencies['tomlkit']},<2",
]

[project.optional-dependencies]
docs = [
    "mike >={original_dependencies['mike']},<3",
]
testing = [
    "pytest ~={original_dependencies['pytest']}",
    "pytest-cov ~=3.1,!=3.1",
]
dev = [
    "mike >={original_dependencies['mike']},<3",
    "pytest ~={original_dependencies['pytest']}",
    "pytest-cov ~=3.1,!=3.1",
    # "pre-commit ~={original_dependencies['pre-commit']},!=2.21.*",
    "pylint ~=2.14",
]

# List from https://peps.python.org/pep-0508/#complete-grammar
pep_508 = [
    "A",
    "A.B-C_D",
    "aa",
    "name",
    "name1<=3",
    "name2>=3",
    "name3>=3,<2",
    "name4@ http://foo.com",
    "name5[bar,fred] @ http://foo.com ; python_version == '2.7'",
    "name6[quux,strange]; python_version < '2.7' and platform_version == '2'",
    "name7; os_name == 'a' or os_name == 'b'",
    # Should parse as (a and b) or c
    "name8; os_name == 'a' and os_name == 'b' or os_name == 'c'",
    # Overriding precedence -> a and (b or c)
    "name9; os_name == 'a' and (os_name == 'b' or os_name == 'c')",
    # should parse as a or (b and c)
    "name10; os_name == 'a' or os_name == 'b' and os_name == 'c'",
    # Overriding precedence -> (a or b) and c
    "name11; (os_name == 'a' or os_name == 'b') and os_name == 'c'",
]
"""

    update_deps(
        context,
        root_repo_path=str(tmp_path),
    )

    updated_pyproject_file = pyproject_file.read_text(encoding="utf8")

    assert updated_pyproject_file == expected_updated_pyproject_file

    # Check the non-version restricted packages are skipped with a message
    for package_name in ["A", "A.B-C_D", "aa", "name"] + [
        f"name{i}" for i in range(6, 12)
    ]:
        assert (
            f"{package_name!r} is not version restricted and will be skipped."
            in caplog.text
        )

    # Check the URL pinned packages are skipped with a message
    for package_name in ["name4", "name5"]:
        assert f"{package_name!r} is pinned to a URL and will be skipped" in caplog.text

    for package_name in ["invoke", "mike", "pytest"]:
        assert f"Package {package_name!r} is already up-to-date" in caplog.text


@pytest.mark.parametrize(
    ("ignore_rules", "expected_result"),
    [
        (
            ["dependency-name=*...update-types=version-update:semver-major"],
            {
                "invoke": "invoke ~=1.7",
                "tomlkit[test,docs]": "tomlkit[test,docs] ~=0.11.4",
                "mike": "mike >=1.1,<3",
                "pytest": "pytest ~=7.2",
                "pytest-cov": "pytest-cov ~=3.1",
                "pre-commit": "pre-commit ~=2.20",
                "pylint": "pylint ~=2.14",
                "Sphinx": "Sphinx >=4.5.0,<6",
            },
        ),
        (
            ["dependency-name=invoke...versions=>=2"],
            {
                "invoke": "invoke ~=1.7",
                "tomlkit[docs,test]": "tomlkit[docs,test] >=0.11.4,<2",
                "mike": "mike >=1.1,<3",
                "pytest": "pytest ~=7.2",
                "pytest-cov": "pytest-cov ~=3.1",
                "pre-commit": "pre-commit ~=2.20",
                "pylint": "pylint ~=2.14",
                "Sphinx": "Sphinx >=4.5.0,<7",
            },
        ),
        (
            [
                "dependency-name=mike...versions=<1",
                "dependency-name=mike...versions=<=1.0.0",
            ],
            {
                "invoke": "invoke ~=1.7",
                "tomlkit[docs,test]": "tomlkit[docs,test] >=0.11.4,<2",
                "mike": "mike >=1.1,<3",
                "pytest": "pytest ~=7.2",
                "pytest-cov": "pytest-cov ~=3.1",
                "pre-commit": "pre-commit ~=2.20",
                "pylint": "pylint ~=2.14",
                "Sphinx": "Sphinx >=4.5.0,<7",
            },
        ),
        (
            ["dependency-name=pylint...versions=~=2.14"],
            {
                "invoke": "invoke ~=1.7",
                "tomlkit[docs,test]": "tomlkit[docs,test] >=0.11.4,<2",
                "mike": "mike >=1.1,<3",
                "pytest": "pytest ~=7.2",
                "pytest-cov": "pytest-cov ~=3.1",
                "pre-commit": "pre-commit ~=2.20",
                "pylint": "pylint ~=2.13",
                "Sphinx": "Sphinx >=4.5.0,<7",
            },
        ),
        (
            ["dependency-name=pytest"],
            {
                "invoke": "invoke ~=1.7",
                "tomlkit[docs,test]": "tomlkit[docs,test] >=0.11.4,<2",
                "mike": "mike >=1.1,<3",
                "pytest": "pytest ~=7.1",
                "pytest-cov": "pytest-cov ~=3.1",
                "pre-commit": "pre-commit ~=2.20",
                "pylint": "pylint ~=2.14",
                "Sphinx": "Sphinx >=4.5.0,<7",
            },
        ),
        (
            ["dependency-name=pytest-cov...update-types=version-update:semver-minor"],
            {
                "invoke": "invoke ~=1.7",
                "tomlkit[docs,test]": "tomlkit[docs,test] >=0.11.4,<2",
                "mike": "mike >=1.1,<3",
                "pytest": "pytest ~=7.2",
                "pytest-cov": "pytest-cov ~=3.0",
                "pre-commit": "pre-commit ~=2.20",
                "pylint": "pylint ~=2.14",
                "Sphinx": "Sphinx >=4.5.0,<7",
            },
        ),
        (
            ["dependency-name=Sphinx...versions=>=4.5.0"],
            {
                "invoke": "invoke ~=1.7",
                "tomlkit[docs,test]": "tomlkit[docs,test] >=0.11.4,<2",
                "mike": "mike >=1.1,<3",
                "pytest": "pytest ~=7.2",
                "pytest-cov": "pytest-cov ~=3.1",
                "pre-commit": "pre-commit ~=2.20",
                "pylint": "pylint ~=2.14",
                "Sphinx": "Sphinx >=4.5.0,<6",
            },
        ),
    ],
    ids=[
        "* semver-major",
        "invoke >=2",
        "mike <1 <=1.0.0",
        "pylint ~=2.14",
        "pytest",
        "pytest-cov semver-minor",
        "Sphinx >=4.5.0",
    ],
)
def test_ignore_rules_logic(
    tmp_path: "Path", ignore_rules: list[str], expected_result: dict[str, str]
) -> None:
    """Check the workflow of multiple interconnecting ignore rules are respected."""
    import re

    import tomlkit
    from invoke import MockContext

    from ci_cd.tasks.update_deps import update_deps

    pyproject_file = tmp_path / "pyproject.toml"
    pyproject_file.write_text(
        data="""
[project]
requires-python = "~=3.7"

dependencies = [
    "invoke ~=1.7",
    "tomlkit[test,docs] ~=0.11.4",
]

[project.optional-dependencies]
docs = [
    "mike >=1.1,<3",
    "Sphinx >=4.5.0,<6",
]
testing = [
    "pytest ~=7.1",
    "pytest-cov ~=3.0",
]
dev = [
    "mike >=1.1,<3",
    "pytest ~=7.1",
    "pytest-cov ~=3.0",
    "pre-commit ~=2.20",
    "pylint ~=2.13",
    "Sphinx >=4.5.0,<6",
]
""",
        encoding="utf8",
    )

    context = MockContext(
        run={
            re.compile(r".*invoke$"): "invoke (1.7.1)",
            re.compile(r".*tomlkit$"): "tomlkit (1.0.0)",
            re.compile(r".*mike$"): "mike (1.1.1)",
            re.compile(r".*pytest$"): "pytest (7.2.0)",
            re.compile(r".*pytest-cov$"): "pytest-cov (3.1.0)",
            re.compile(r".*pre-commit$"): "pre-commit (2.20.0)",
            re.compile(r".*pylint$"): "pylint (2.14.0)",
            re.compile(r".*Sphinx$"): "Sphinx (6.1.3)",
        },
    )

    update_deps(
        context,
        root_repo_path=str(tmp_path),
        ignore=ignore_rules,
        ignore_separator="...",
    )

    pyproject = tomlkit.loads(pyproject_file.read_bytes())

    dependencies: list[str] = pyproject.get("project", {}).get("dependencies", [])
    for optional_deps in (
        pyproject.get("project", {}).get("optional-dependencies", {}).values()
    ):
        dependencies.extend(optional_deps)

    for line in dependencies:
        for dependency, dependency_requirement in expected_result.items():
            if f"{dependency} " in line:
                assert line == dependency_requirement
                break
        else:
            pytest.fail(f"Unknown package in line: {line}")


def test_python_version_marker(
    tmp_path: "Path", caplog: pytest.LogCaptureFixture
) -> None:
    """Check the python version marker is respected."""
    import re

    from invoke import MockContext

    from ci_cd.tasks.update_deps import update_deps

    pyproject_file = tmp_path / "pyproject.toml"
    pyproject_file.write_text(
        data="""
[project]
requires-python = "~=3.6"

dependencies = [
    "oteapi-core ~=0.1.0; python_version <= '3.7'",
    "oteapi-core ~=0.2.0; python_version > '3.7'",
]
""",
        encoding="utf8",
    )

    context = MockContext(
        run={
            re.compile(r".*3.7 oteapi-core$"): "oteapi-core (0.1.9)",
            re.compile(r".*3.8 oteapi-core$"): "oteapi-core (1.0.1)",
        }
    )

    expected_updated_pyproject_file = """
[project]
requires-python = "~=3.6"

dependencies = [
    "oteapi-core ~=0.1.9; python_version <= '3.7'",
    "oteapi-core >=0.2.0,<2; python_version > '3.7'",
]
"""

    update_deps(
        context,
        root_repo_path=str(tmp_path),
    )

    updated_pyproject_file = pyproject_file.read_text(encoding="utf8")

    assert updated_pyproject_file == expected_updated_pyproject_file

    assert "Min/max Python version from marker: 3.7" in caplog.text
    assert "Min/max Python version from marker: 3.8" in caplog.text
