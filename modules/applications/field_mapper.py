from __future__ import annotations

import re
from typing import Any

from modules.applications.form_detector import FormField
from modules.intelligence.schemas import Profile


FIELD_ALIASES = {
    "first name": ("first_name", "first-name", "firstname"), "last name": ("last_name", "last-name", "lastname"),
    "full name": ("name", "full_name", "full-name"), "email": ("email", "email_address"), "phone": ("phone", "telephone"),
    "location": ("location", "city", "address"), "linkedin": ("linkedin", "linkedin_url"), "github": ("github", "github_url"), "portfolio": ("portfolio", "website"),
}


def _value_for(label: str, profile: Profile) -> str | None:
    label = label.lower()
    if "first" in label: return profile.full_name.split()[0] if profile.full_name else None
    if "last" in label: return profile.full_name.split()[-1] if profile.full_name else None
    for key, value in (("email", profile.email), ("phone", profile.phone), ("location", profile.location), ("linkedin", profile.linkedin_url), ("github", profile.github_url), ("portfolio", profile.portfolio_url)):
        if key in label: return value or None
    return None


class FieldMapper:
    def map(self, fields: list[FormField], profile: Profile) -> dict[str, str]:
        return {field.name: value for field in fields if (value := _value_for(field.label, profile))}

    def unknown_required(self, fields: list[FormField], values: dict[str, str]) -> list[FormField]:
        return [field for field in fields if field.required and field.name not in values and field.input_type not in {"file", "hidden", "submit"}]
