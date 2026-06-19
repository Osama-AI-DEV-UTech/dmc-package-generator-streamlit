"""Expert-grade prompt engineering for the DMC Package Generator.

Stage 1  ATLAS  (research)  : OpenAI + web_search -> one shared, fully-sourced
                              destination dossier (multiple real DMCs w/ full
                              contact, ALL excursions, real hotels >= rating,
                              economy fares, entrance fees), Umrah/Hajj aware.
Stage 2  FORGE  (structure) : per-variant -> ONE JSON object
                              { "package": <exact schema>, "dmc_info": {...},
                                "price_references": [...] } - distinct per variant.
"""
from __future__ import annotations

import json
from .inputs import UserInput


def _is_pilgrimage(inp: UserInput) -> bool:
    blob = " ".join(inp.package_moods + inp.package_types).lower()
    return ("umrah" in blob or "hajj" in blob or "pilgrim" in blob or "religious" in blob
            or inp.country.strip().lower() in {"saudi arabia", "ksa"})


PILGRIMAGE_INTEL = """\
PILGRIMAGE INTELLIGENCE (Umrah / Hajj) - apply when relevant
- Treat this as a faith journey, not a sightseeing tour. Tone is respectful and precise.
- Geography & flow: arrivals usually via Jeddah (JED) or Madinah (MED); ground legs are
  Jeddah -> Makkah (~1.5h), Makkah <-> Madinah (~4-5h by road, or high-speed Haramain
  train), Madinah -> airport. Sequence Makkah/Madinah sensibly around flights.
- Rituals to reflect in the itinerary where applicable: entering Ihram at the Meeqat,
  Umrah (Tawaf around the Kaaba, Sa'i between Safa & Marwah, Halq/Taqsir); for Hajj the
  days of Mina, Arafah, Muzdalifah, Jamarat, Tawaf al-Ifadah. Madinah Ziyarat: Masjid
  an-Nabawi (Rawdah, Prophet's tomb), Quba Mosque, Qiblatain, Uhud, the trenches.
- Hotels: state DISTANCE / walking time to Masjid al-Haram (Makkah) and Masjid an-Nabawi
  (Madinah) - this is the #1 buying factor. Mention well-known categories (e.g. Clock
  Tower / Ajyad area in Makkah; Central Haram area in Madinah) using REAL property names.
- Logistics: visa type (Umrah/Hajj/tourist), Nusuk/permit context, women's mahram norms,
  segregated prayer areas, wheelchair/elderly support, laundry for Ihram, ZamZam.
- Meals are typically Halal by default; offer South-Asian / Arabic / Turkish cuisine notes.
"""


# ======================================================================
#  STAGE 1 - ATLAS (research)
# ======================================================================

RESEARCH_SYSTEM = """\
ROLE
You are "ATLAS", a principal Destination Management Company (DMC) product architect
and inbound-contracting analyst with 20+ years building enterprise ground packages.
You reason like a contracting & pricing manager: every DMC, hotel, transfer, excursion
and fee must be REAL, current, and backed by a source URL.

MISSION (this stage only)
With the web_search tool, produce ONE rich, sourced dossier for the destination -
raw material strong enough to assemble several DISTINCT, realistic packages from.

NON-NEGOTIABLES
- Never invent contact details, prices or properties. If unknown, say so / leave blank.
- Attach a SOURCE URL to every DMC, hotel, excursion fee and transfer price.
- Prefer official / operator / reputable OTA sources over aggregator blogs.
- Honour the minimum hotel rating, allowed transfer types and meal preferences given.

WHAT TO GATHER
1. DMC DIRECTORY - as many REAL inbound DMCs / licensed ground operators as you can
   (>= the number of packages requested). Per DMC: company name, legal name (if shown),
   city & country, full address, phone (with country code), WhatsApp (if shown), email,
   website, languages, specialisation, and the source URL. Null any field not visible.
   verified=true only if it came from a live source.
2. EXCURSIONS & ATTRACTIONS - ALL the major experiences a visitor would do across the
   chosen city/country (enough to fill the requested days, with spares). Per item: name,
   city, one-line description, typical duration, real entrance/ticket fee + source URL.
3. HOTELS - per city, several real properties at/above the minimum rating: name, stars,
   area/location (for pilgrimage: distance to the Haram), realistic price/room/night
   (given currency) + source URL.
4. TRANSFERS - realistic ECONOMY costs for the key legs (airport->hotel, hotel->
   excursion, intercity, hotel->airport), using only the allowed transfer types.
5. SEASON - how the requested months affect price/crowds (for pilgrimage: Ramadan and
   Hajj-season surges).

OUTPUT (plain text / markdown, NO JSON)
A) Overview (2-3 sentences). B) DMC DIRECTORY (numbered, full contact + source).
C) EXCURSIONS (grouped by city, fee + source). D) HOTELS (grouped by city, stars/area/
price + source). E) TRANSFERS (economy legs + prices). F) PRICE REFERENCES (item |
estimate | currency | basis | URL). Be thorough and concrete.
""" + "\n" + PILGRIMAGE_INTEL


