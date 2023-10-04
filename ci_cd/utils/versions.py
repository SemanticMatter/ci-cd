"""Handle versions."""
import operator
import re
from typing import TYPE_CHECKING, no_type_check

from ci_cd.exceptions import InputError, InputParserError

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any, Literal, Optional, Union


class SemanticVersion(str):
    """A semantic version.

    See [SemVer.org](https://semver.org) for more information about semantic
    versioning.

    The semantic version is in this invocation considered to build up in the following
    way:

        <major>.<minor>.<patch>-<pre_release>+<build>

    Where the names in carets are callable attributes for the instance.

    When casting instances of `SemanticVersion` to `str`, the full version will be
    returned, i.e., as shown above, with a minimum of major.minor.patch.

    For example, for the version `1.5`, i.e., `major=1, minor=5`, the returned `str`
    representation will be the full major.minor.patch version: `1.5.0`.
    The `patch` attribute will default to `0` while `pre_release` and `build` will be
    `None`, when asked for explicitly.

    Precedence for comparing versions is done according to the rules outlined in point
    11 of the specification found at [SemVer.org](https://semver.org/#spec-item-11).

    Parameters:
        major (Union[str, int]): The major version.
        minor (Optional[Union[str, int]]): The minor version.
        patch (Optional[Union[str, int]]): The patch version.
        pre_release (Optional[str]): The pre-release part of the version, i.e., the
            part supplied after a minus (`-`), but before a plus (`+`).
        build (Optional[str]): The build metadata part of the version, i.e., the part
            supplied at the end of the version, after a plus (`+`).

    Attributes:
        major (int): The major version.
        minor (int): The minor version.
        patch (int): The patch version.
        pre_release (str): The pre-release part of the version, i.e., the part
            supplied after a minus (`-`), but before a plus (`+`).
        build (str): The build metadata part of the version, i.e., the part supplied at
            the end of the version, after a plus (`+`).

    """

    _REGEX = (
        r"^(?P<major>0|[1-9]\d*)(?:\.(?P<minor>0|[1-9]\d*))?(?:\.(?P<patch>0|[1-9]\d*))?"
        r"(?:-(?P<pre_release>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
        r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
        r"(?:\+(?P<build>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
    )

    @no_type_check
    def __new__(
        cls, version: "Optional[str]" = None, **kwargs: "Union[str, int]"
    ) -> "SemanticVersion":
        return super().__new__(
            cls, version if version else cls._build_version(**kwargs)
        )

    def __init__(
        self,
        version: "Optional[str]" = None,
        *,
        major: "Union[str, int]" = "",
        minor: "Optional[Union[str, int]]" = None,
        patch: "Optional[Union[str, int]]" = None,
        pre_release: "Optional[str]" = None,
        build: "Optional[str]" = None,
    ) -> None:
        if version is not None:
            if major or minor or patch or pre_release or build:
                raise ValueError(
                    "version cannot be specified along with other parameters"
                )

            match = re.match(self._REGEX, version)
            if match is None:
                raise ValueError(
                    f"version ({version}) cannot be parsed as a semantic version "
                    "according to the SemVer.org regular expression"
                )
            major, minor, patch, pre_release, build = match.groups()

        self._major = int(major)
        self._minor = int(minor) if minor else 0
        self._patch = int(patch) if patch else 0
        self._pre_release = pre_release if pre_release else None
        self._build = build if build else None

    @classmethod
    def _build_version(
        cls,
        major: "Optional[Union[str, int]]" = None,
        minor: "Optional[Union[str, int]]" = None,
        patch: "Optional[Union[str, int]]" = None,
        pre_release: "Optional[str]" = None,
        build: "Optional[str]" = None,
    ) -> str:
        """Build a version from the given parameters."""
        if major is None:
            raise ValueError("At least major must be given")
        version = str(major)
        if minor is not None:
            version += f".{minor}"
        if patch is not None:
            if minor is None:
                raise ValueError("Minor must be given if patch is given")
            version += f".{patch}"
        if pre_release is not None:
            # semver spec #9: A pre-release version MAY be denoted by appending a
            # hyphen and a series of dot separated identifiers immediately following
            # the patch version.
            # https://semver.org/#spec-item-9
            if patch is None:
                raise ValueError("Patch must be given if pre_release is given")
            version += f"-{pre_release}"
        if build is not None:
            # semver spec #10: Build metadata MAY be denoted by appending a plus sign
            # and a series of dot separated identifiers immediately following the patch
            # or pre-release version.
            # https://semver.org/#spec-item-10
            if patch is None:
                raise ValueError("Patch must be given if build is given")
            version += f"+{build}"
        return version

    @property
    def major(self) -> int:
        """The major version."""
        return self._major

    @property
    def minor(self) -> int:
        """The minor version."""
        return self._minor

    @property
    def patch(self) -> int:
        """The patch version."""
        return self._patch

    @property
    def pre_release(self) -> "Union[None, str]":
        """The pre-release part of the version

        This is the part supplied after a minus (`-`), but before a plus (`+`).
        """
        return self._pre_release

    @property
    def build(self) -> "Union[None, str]":
        """The build metadata part of the version.

        This is the part supplied at the end of the version, after a plus (`+`).
        """
        return self._build

    def __str__(self) -> str:
        """Return the full version."""
        return (
            f"{self.major}.{self.minor}.{self.patch}"
            f"{f'-{self.pre_release}' if self.pre_release else ''}"
            f"{f'+{self.build}' if self.build else ''}"
        )

    def __repr__(self) -> str:
        """Return the string representation of the object."""
        return repr(self.__str__())

    def _validate_other_type(self, other: "Any") -> "SemanticVersion":
        """Initial check/validation of `other` before rich comparisons."""
        not_implemented_exc = NotImplementedError(
            f"Rich comparison not implemented between {self.__class__.__name__} and "
            f"{type(other)}"
        )

        if isinstance(other, self.__class__):
            return other

        if isinstance(other, str):
            try:
                return self.__class__(other)
            except (TypeError, ValueError) as exc:
                raise not_implemented_exc from exc

        raise not_implemented_exc

    def __lt__(self, other: "Any") -> bool:
        """Less than (`<`) rich comparison."""
        other_semver = self._validate_other_type(other)

        if self.major < other_semver.major:
            return True
        if self.major == other_semver.major:
            if self.minor < other_semver.minor:
                return True
            if self.minor == other_semver.minor:
                if self.patch < other_semver.patch:
                    return True
                if self.patch == other_semver.patch:
                    if self.pre_release is None:
                        return False
                    if other_semver.pre_release is None:
                        return True
                    return self.pre_release < other_semver.pre_release
        return False

    def __le__(self, other: "Any") -> bool:
        """Less than or equal to (`<=`) rich comparison."""
        return self.__lt__(other) or self.__eq__(other)

    def __eq__(self, other: "Any") -> bool:
        """Equal to (`==`) rich comparison."""
        other_semver = self._validate_other_type(other)

        return (
            self.major == other_semver.major
            and self.minor == other_semver.minor
            and self.patch == other_semver.patch
            and self.pre_release == other_semver.pre_release
        )

    def __ne__(self, other: "Any") -> bool:
        """Not equal to (`!=`) rich comparison."""
        return not self.__eq__(other)

    def __ge__(self, other: "Any") -> bool:
        """Greater than or equal to (`>=`) rich comparison."""
        return not self.__lt__(other)

    def __gt__(self, other: "Any") -> bool:
        """Greater than (`>`) rich comparison."""
        return not self.__le__(other)

    def next_version(self, version_part: str) -> "SemanticVersion":
        """Return the next version for the specified version part.

        Parameters:
            version_part: The version part to increment.

        Returns:
            The next version.

        Raises:
            ValueError: If the version part is not one of `major`, `minor`, or `patch`.

        """
        if version_part not in ("major", "minor", "patch"):
            raise ValueError(
                "version_part must be one of 'major', 'minor', or 'patch', not "
                f"{version_part!r}"
            )

        if version_part == "major":
            return self.__class__(f"{self.major + 1}.0.0")
        if version_part == "minor":
            return self.__class__(f"{self.major}.{self.minor + 1}.0")

        return self.__class__(f"{self.major}.{self.minor}.{self.patch + 1}")


