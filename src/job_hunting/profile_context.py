from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


ALLOWED_PROFILE_SECTION_KEYS = {
    "work_experience",
    "projects",
    "education",
    "skills",
    "public_speaking",
    "values",
}

DISCOVERY_SCORING_SECTIONS = ("work_experience", "projects", "skills")
ALLOWED_TOP_LEVEL_KEYS = {"identity", "search", "profile_sections"}


class ProfileConfigError(ValueError):
    pass


@dataclass(frozen=True)
class LinkConfig:
    key: str
    label: str
    url: str
    display: str
    show_on_cv: bool = False


@dataclass(frozen=True)
class IdentityConfig:
    full_name: str
    preferred_name: str
    email: str
    location_base: str
    work_modes: tuple[str, ...]
    links: tuple[LinkConfig, ...]


@dataclass(frozen=True)
class RoleSearchConfig:
    primary: str
    accepted: tuple[str, ...]
    excluded: tuple[str, ...]


@dataclass(frozen=True)
class SenioritySearchConfig:
    target: str
    accepted: tuple[str, ...]
    excluded: tuple[str, ...]


@dataclass(frozen=True)
class LocationsSearchConfig:
    accepted: tuple[str, ...]
    excluded: tuple[str, ...]


@dataclass(frozen=True)
class IndustriesSearchConfig:
    preferred: tuple[str, ...]


@dataclass(frozen=True)
class SearchConfig:
    roles: RoleSearchConfig
    seniority: SenioritySearchConfig
    locations: LocationsSearchConfig
    industries: IndustriesSearchConfig
    salary: str | None
    dealbreakers: tuple[str, ...]


@dataclass(frozen=True)
class SectionLink:
    label: str
    url: str


@dataclass(frozen=True)
class PeriodConfig:
    start: str
    end: str


@dataclass(frozen=True)
class WorkAchievement:
    area: str
    text: str
    links: tuple[SectionLink, ...]


@dataclass(frozen=True)
class WorkRole:
    id: str
    company: str
    title: str
    period: PeriodConfig
    industry: str | None
    company_summary: str | None
    show_on_cv: bool
    achievements: tuple[WorkAchievement, ...]


@dataclass(frozen=True)
class ProjectItem:
    id: str
    name: str
    title: str | None
    period: PeriodConfig | None
    description: str
    show_on_cv: bool
    links: tuple[SectionLink, ...]
    tech_stack: tuple[str, ...]


@dataclass(frozen=True)
class EducationItem:
    id: str
    institution: str
    degree: str
    field: str
    period: PeriodConfig | None
    grade: str | None
    show_on_cv: bool
    links: tuple[SectionLink, ...]


@dataclass(frozen=True)
class SkillGroup:
    name: str
    show_on_cv: bool
    skills: tuple[str, ...]


@dataclass(frozen=True)
class TalkItem:
    id: str
    conference: str
    title: str
    show_on_cv: bool
    links: tuple[SectionLink, ...]


@dataclass(frozen=True)
class PublicationItem:
    id: str
    title: str
    description: str | None
    show_on_cv: bool
    links: tuple[SectionLink, ...]


@dataclass(frozen=True)
class ValueItem:
    id: str
    title: str
    description: str


@dataclass(frozen=True)
class ProfileSections:
    work_experience: tuple[WorkRole, ...] = ()
    projects: tuple[ProjectItem, ...] = ()
    education: tuple[EducationItem, ...] = ()
    skills: tuple[SkillGroup, ...] = ()
    talks: tuple[TalkItem, ...] = ()
    publications: tuple[PublicationItem, ...] = ()
    values: tuple[ValueItem, ...] = ()
    interests: tuple[ValueItem, ...] = ()


@dataclass(frozen=True)
class ProfileConfig:
    path: Path
    root_dir: Path
    identity: IdentityConfig
    search: SearchConfig
    profile_sections: dict[str, Path]


@dataclass(frozen=True)
class DiscoveryProfileContext:
    filter_context: str
    scoring_context: str


