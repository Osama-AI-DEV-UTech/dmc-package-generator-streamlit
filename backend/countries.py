"""Country dropdown (from platform metadata) + city dropdown (rich global data).

Countries come from the platform metadata so they carry real platform ids.
Cities for a chosen country come from the bundled global dataset (so popular
tourist cities like Mecca/Medina/Cappadocia are available); the UI also accepts
free-text cities, so coverage gaps never block the user.
"""
from __future__ import annotations

import json
import os
from functools import lru_cache

from . import metadata as meta

_DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "data", "countries_cities.json")

POPULAR = {
    "United States": ["New York", "Los Angeles", "Las Vegas", "San Francisco",
                      "Miami", "Orlando", "Chicago", "Washington", "Boston", "Seattle"],
    "France": ["Paris", "Nice", "Lyon", "Marseille", "Bordeaux", "Cannes", "Strasbourg"],
    "Italy": ["Rome", "Venice", "Florence", "Milan", "Naples", "Pisa", "Verona"],
    "Spain": ["Madrid", "Barcelona", "Seville", "Valencia", "Granada", "Malaga"],
    "United Kingdom": ["London", "Edinburgh", "Manchester", "Liverpool", "Oxford", "Cambridge"],
    "Turkey": ["Istanbul", "Cappadocia", "Antalya", "Izmir", "Bodrum", "Ankara", "Pamukkale"],
    "United Arab Emirates": ["Dubai", "Abu Dhabi", "Sharjah", "Ras Al Khaimah", "Fujairah"],
    "Japan": ["Tokyo", "Kyoto", "Osaka", "Hiroshima", "Nara", "Sapporo", "Hakone"],
    "Thailand": ["Bangkok", "Phuket", "Chiang Mai", "Pattaya", "Krabi", "Koh Samui"],
    "India": ["Delhi", "Agra", "Jaipur", "Mumbai", "Goa", "Kerala", "Udaipur", "Varanasi"],
    "Egypt": ["Cairo", "Luxor", "Aswan", "Hurghada", "Sharm El Sheikh", "Alexandria", "Giza"],
    "Indonesia": ["Bali", "Jakarta", "Yogyakarta", "Lombok", "Ubud", "Surabaya"],
    "Greece": ["Athens", "Santorini", "Mykonos", "Crete", "Rhodes", "Thessaloniki"],
    "Morocco": ["Marrakech", "Casablanca", "Fes", "Rabat", "Chefchaouen", "Tangier"],
    "Malaysia": ["Kuala Lumpur", "Penang", "Langkawi", "Malacca", "Kota Kinabalu"],
    "Switzerland": ["Zurich", "Geneva", "Lucerne", "Interlaken", "Zermatt", "Bern"],
    "Germany": ["Berlin", "Munich", "Frankfurt", "Hamburg", "Cologne", "Heidelberg"],
    "Mexico": ["Cancun", "Mexico City", "Playa del Carmen", "Tulum", "Cabo San Lucas"],
    "Pakistan": ["Lahore", "Karachi", "Islamabad", "Skardu", "Hunza", "Murree", "Naran"],
    "Saudi Arabia": ["Mecca", "Medina", "Jeddah", "Riyadh", "AlUla", "Taif", "Dammam"],
    "Nepal": ["Kathmandu", "Pokhara", "Nagarkot", "Chitwan", "Lumbini"],
    "Maldives": ["Male", "Maafushi", "Hulhumale"],
}

MIN_CITIES_CAP = 1200


@lru_cache(maxsize=1)
def _global() -> dict:
    try:
        with open(_DATA, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}


def list_countries() -> list[str]:
    countries = meta.country_options()
    if countries:
        return countries
    g = _global()
    return sorted(g.keys()) if g else ["Saudi Arabia", "United Arab Emirates", "Turkey"]


def cities_for(country: str) -> list[str]:
    g = _global()
    key = country if country in g else meta.alias_for_cities(country)
    cities = g.get(key, []) or []
    popular = [c for c in POPULAR.get(country, POPULAR.get(key, [])) if c]
    pop_set = set(popular)
    rest = [c for c in cities if c not in pop_set]
    ordered = popular + rest
    if len(ordered) > MIN_CITIES_CAP:
        ordered = popular + rest[: MIN_CITIES_CAP - len(popular)]
    return ordered