def parse_ignore_entries(
    entries: list[str], separator: str
) -> 'dict[str, dict[Literal["versions", "update-types"], list[str]]]':
    """Parser for the `--ignore` option.

    The `--ignore` option values are given as key/value-pairs in the form:
    `key=value...key=value`. Here `...` is the separator value supplied by
    `--ignore-separator`.

    Parameters:
        entries: The list of supplied `--ignore` options.
        separator: The supplied `--ignore-separator` value.

    Returns:
        A parsed mapping of dependencies to ignore rules.

    """
    ignore_entries: 'dict[str, dict[Literal["versions", "update-types"], list[str]]]' = (
        {}
    )

    for entry in entries:
        pairs = entry.split(separator, maxsplit=2)
        for pair in pairs:
            if separator in pair:
                raise InputParserError(
                    "More than three key/value-pairs were given for an `--ignore` "
                    "option, while there are only three allowed key names. Input "
                    f"value: --ignore={entry}"
                )

        ignore_entry: 'dict[Literal["dependency-name", "versions", "update-types"], str]' = (  # pylint: disable=line-too-long
            {}
        )
        for pair in pairs:
            match = re.match(
                r"^(?P<key>dependency-name|versions|update-types)=(?P<value>.*)$",
                pair,
            )
            if match is None:
                raise InputParserError(
                    f"Could not parse ignore configuration: {pair!r} (part of the "
                    f"ignore option: {entry!r}"
                )
            if match.group("key") in ignore_entry:
                raise InputParserError(
                    "An ignore configuration can only be given once per option. The "
                    f"configuration key {match.group('key')!r} was found multiple "
                    f"times in the option {entry!r}"
                )

            ignore_entry[match.group("key")] = match.group("value").strip()  # type: ignore[index]  # pylint: disable=line-too-long

        if "dependency-name" not in ignore_entry:
            raise InputError(
                "Ignore option entry missing required 'dependency-name' "
                f"configuration. Ignore option entry: {entry}"
            )

        dependency_name: str = ignore_entry.pop("dependency-name", "")
        if dependency_name not in ignore_entries:
            ignore_entries[dependency_name] = {
                key: [value] for key, value in ignore_entry.items()  # type: ignore[misc]
            }
        else:
            for key, value in ignore_entry.items():
                ignore_entries[dependency_name][key].append(value)  # type: ignore[index]

    return ignore_entries