@dataclass(frozen=True)
class ApplicationProfileContext:
    identity_context: str
    profile_sections_context: str
    section_keys: tuple[str, ...]


def load_profile_config(path: Path | str = "knowledge/profile.yaml") -> ProfileConfig:
    profile_path = Path(path)
    try:
        raw = yaml.safe_load(profile_path.read_text(encoding="utf-8")) or {}
    except FileNotFoundError as exc:
        raise ProfileConfigError(f"profile config not found: {profile_path}") from exc
    if not isinstance(raw, dict):
        raise ProfileConfigError("profile config must be a YAML mapping")

    _reject_unsupported_top_level_keys(raw)

    identity = _parse_identity(_require_mapping(raw, "identity"))
    search = _parse_search(_require_mapping(raw, "search"))
    profile_sections = _parse_profile_sections(
        _require_mapping(raw, "profile_sections")
    )

    return ProfileConfig(
        path=profile_path,
        root_dir=profile_path.parent,
        identity=identity,
        search=search,
        profile_sections=profile_sections,
    )


def build_discovery_context(
    path: Path | str = "knowledge/profile.yaml",
) -> DiscoveryProfileContext:
    config = load_profile_config(path)
    scoring_parts: list[str] = []
    for key in DISCOVERY_SCORING_SECTIONS:
        if key in config.profile_sections:
            scoring_parts.append(_read_section(config, key))
    if not scoring_parts:
        raise ProfileConfigError(
            "Discovery scoring requires at least one of profile_sections: "
            + ", ".join(DISCOVERY_SCORING_SECTIONS)
        )
    return DiscoveryProfileContext(
        filter_context=_format_discovery_filter_context(config),
        scoring_context="\n\n".join(scoring_parts),
    )


def build_application_context(
    path: Path | str = "knowledge/profile.yaml",
) -> ApplicationProfileContext:
    config = load_profile_config(path)
    section_parts = [_read_section(config, key) for key in config.profile_sections]
    return ApplicationProfileContext(
        identity_context=_format_identity_context(config.identity),
        profile_sections_context="\n\n".join(section_parts),
        section_keys=tuple(config.profile_sections.keys()),
    )


def _reject_unsupported_top_level_keys(raw: dict[str, Any]) -> None:
    unsupported_keys = sorted(set(raw) - ALLOWED_TOP_LEVEL_KEYS)
    if unsupported_keys:
        raise ProfileConfigError(
            f"unsupported top-level profile config key: {unsupported_keys[0]}"
        )


def _parse_identity(raw: dict[str, Any]) -> IdentityConfig:
    location = _require_mapping(raw, "location", prefix="identity")
    links_raw = raw.get("links", [])
    if not isinstance(links_raw, list):
        raise ProfileConfigError("identity.links must be a list")
    return IdentityConfig(
        full_name=_require_string(raw, "full_name", prefix="identity"),
        preferred_name=_require_string(raw, "preferred_name", prefix="identity"),
        email=_require_string(raw, "email", prefix="identity"),
        location_base=_require_string(location, "base", prefix="identity.location"),
        work_modes=tuple(
            _require_string_list(location, "work_modes", prefix="identity.location")
        ),
        links=tuple(_parse_link(item, index) for index, item in enumerate(links_raw)),
    )


def _parse_link(raw: Any, index: int) -> LinkConfig:
    if not isinstance(raw, dict):
        raise ProfileConfigError(f"identity.links[{index}] must be a mapping")
    return LinkConfig(
        key=_require_string(raw, "key", prefix=f"identity.links[{index}]"),
        label=_require_string(raw, "label", prefix=f"identity.links[{index}]"),
        url=_require_string(raw, "url", prefix=f"identity.links[{index}]"),
        display=str(raw.get("display") or raw.get("url") or ""),
        show_on_cv=bool(raw.get("show_on_cv", False)),
    )