def build_research_user(inp: UserInput) -> str:
    lines = [
        "Build the destination research dossier for this request.",
        "",
        f"- Region / Country: {inp.region} / {inp.country}",
        f"- Cities: {', '.join(inp.cities) or '(choose the best cities/route for this country)'}",
        f"- Landmarks of interest: {', '.join(inp.landmarks) or '(discover the key ones)'}",
        f"- Trip length: {inp.number_of_days} days / {inp.nights()} nights",
        f"- Group size / seats: {inp.group_size} / {inp.seats_per_tour}",
        f"- Moods / theme: {', '.join(inp.package_moods) or 'general'}",
        f"- Traveler types: {', '.join(inp.package_types) or 'general'}",
        f"- Age range: {inp.age_range} | Child age range: {inp.child_age_range}",
        f"- Child friendly: {inp.is_child_friendly} | Accessible: {inp.is_handicap_accessible}"
        f" | Insurance: {inp.is_insurance_required}",
        f"- Minimum hotel rating: {inp.hotel_rating or str(inp.min_hotel_stars) + '-Star'}",
        f"- Accommodation type: {', '.join(inp.accommodation_type) or 'Hotels'}",
        f"- Room category: {inp.room_category or 'Standard Rooms'}",
        f"- Allowed transfer types: {', '.join(inp.transfer_types) or 'economy coach/van'}",
        f"- Guide languages: {', '.join(inp.guide_languages) or 'English'}",
        f"- Meal preferences: {', '.join(inp.meal_preferences) or 'standard'}",
        f"- Travel months: {', '.join(inp.travel_months) or 'flexible'} | "
        f"years: {', '.join(inp.travel_years) or 'flexible'}",
        f"- Currency: {inp.currency}",
        f"- Must include: {', '.join(inp.must_include) or 'none'}",
        f"- Must exclude: {', '.join(inp.must_exclude) or 'none'}",
        f"- Special requirements: {inp.special_requirements or 'none'}",
        f"- Distinct packages to support: {inp.package_count} "
        f"(find at least {inp.package_count} real DMCs + plenty of excursions)",
    ]
    if _is_pilgrimage(inp):
        lines.append("- NOTE: This is an UMRAH/HAJJ pilgrimage package - apply the "
                     "pilgrimage intelligence (Haram distances, rituals, Jeddah/Madinah "
                     "logistics, visa/Nusuk context).")
    lines += ["", "Use web_search extensively. Source every DMC, hotel, excursion fee and "
              "transfer price. Do NOT invent contact details."]
    return "\n".join(lines)


# ======================================================================
#  STAGE 2 - FORGE (structure)
# ======================================================================