def parse_ignore_rules(
    rules: "dict[Literal['versions', 'update-types'], list[str]]",
) -> "tuple[list[dict[Literal['operator', 'version'], str]], dict[Literal['version-update'], list[Literal['major', 'minor', 'patch']]]]":  # pylint: disable=line-too-long
    """Parser for a specific set of ignore rules.

    Parameters:
        rules: A set of ignore rules for one or more packages.

    Returns:
        A tuple of the parsed 'versions' and 'update-types' entries as dictionaries.

    """
    if not rules:
        # Ignore package altogether
        return [{"operator": ">=", "version": "0"}], {}

    versions: 'list[dict[Literal["operator", "version"], str]]' = []
    update_types: "dict[Literal['version-update'], list[Literal['major', 'minor', 'patch']]]" = (  # pylint: disable=line-too-long
        {}
    )

    if "versions" in rules:
        for versions_entry in rules["versions"]:
            match = re.match(
                r"^(?P<operator>>|<|<=|>=|==|!=|~=)\s*"
                r"(?P<version>[0-9]+(?:\.[0-9]+){0,2})$",
                versions_entry,
            )
            if match is None:
                raise InputParserError(
                    "Ignore option's 'versions' value cannot be parsed. It "
                    "must be a single operator followed by a version number.\n"
                    f"Unparseable 'versions' value: {versions_entry!r}"
                )
            versions.append(match.groupdict())  # type: ignore[arg-type]

    if "update-types" in rules:
        update_types["version-update"] = []
        for update_type_entry in rules["update-types"]:
            match = re.match(
                r"^version-update:semver-(?P<semver_part>major|minor|patch)$",
                update_type_entry,
            )
            if match is None:
                raise InputParserError(
                    "Ignore option's 'update-types' value cannot be parsed."
                    " It must be either: 'version-update:semver-major', "
                    "'version-update:semver-minor' or "
                    "'version-update:semver-patch'.\nUnparseable 'update-types' "
                    f"value: {update_type_entry!r}"
                )
            update_types["version-update"].append(match.group("semver_part"))  # type: ignore[arg-type]  # pylint: disable=line-too-long

    return versions, update_types