def _parse_search(raw: dict[str, Any]) -> SearchConfig:
    roles = _require_mapping(raw, "roles", prefix="search")
    seniority = _require_mapping(raw, "seniority", prefix="search")
    locations = _require_mapping(raw, "locations", prefix="search")
    industries = _require_mapping(raw, "industries", prefix="search")
    return SearchConfig(
        roles=RoleSearchConfig(
            primary=_require_string(roles, "primary", prefix="search.roles"),
            accepted=tuple(
                _require_string_list(roles, "accepted", prefix="search.roles")
            ),
            excluded=tuple(
                _string_list(roles.get("excluded", []), "search.roles.excluded")
            ),
        ),
        seniority=SenioritySearchConfig(
            target=_require_string(seniority, "target", prefix="search.seniority"),
            accepted=tuple(
                _require_string_list(
                    seniority, "accepted", prefix="search.seniority"
                )
            ),
            excluded=tuple(
                _string_list(
                    seniority.get("excluded", []), "search.seniority.excluded"
                )
            ),
        ),
        locations=LocationsSearchConfig(
            accepted=tuple(
                _require_string_list(
                    locations, "accepted", prefix="search.locations"
                )
            ),
            excluded=tuple(
                _string_list(
                    locations.get("excluded", []), "search.locations.excluded"
                )
            ),
        ),
        industries=IndustriesSearchConfig(
            preferred=tuple(
                _require_string_list(
                    industries, "preferred", prefix="search.industries"
                )
            ),
        ),
        salary=_optional_string(raw, "salary", prefix="search"),
        dealbreakers=tuple(
            _string_list(raw.get("dealbreakers", []), "search.dealbreakers")
        ),
    )


def _parse_profile_sections(raw: dict[str, Any]) -> dict[str, Path]:
    sections: dict[str, Path] = {}
    for key, value in raw.items():
        if key not in ALLOWED_PROFILE_SECTION_KEYS:
            raise ProfileConfigError(f"unsupported profile_sections key: {key}")
        if not isinstance(value, str) or not value.strip():
            raise ProfileConfigError(f"profile_sections.{key} must be a non-empty path")
        section_path = Path(value.strip())
        if section_path.suffix != ".yaml":
            raise ProfileConfigError(f"profile_sections.{key} must point to a .yaml file")
        sections[key] = section_path
    return sections


def load_profile_sections(config: ProfileConfig) -> ProfileSections:
    values: dict[str, Any] = {
        "work_experience": (),
        "projects": (),
        "education": (),
        "skills": (),
        "talks": (),
        "publications": (),
        "values": (),
        "interests": (),
    }
    for key, relative_path in config.profile_sections.items():
        raw = _read_section_yaml(config, key, relative_path)
        if key == "work_experience":
            values["work_experience"] = _parse_work_experience(raw)
        elif key == "projects":
            values["projects"] = _parse_projects(raw)
        elif key == "education":
            values["education"] = _parse_education(raw)
        elif key == "skills":
            values["skills"] = _parse_skills(raw)
        elif key == "public_speaking":
            talks, publications = _parse_public_performance(raw)
            values["talks"] = talks
            values["publications"] = publications
        elif key == "values":
            profile_values, interests = _parse_values_and_interests(raw)
            values["values"] = profile_values
            values["interests"] = interests
    return ProfileSections(**values)


def _read_section_yaml(
    config: ProfileConfig, key: str, relative_path: Path
) -> dict[str, Any]:
    full_path = config.root_dir / relative_path
    try:
        raw = yaml.safe_load(full_path.read_text(encoding="utf-8")) or {}
    except FileNotFoundError as exc:
        raise ProfileConfigError(
            f"profile_sections.{key} points to {relative_path}, "
            "but the file does not exist"
        ) from exc
    if not isinstance(raw, dict):
        raise ProfileConfigError(f"profile_sections.{key} must be a YAML mapping")
    return raw


