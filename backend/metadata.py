"""Authoritative platform metadata (the real ids the DMC platform expects).

Loaded from data/metadata.json (the `dmcCustomPackage` metaData payload). Every
dropdown option and every id/value pair the generator emits is sourced from here,
so packages are natively compatible with the platform. Values not present in the
metadata (e.g. the added Umrah/Hajj moods, or a city outside the curated list)
get a STABLE deterministic uuid5 so output always validates and is reproducible.
"""
from __future__ import annotations

import json
import os
import uuid
from functools import lru_cache

_META = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "data", "metadata.json")

# Moods the platform does not yet expose but the business needs (added on top).
EXTRA_MOODS = ["Umrah", "Hajj", "Religious & Pilgrimage"]

# Country-name aliases: metadata name -> global cities dataset key.
COUNTRY_ALIASES = {
    "Czechia": "Czech Republic", "Cabo Verde": "Cape Verde", "Bahamas": "The Bahamas",
    "British Virgin Islands": "British Virgin Islands", "Gambia": "Gambia",
    "Republic of the Congo": "Congo", "Democratic Republic of the Congo": "DR Congo",
    "Eswatini": "Swaziland", "Myanmar": "Myanmar (Burma)", "Macedonia": "North Macedonia",
}


@lru_cache(maxsize=1)
def _raw() -> dict:
    try:
        with open(_META, encoding="utf-8") as fh:
            payload = json.load(fh)
        return {c["type"]: c["values"] for c in payload.get("data", [])}
    except Exception:
        return {}


def _stable_id(value: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"ubidtours::{value}"))


@lru_cache(maxsize=64)
def _index(type_: str) -> dict:
    """Case-insensitive value -> id map for a metadata type."""
    return {v["value"].strip().lower(): v["id"] for v in _raw().get(type_, [])}


def options(type_: str) -> list[str]:
    vals = [v["value"] for v in _raw().get(type_, [])]
    if type_ == "packageMood":
        vals = vals + EXTRA_MOODS
    return sorted(dict.fromkeys(vals))


def id_for(type_: str, value: str) -> str:
    if not value:
        return _stable_id("")
    return _index(type_).get(value.strip().lower()) or _stable_id(value)


def idval(type_: str, value: str) -> dict:
    return {"id": id_for(type_, value), "value": value}


def idval_list(type_: str, values) -> list[dict]:
    return [idval(type_, v) for v in (values or [])]


# --- Convenience option lists (>= 10 where required) ------------------
def mood_options() -> list[str]:      return options("packageMood")
def traveler_options() -> list[str]:  return options("pkgType")
def transfer_options() -> list[str]:  return options("availableType")
def meal_options() -> list[str]:      return options("availableMealPref")
def region_options() -> list[str]:    return options("region")
def age_options() -> list[str]:       return options("ageGroups")
def child_age_options() -> list[str]: return options("childAgeRange")
def rating_options() -> list[str]:    return options("rating")
def accommodation_options() -> list[str]: return options("accommodation")
def room_category_options() -> list[str]: return options("roomCategory")
def guide_language_options() -> list[str]: return options("guideLanguages")
def day_options() -> list[str]:       return options("pkgDays")
def month_options() -> list[str]:     return options("pkgMonths")
def year_options() -> list[str]:      return options("pkgYears")
def country_options() -> list[str]:   return options("countries")


def resolve_country(value: str) -> dict:
    return idval("countries", value)


def resolve_city(value: str) -> dict:
    """City id from the platform list if known, else a stable uuid5."""
    return {"id": id_for("cities", value), "value": value}


def alias_for_cities(country: str) -> str:
    return COUNTRY_ALIASES.get(country, country)