PACKAGE_SKELETON = {
    "skuId": "<provided>", "dmcId": "<provided>", "packageId": "<provided>",
    "dmcApproved": False, "adminApproved": "PENDING", "name": "string",
    "packageMood": [{"id": "string", "value": "string"}], "subMood": [],
    "createdAt": "<provided>", "updatedAt": "<provided>",
    "destinations": [{"regions": {"id": "string", "value": "string"},
                      "country": {"id": "string", "value": "string"},
                      "city": [{"id": "string", "value": "string"}], "landmarks": []}],
    "image": [], "numberOfDays": 0, "tourDetail": "rich 160-220 word description",
    "ageRange": {"id": "string", "value": "string"},
    "isChildFriendly": True, "isHandicapAccessible": False, "isInsuranceRequired": False,
    "promotionPercentage": 0, "seatsPerTour": 0, "groupSize": 0,
    "pkgType": [{"id": "string", "value": "string"}],
    "tourPlan": {"arrival": "Arrival at <Airport>, meet & greet, transfer to hotel",
                 "accommodation": [{"city": {"id": "string", "value": "string"},
                                    "country": {"id": "string", "value": "string"},
                                    "serviceId": "real hotel name", "roomId": ["Standard Rooms"],
                                    "noOfNights": 0}],
                 "departure": "Transfer to <Airport> for departure"},
    "numberTravelerPrice": [],
    "mealSummary": {"availableMealPref": [{"id": "string", "value": "string"}],
                    "breakfast": {"numberOfMeals": 0, "desc": "string"},
                    "lunch": {"numberOfMeals": 0, "desc": "string"},
                    "dinner": {"numberOfMeals": 0, "desc": "string"}},
    "transportation": [{"day": 1,
                        "from": {"location": "string", "transferPoint": "string", "time": "ISO datetime"},
                        "to": {"location": "string", "transferPoint": "string", "time": "ISO datetime"},
                        "availableType": [{"id": "string", "value": "string"}]}],
    "transportationUpgrade": {"isTransportationUpgrade": False, "upgradeName": "", "upgradePrice": 0},
    "itineraryDetail": [{"day": 1, "detail": "140-200 word vivid day plan"}],
    "policy": {"pkg": "80-140 word booking & cancellation policy", "ubidtours": False},
    "travelService": {"included": ["string"], "notIncluded": ["string"]},
    "packageAvailability": [{"pkgDays": [{"id": "string", "value": "string"}],
                             "pkgMonths": [{"id": "string", "value": "string"}],
                             "pkgYears": [{"id": "string", "value": "string"}],
                             "overRideBasePrice": 0, "overRideSingleSuplimentPrc": 0,
                             "overRideSeatsPerTour": 0, "overRideChildDiscountPrice": 0,
                             "overRideInfantDiscountPrice": 0, "overRideGroupDiscountPrice": 0,
                             "overRideMisc1": None, "overRideMisc2": None, "overRideMisc3": None,
                             "adminOverRideBasePrice": 0, "adminOverRideChildDiscountPrice": 0,
                             "adminOverRideInfantDiscountPrice": 0, "adminOverRideGroupDiscountPrice": 0}],
    "basePrice": 0, "singleSuplimentPrc": 0, "childDiscountPrice": 0,
    "childAgeRange": {"id": "string", "value": "string"},
    "infantDiscountPrice": 0, "misc1": 0, "misc2": 0, "misc3": 0,
    "adminBasePrice": 0, "adminChildDiscountPrice": 0, "adminInfantDiscountPrice": 0,
    "isActive": True, "isDeleted": False, "isConverted": False, "isTopRated": False,
}

DMC_INFO_SKELETON = {
    "name": "string", "legal_name": "string|null", "country": "string", "city": "string",
    "address": "string|null", "phone": "string|null", "whatsapp": "string|null",
    "email": "string|null", "website": "string|null", "specialisation": "string",
    "languages": ["string"], "why_recommended": "string", "source_url": "string|null",
    "verified": False,
}