def _parse_work_experience(raw: dict[str, Any]) -> tuple[WorkRole, ...]:
    roles = []
    for index, item in enumerate(
        _require_list(raw.get("roles"), "work_experience.roles")
    ):
        prefix = f"work_experience.roles[{index}]"
        if not isinstance(item, dict):
            raise ProfileConfigError(f"{prefix} must be a mapping")
        achievements = []
        for achievement_index, achievement in enumerate(
            _require_list(item.get("achievements"), f"{prefix}.achievements")
        ):
            achievement_prefix = f"{prefix}.achievements[{achievement_index}]"
            if not isinstance(achievement, dict):
                raise ProfileConfigError(f"{achievement_prefix} must be a mapping")
            achievements.append(
                WorkAchievement(
                    area=_require_string(
                        achievement, "area", prefix=achievement_prefix
                    ),
                    text=_require_string(
                        achievement, "text", prefix=achievement_prefix
                    ),
                    links=_parse_section_links(achievement, achievement_prefix),
                )
            )
        roles.append(
            WorkRole(
                id=_require_string(item, "id", prefix=prefix),
                company=_require_string(item, "company", prefix=prefix),
                title=_require_string(item, "title", prefix=prefix),
                period=_parse_period(item.get("period"), prefix, required=True),
                industry=_optional_string(item, "industry", prefix=prefix),
                company_summary=_optional_string(
                    item, "company_summary", prefix=prefix
                ),
                show_on_cv=_optional_bool(item, "show_on_cv", prefix=prefix),
                achievements=tuple(achievements),
            )
        )
    return tuple(roles)


def _parse_projects(raw: dict[str, Any]) -> tuple[ProjectItem, ...]:
    projects = []
    for index, item in enumerate(_require_list(raw.get("projects"), "projects.projects")):
        prefix = f"projects.projects[{index}]"
        if not isinstance(item, dict):
            raise ProfileConfigError(f"{prefix} must be a mapping")
        projects.append(
            ProjectItem(
                id=_require_string(item, "id", prefix=prefix),
                name=_require_string(item, "name", prefix=prefix),
                title=_optional_string(item, "title", prefix=prefix),
                period=_parse_period(item.get("period"), prefix, required=False),
                description=_require_string(item, "description", prefix=prefix),
                show_on_cv=_optional_bool(item, "show_on_cv", prefix=prefix),
                links=_parse_section_links(item, prefix),
                tech_stack=tuple(
                    _string_list(item.get("tech_stack", []), f"{prefix}.tech_stack")
                ),
            )
        )
    return tuple(projects)


def _parse_education(raw: dict[str, Any]) -> tuple[EducationItem, ...]:
    education = []
    for index, item in enumerate(
        _require_list(raw.get("education"), "education.education")
    ):
        prefix = f"education.education[{index}]"
        if not isinstance(item, dict):
            raise ProfileConfigError(f"{prefix} must be a mapping")
        education.append(
            EducationItem(
                id=_require_string(item, "id", prefix=prefix),
                institution=_require_string(item, "institution", prefix=prefix),
                degree=_require_string(item, "degree", prefix=prefix),
                field=_require_string(item, "field", prefix=prefix),
                period=_parse_period(item.get("period"), prefix, required=False),
                grade=_optional_string(item, "grade", prefix=prefix),
                show_on_cv=_optional_bool(item, "show_on_cv", prefix=prefix),
                links=_parse_section_links(item, prefix),
            )
        )
    return tuple(education)


def _parse_skills(raw: dict[str, Any]) -> tuple[SkillGroup, ...]:
    groups = []
    for index, item in enumerate(
        _require_list(raw.get("skill_groups"), "skills.skill_groups")
    ):
        prefix = f"skills.skill_groups[{index}]"
        if not isinstance(item, dict):
            raise ProfileConfigError(f"{prefix} must be a mapping")
        groups.append(
            SkillGroup(
                name=_require_string(item, "name", prefix=prefix),
                show_on_cv=_optional_bool(item, "show_on_cv", prefix=prefix),
                skills=tuple(_require_string_list(item, "skills", prefix=prefix)),
            )
        )
    return tuple(groups)