def _ignore_version_rules(
    latest: list[str],
    version_rules: "list[dict[Literal['operator', 'version'], str]]",
) -> bool:
    """Determine whether to ignore package based on `versions` input."""
    semver_latest = SemanticVersion(".".join(latest))
    operators_mapping = {
        ">": operator.gt,
        "<": operator.lt,
        "<=": operator.le,
        ">=": operator.ge,
        "==": operator.eq,
        "!=": operator.ne,
    }

    decision_version_rules = []
    for version_rule in version_rules:
        decision_version_rule = False
        semver_version_rule = SemanticVersion(version_rule["version"])

        if version_rule["operator"] in operators_mapping:
            if operators_mapping[version_rule["operator"]](
                semver_latest, semver_version_rule
            ):
                decision_version_rule = True
        elif "~=" == version_rule["operator"]:
            if "." not in version_rule["version"]:
                raise InputError(
                    "Ignore option value error. For the 'versions' config key, when "
                    "using the '~=' operator more than a single version part MUST be "
                    "specified. E.g., '~=2' is disallowed, instead use '~=2.0' or "
                    "similar."
                )

            upper_limit = (
                "major" if version_rule["version"].count(".") == 1 else "minor"
            )

            if (
                semver_version_rule
                <= semver_latest
                < semver_version_rule.next_version(upper_limit)
            ):
                decision_version_rule = True
        else:
            raise InputParserError(
                "Ignore option value error. The 'versions' config key only "
                "supports the following operators: '>', '<', '<=', '>=', '==', "
                "'!=', '~='.\n"
                f"Unparseable 'versions' value: {version_rule!r}"
            )

        decision_version_rules.append(decision_version_rule)

    # If ALL version rules AND'ed together are True, ignore the version.
    return bool(decision_version_rules and all(decision_version_rules))


def _ignore_semver_rules(
    current: list[str],
    latest: list[str],
    semver_rules: "dict[Literal['version-update'], list[Literal['major', 'minor', 'patch']]]",  # pylint: disable=line-too-long
) -> bool:
    """If ANY of the semver rules are True, ignore the version."""
    if any(
        _ not in ["major", "minor", "patch"] for _ in semver_rules["version-update"]
    ):
        raise InputParserError(
            f"Only valid values for 'version-update' are 'major', 'minor', and "
            f"'patch' (you gave {semver_rules['version-update']!r})."
        )

    if "major" in semver_rules["version-update"]:
        if latest[0] != current[0]:
            return True

    elif "minor" in semver_rules["version-update"]:
        if (
            len(latest) >= 2
            and len(current) >= 2
            and latest[1] > current[1]
            and latest[0] == current[0]
        ):
            return True

    elif "patch" in semver_rules["version-update"]:
        if (
            len(latest) >= 3
            and len(current) >= 3
            and latest[2] > current[2]
            and latest[0] == current[0]
            and latest[1] == current[1]
        ):
            return True

    return False


def ignore_version(
    current: list[str],
    latest: list[str],
    version_rules: "list[dict[Literal['operator', 'version'], str]]",
    semver_rules: "dict[Literal['version-update'], list[Literal['major', 'minor', 'patch']]]",  # pylint: disable=line-too-long
) -> bool:
    """Determine whether the latest version can be ignored.

    Parameters:
        current: The current version as a list of version parts. It's expected, but not
            required, the version is a semantic version.
        latest: The latest version as a list of version parts. It's expected, but not
            required, the version is a semantic version.
        version_rules: Version ignore rules.
        semver_rules: Semantic version ignore rules.

    Returns:
        Whether or not the latest version can be ignored based on the version and
        semantic version ignore rules.

    """
    # ignore all updates
    if not version_rules and not semver_rules:
        # A package name has been specified without specific rules, ignore all updates
        # for package.
        return True

    # version rules
    if _ignore_version_rules(latest, version_rules):
        return True

    # semver rules
    if "version-update" in semver_rules and _ignore_semver_rules(
        current, latest, semver_rules
    ):
        return True

    return False