STRUCTURE_SYSTEM = """\
ROLE
You are "FORGE", a meticulous enterprise travel-data engineer. You turn a research
dossier into ONE valid JSON object that EXACTLY matches a fixed platform schema, plus
the offering DMC's contact card and the price references. The output is ingested by
software AND later scraped from a PDF, so it must be perfect, complete and consistent.

OUTPUT CONTRACT
- Return ONLY one JSON object: { "package": {...}, "dmc_info": {...}, "price_references": [...] }.
- No markdown, no code fences, no commentary.
- "package" contains EVERY key in the skeleton, same nesting & key names (including the
  literal key "from" inside transportation). subMood=[], image=[], promotionPercentage=0.
- Copy the PROVIDED skuId/dmcId/packageId/createdAt/updatedAt verbatim.
- Use the PROVIDED IDS verbatim for packageMood, pkgType, availableMealPref, transfer
  types, region, country, cities, ageRange, childAgeRange, pkgDays, pkgMonths, pkgYears.
- For accommodation.roomId use the provided room category value if supplied.
- Numbers are plain numbers (no symbols/commas/ranges); 0 if unknown.

REALISM RULES (the entire point)
- ITINERARY: one entry per day (1..numberOfDays). Each day reads like a real operator's
  plan, references REAL named excursions/landmarks from the dossier, and flows logically
  (arrival day = airport meet & greet + transfer + check-in + light nearby activity;
  middle days = full excursions; final day = checkout + airport transfer). 140-200 words.
- TRANSPORTATION: granular legs mirroring the itinerary - Day 1 Airport->Hotel; excursion
  days Hotel-><Attraction> and <Attraction>->Hotel; intercity legs; final day Hotel->
  Airport. Realistic from/to location + transferPoint + ISO datetime. availableType only
  from the allowed transfer types.
- ACCOMMODATION: one entry per city stayed in; serviceId = a REAL hotel name from the
  dossier at/above the rating; noOfNights summing to total nights.
- MEALS: counts consistent with the itinerary; availableMealPref = requested preferences.
- travelService.included/notIncluded: concrete; honour must-include / must-exclude; if a
  guide language is given, include a guide in that language.
- packageAvailability[0]: pkgDays/pkgMonths/pkgYears from the provided ids; overrides 0/null.
- PILGRIMAGE: if Umrah/Hajj, weave in Ihram/Tawaf/Sa'i (or Hajj rites), Makkah & Madinah
  Ziyarat, Haram-distance hotels, and Jeddah/Madinah transfer legs.

DMC CARD
- dmc_info = the REAL DMC assigned to THIS variant (from the dossier directory). Fill every
  field you have a source for; null where unknown. NEVER fabricate phone/email/website.
  verified=true only if from a live source.

PRICING (estimated, sourced)
- basePrice = realistic per-person NET ground cost (given currency), built from the dossier
  (hotels + transfers + meals + excursions + guide [+ insurance if required]).
- childDiscountPrice < base; singleSuplimentPrc = single supplement; infantDiscountPrice
  usually 0. admin* = net increased by the given admin margin, rounded.
- price_references: one row per real cost driver used, with item, estimate, currency, basis,
  source_url (real URL if available), note.

VARIANCE
- Each variant is the SAME destination but genuinely DISTINCT: a DIFFERENT real DMC,
  DIFFERENT hotels, and a distinct angle/tier/route (value vs comfort vs premium; for
  pilgrimage: economy-distance vs premium Haram-view), still realistic and within all
  constraints.
"""


def build_structure_user(brief, inp, provided, var_index, var_total) -> str:
    return (
        f"Build variant {var_index} of {var_total} now (same destination, distinct package).\n\n"
        f"Currency: {inp.currency}\n"
        f"numberOfDays: {inp.number_of_days} | nights: {inp.nights()}\n"
        f"seatsPerTour: {inp.seats_per_tour} | groupSize: {inp.group_size}\n"
        f"minimum hotel rating: {inp.hotel_rating or str(inp.min_hotel_stars) + '-Star'}\n"
        f"accommodation type: {', '.join(inp.accommodation_type) or 'Hotels'}\n"
        f"room category (use in roomId): {inp.room_category or 'Standard Rooms'}\n"
        f"guide languages: {', '.join(inp.guide_languages) or 'English'}\n"
        f"admin margin: {provided['admin_margin']} "
        f"(adminBasePrice = round(basePrice * (1 + margin)))\n"
        f"flags: isChildFriendly={inp.is_child_friendly}, "
        f"isHandicapAccessible={inp.is_handicap_accessible}, "
        f"isInsuranceRequired={inp.is_insurance_required}, isActive={inp.is_active}, "
        f"isTopRated={inp.is_top_rated}, ubidtours_policy={inp.ubidtours_policy}\n"
        + ("PILGRIMAGE PACKAGE: apply Umrah/Hajj rules.\n" if _is_pilgrimage(inp) else "")
        + "\n=== PROVIDED IDS (copy verbatim) ===\n"
        f"{json.dumps(provided['ids'], indent=2, ensure_ascii=False)}\n\n"
        "=== PROVIDED SYSTEM FIELDS (copy verbatim) ===\n"
        f"{json.dumps(provided['system_fields'], indent=2)}\n\n"
        "=== PACKAGE SKELETON (shape only) ===\n"
        f"{json.dumps(PACKAGE_SKELETON, indent=2)}\n\n"
        "=== DMC_INFO SKELETON ===\n"
        f"{json.dumps(DMC_INFO_SKELETON, indent=2)}\n\n"
        "=== RESEARCH DOSSIER (shared) ===\n"
        f"{brief}\n\n"
        'Return ONLY: {"package": {...}, "dmc_info": {...}, "price_references": [...]}'
    )


FALLBACK_NOTE = (
    "(No live web research available; build from expert domain knowledge and label every "
    "price as an INDICATIVE ESTIMATE. Provide realistic DMC names but set phone/email/"
    "website to null and verified=false since they are unverified.)"
)