def _parse_public_performance(
    raw: dict[str, Any],
) -> tuple[tuple[TalkItem, ...], tuple[PublicationItem, ...]]:
    talks_raw = _optional_list(raw.get("talks"), "public_speaking.talks")
    publications_raw = _optional_list(
        raw.get("publications"), "public_speaking.publications"
    )
    if not talks_raw and not publications_raw:
        raise ProfileConfigError("public_speaking requires talks or publications")

    talks = []
    for index, item in enumerate(talks_raw):
        prefix = f"public_speaking.talks[{index}]"
        if not isinstance(item, dict):
            raise ProfileConfigError(f"{prefix} must be a mapping")
        talks.append(
            TalkItem(
                id=_require_string(item, "id", prefix=prefix),
                conference=_require_string(item, "conference", prefix=prefix),
                title=_require_string(item, "title", prefix=prefix),
                show_on_cv=_optional_bool(item, "show_on_cv", prefix=prefix),
                links=_parse_section_links(item, prefix),
            )
        )

    publications = []
    for index, item in enumerate(publications_raw):
        prefix = f"public_speaking.publications[{index}]"
        if not isinstance(item, dict):
            raise ProfileConfigError(f"{prefix} must be a mapping")
        publications.append(
            PublicationItem(
                id=_require_string(item, "id", prefix=prefix),
                title=_require_string(item, "title", prefix=prefix),
                description=_optional_string(item, "description", prefix=prefix),
                show_on_cv=_optional_bool(item, "show_on_cv", prefix=prefix),
                links=_parse_section_links(item, prefix),
            )
        )
    return tuple(talks), tuple(publications)


def _parse_values_and_interests(
    raw: dict[str, Any],
) -> tuple[tuple[ValueItem, ...], tuple[ValueItem, ...]]:
    values_raw = _optional_list(raw.get("values"), "values.values")
    interests_raw = _optional_list(raw.get("interests"), "values.interests")
    if not values_raw and not interests_raw:
        raise ProfileConfigError("values requires values or interests")
    return (
        _parse_value_items(values_raw, "values.values"),
        _parse_value_items(interests_raw, "values.interests"),
    )


def _parse_value_items(raw_items: list[Any], name: str) -> tuple[ValueItem, ...]:
    items = []
    for index, item in enumerate(raw_items):
        prefix = f"{name}[{index}]"
        if not isinstance(item, dict):
            raise ProfileConfigError(f"{prefix} must be a mapping")
        items.append(
            ValueItem(
                id=_require_string(item, "id", prefix=prefix),
                title=_require_string(item, "title", prefix=prefix),
                description=_require_string(item, "description", prefix=prefix),
            )
        )
    return tuple(items)


def _read_section(config: ProfileConfig, key: str) -> str:
    relative_path = config.profile_sections[key]
    full_path = config.root_dir / relative_path
    try:
        content = full_path.read_text(encoding="utf-8").strip()
    except FileNotFoundError as exc:
        raise ProfileConfigError(
            f"profile_sections.{key} points to {relative_path}, "
            "but the file does not exist"
        ) from exc
    return f"## {key}\n\n{content}"


def _format_identity_context(identity: IdentityConfig) -> str:
    links = "\n".join(
        f"- {link.label}: {link.url} ({link.display})" for link in identity.links
    )
    return (
        f"Full name: {identity.full_name}\n"
        f"Preferred name: {identity.preferred_name}\n"
        f"Email: {identity.email}\n"
        f"Location: {identity.location_base}\n"
        f"Work modes: {', '.join(identity.work_modes)}\n"
        f"Links:\n{links}"
    )


def _format_discovery_filter_context(config: ProfileConfig) -> str:
    search = config.search
    lines = [
        f"Primary role: {search.roles.primary}",
        f"Accepted roles: {', '.join(search.roles.accepted)}",
        f"Excluded roles: {', '.join(search.roles.excluded)}",
        f"Target seniority: {search.seniority.target}",
        f"Accepted seniority: {', '.join(search.seniority.accepted)}",
        f"Excluded seniority: {', '.join(search.seniority.excluded)}",
        f"Accepted locations: {', '.join(search.locations.accepted)}",
        f"Excluded locations: {', '.join(search.locations.excluded)}",
        f"Preferred industries: {', '.join(search.industries.preferred)}",
    ]
    if search.salary:
        lines.append(f"Salary threshold: {search.salary}")
    lines.extend(
        [
            f"Dealbreakers: {', '.join(search.dealbreakers)}",
            f"Candidate base location: {config.identity.location_base}",
            f"Candidate work modes: {', '.join(config.identity.work_modes)}",
        ]
    )
    return "\n".join(lines)


