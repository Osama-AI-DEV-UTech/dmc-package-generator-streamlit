"""Orchestrates: one research pass -> N distinct structured packages.

Ids come from the authoritative platform metadata; each variant is isolated
(retried once on failure / malformed JSON) so one bad variant never kills the run.
"""
from __future__ import annotations

import copy
import random
import string
import uuid
from datetime import datetime, timezone

from . import metadata as meta
from . import prompts
from .config import settings
from .inputs import UserInput
from .openai_client import OpenAIError, extract_json, get_provider
from .schema import DMCInfo, Package, PriceReference


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")


def _sku() -> str:
    return "P-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


def _build_ids(inp: UserInput) -> dict:
    return {
        "packageMood": meta.idval_list("packageMood", inp.package_moods),
        "pkgType": meta.idval_list("pkgType", inp.package_types),
        "availableMealPref": meta.idval_list("availableMealPref", inp.meal_preferences),
        "transferTypes": meta.idval_list("availableType", inp.transfer_types),
        "guideLanguages": meta.idval_list("guideLanguages", inp.guide_languages),
        "accommodationType": meta.idval_list("accommodation", inp.accommodation_type),
        "roomCategory": meta.idval("roomCategory", inp.room_category) if inp.room_category else None,
        "rating": meta.idval("rating", inp.hotel_rating) if inp.hotel_rating else None,
        "region": meta.idval("region", inp.region),
        "country": meta.resolve_country(inp.country),
        "cities": [meta.resolve_city(c) for c in inp.cities],
        "ageRange": meta.idval("ageGroups", inp.age_range),
        "childAgeRange": meta.idval("childAgeRange", inp.child_age_range),
        "pkgDays": meta.idval_list("pkgDays", inp.travel_days),
        "pkgMonths": meta.idval_list("pkgMonths", inp.travel_months),
        "pkgYears": meta.idval_list("pkgYears", inp.travel_years),
    }


def _system_fields(inp: UserInput) -> dict:
    now = _now_iso()
    return {
        "skuId": _sku(), "dmcId": str(uuid.uuid4()), "packageId": str(uuid.uuid4()),
        "createdAt": now, "updatedAt": now,
        "dmcApproved": False, "adminApproved": "PENDING",
        "numberOfDays": inp.number_of_days,
        "seatsPerTour": inp.seats_per_tour, "groupSize": inp.group_size,
    }


def _coerce_package(pkg_dict: dict, inp: UserInput, sysf: dict) -> Package:
    pkg_dict = copy.deepcopy(pkg_dict)
    pkg_dict.update({
        "skuId": sysf["skuId"], "dmcId": sysf["dmcId"], "packageId": sysf["packageId"],
        "createdAt": sysf["createdAt"], "updatedAt": sysf["updatedAt"],
        "dmcApproved": False, "adminApproved": "PENDING",
        "numberOfDays": inp.number_of_days,
        "seatsPerTour": inp.seats_per_tour, "groupSize": inp.group_size,
        "image": [], "subMood": [], "promotionPercentage": 0,
        "isChildFriendly": inp.is_child_friendly,
        "isHandicapAccessible": inp.is_handicap_accessible,
        "isInsuranceRequired": inp.is_insurance_required,
        "isActive": inp.is_active, "isTopRated": inp.is_top_rated,
        "isDeleted": False, "isConverted": False,
    })
    if not pkg_dict.get("name"):
        pkg_dict["name"] = inp.name or f"{inp.country} Tour {inp.number_of_days} Days"
    # enforce room category into roomId if provided
    if inp.room_category:
        try:
            for acc in pkg_dict.get("tourPlan", {}).get("accommodation", []):
                acc["roomId"] = [inp.room_category]
        except Exception:
            pass
    return Package.model_validate(pkg_dict)


class VariantResult:
    def __init__(self, index, package, dmc, references, currency):
        self.index = index
        self.package = package
        self.dmc = dmc
        self.references = references
        self.currency = currency


class GenerationResult:
    def __init__(self, request_id, variants, sources, engine, warnings):
        self.request_id = request_id
        self.variants = variants
        self.sources = sources
        self.engine = engine
        self.warnings = warnings


def _parse_one(raw, inp, sysf, currency, index) -> VariantResult:
    parsed = extract_json(raw)
    pkg_dict = parsed.get("package", parsed)
    package = _coerce_package(pkg_dict, inp, sysf)

    dmc = None
    if isinstance(parsed.get("dmc_info"), dict):
        try:
            dmc = DMCInfo.model_validate(parsed["dmc_info"])
        except Exception:
            dmc = None

    refs = []
    for r in parsed.get("price_references", []) or []:
        try:
            refs.append(PriceReference.model_validate(r))
        except Exception:
            continue
    return VariantResult(index, package, dmc, refs, currency)


def generate(inp: UserInput) -> GenerationResult:
    provider = get_provider()
    ids = _build_ids(inp)
    warnings = []

    # ---- Stage 1: shared research --------------------------------------
    try:
        brief, sources = provider.research(
            prompts.RESEARCH_SYSTEM, prompts.build_research_user(inp))
    except Exception as exc:  # noqa: BLE001
        brief, sources = "", []
        warnings.append(f"Research step failed, using fallback: {exc}")

    engine = "openai+web_search" if sources else "openai"
    if not brief.strip():
        brief = prompts.FALLBACK_NOTE + "\n" + prompts.build_research_user(inp)
        engine = "openai (no live research)"

    # ---- Stage 2: N distinct variants ----------------------------------
    total = inp.package_count
    variants = []
    for i in range(1, total + 1):
        sysf = _system_fields(inp)
        provided = {"ids": ids, "system_fields": sysf, "admin_margin": settings.admin_margin}
        user_msg = prompts.build_structure_user(brief, inp, provided, i, total)

        parsed_ok = False
        last_err = None
        for _ in range(2):
            try:
                raw = provider.structure(prompts.STRUCTURE_SYSTEM, user_msg)
                variants.append(_parse_one(raw, inp, sysf, inp.currency, i))
                parsed_ok = True
                break
            except Exception as exc:  # noqa: BLE001
                last_err = exc
        if not parsed_ok:
            warnings.append(f"Package {i} could not be generated: {last_err}")

    if not variants:
        raise OpenAIError("No packages could be generated. " + " | ".join(warnings))

    ref_urls = [r.source_url for v in variants for r in v.references if r.source_url]
    merged = list(dict.fromkeys(sources + ref_urls))
    return GenerationResult(uuid.uuid4().hex[:12], variants, merged, engine, warnings)