def _require_mapping(
    raw: dict[str, Any], key: str, prefix: str = ""
) -> dict[str, Any]:
    value = raw.get(key)
    name = f"{prefix}.{key}" if prefix else key
    if not isinstance(value, dict):
        raise ProfileConfigError(f"{name} is required and must be a mapping")
    return value


def _require_string(raw: dict[str, Any], key: str, prefix: str = "") -> str:
    value = raw.get(key)
    name = f"{prefix}.{key}" if prefix else key
    if not isinstance(value, str) or not value.strip():
        raise ProfileConfigError(f"{name} is required")
    return value.strip()


def _optional_string(raw: dict[str, Any], key: str, prefix: str = "") -> str | None:
    value = raw.get(key)
    name = f"{prefix}.{key}" if prefix else key
    if value is None:
        return None
    if not isinstance(value, str):
        raise ProfileConfigError(f"{name} must be a string")
    normalized = value.strip()
    return normalized or None


def _optional_bool(
    raw: dict[str, Any], key: str, prefix: str = "", default: bool = True
) -> bool:
    value = raw.get(key, default)
    name = f"{prefix}.{key}" if prefix else key
    if not isinstance(value, bool):
        raise ProfileConfigError(f"{name} must be a boolean")
    return value


def _optional_list(value: Any, name: str) -> list[Any]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ProfileConfigError(f"{name} must be a list")
    return value


def _require_list(value: Any, name: str) -> list[Any]:
    if not isinstance(value, list) or not value:
        raise ProfileConfigError(f"{name} must be a non-empty list")
    return value


def _parse_period(raw: Any, prefix: str, *, required: bool) -> PeriodConfig | None:
    if raw is None and not required:
        return None
    if not isinstance(raw, dict):
        raise ProfileConfigError(f"{prefix}.period is required and must be a mapping")
    start = _require_string(raw, "start", prefix=f"{prefix}.period")
    end = _require_string(raw, "end", prefix=f"{prefix}.period")
    _validate_period_value(start, f"{prefix}.period.start", allow_present=False)
    _validate_period_value(end, f"{prefix}.period.end", allow_present=True)
    return PeriodConfig(start=start, end=end)


def _validate_period_value(value: str, name: str, *, allow_present: bool) -> None:
    if allow_present and value == "present":
        return
    if not re.fullmatch(r"\d{4}-\d{2}", value):
        raise ProfileConfigError(f"{name} must use YYYY-MM")


def _parse_section_links(raw: dict[str, Any], prefix: str) -> tuple[SectionLink, ...]:
    links_raw = raw.get("links", [])
    if links_raw is None:
        return ()
    if not isinstance(links_raw, list):
        raise ProfileConfigError(f"{prefix}.links must be a list")

    links = []
    for index, item in enumerate(links_raw):
        link_prefix = f"{prefix}.links[{index}]"
        if not isinstance(item, dict):
            raise ProfileConfigError(f"{link_prefix} must be a mapping")
        url = _require_string(item, "url", prefix=link_prefix)
        if not url.startswith("https://"):
            raise ProfileConfigError(f"{link_prefix}.url must be an https URL")
        links.append(
            SectionLink(
                label=_require_string(item, "label", prefix=link_prefix),
                url=url,
            )
        )
    return tuple(links)


def _require_string_list(
    raw: dict[str, Any], key: str, prefix: str = ""
) -> list[str]:
    value = raw.get(key)
    name = f"{prefix}.{key}" if prefix else key
    if value is None:
        raise ProfileConfigError(f"{name} is required")
    return _string_list(value, name)


def _string_list(value: Any, name: str) -> list[str]:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item.strip() for item in value
    ):
        raise ProfileConfigError(f"{name} must be a list of strings")
    return [item.strip() for item in value]
