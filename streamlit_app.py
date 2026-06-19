"""Streamlit UI — Enterprise DMC Package Generator (in-process, deploy-ready).

Runs the WHOLE thing inside Streamlit — no separate FastAPI server needed.
Perfect for Streamlit Community Cloud (free).

  Local : streamlit run streamlit_app.py   (key from .env or .streamlit/secrets.toml)
  Cloud : set OPENAI_API_KEY in the app's Secrets, then deploy.

(The FastAPI app in backend/main.py still exists for your real API/scraper use;
 this UI just calls the generator directly so it can run as a single process.)
"""
from __future__ import annotations

import os
import tempfile

import streamlit as st

<<<<<<< HEAD
import auth

=======
>>>>>>> cc002af36067b30f97bc2563e88f27c612b8d4c9
st.set_page_config(page_title="DMC Package Generator", page_icon="🧭", layout="wide")

# ---- API key: Streamlit secrets first, then environment -----------------
def _secret(name, default=""):
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return os.getenv(name, default)

from backend.config import settings  # noqa: E402
settings.openai_api_key = _secret("OPENAI_API_KEY", settings.openai_api_key)
settings.openai_model = _secret("OPENAI_MODEL", settings.openai_model)
settings.openai_research_model = _secret("OPENAI_RESEARCH_MODEL", settings.openai_research_model)
_ws = _secret("ENABLE_WEB_SEARCH", "true")
settings.enable_web_search = str(_ws).strip().lower() in ("1", "true", "yes", "on")
try:
    settings.admin_margin = float(_secret("ADMIN_MARGIN", settings.admin_margin))
except Exception:
    pass

from backend import countries as geo  # noqa: E402
from backend import metadata as meta  # noqa: E402
from backend.generator import generate  # noqa: E402
from backend.inputs import UserInput  # noqa: E402
from backend.openai_client import OpenAIError  # noqa: E402
from backend.pdf import build_package_pdf  # noqa: E402

st.markdown("""
<style>
  .block-container{padding-top:1.6rem;max-width:1200px}
  .hero{background:linear-gradient(135deg,#0f1a2b,#1f2f48);color:#fff;border-radius:16px;
        padding:24px 30px;border-bottom:4px solid #c9772f;margin-bottom:6px}
  .hero h1{margin:0;font-size:22px}
  .hero p{margin:4px 0 0;color:#f3e3d4;font-size:13px}
  .tag{display:inline-block;background:#c9772f;color:#fff;font-size:11px;font-weight:700;
       padding:3px 11px;border-radius:999px;margin:3px 5px 0 0}
  .card{background:#fff;border:1px solid #e3e7ee;border-radius:14px;padding:0;margin:14px 0;
        box-shadow:0 8px 26px rgba(20,30,50,.06);overflow:hidden}
  .card-head{background:linear-gradient(135deg,#15233a,#22344f);color:#fff;padding:16px 20px}
  .card-head .t{font-size:17px;font-weight:700}
  .card-head .s{font-size:12px;color:#cdd7e6;margin-top:2px}
  .dmc{background:#eaf4f3;border:1px solid #bfe0dc;border-radius:10px;padding:14px 16px;margin:6px 0 12px}
  .lbl{font-size:11px;color:#6a778c;font-weight:700;text-transform:uppercase}
  .sec{font-size:11px;font-weight:800;color:#c9772f;letter-spacing:.5px;text-transform:uppercase;margin:14px 0 4px}
  .verified{color:#1f6f6b;font-weight:700}
  .unverified{color:#b4762f;font-weight:700}
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='hero'><h1>🧭 Enterprise DMC Package Generator</h1>"
            "<p>Enter a few details — get complete, ready-to-sell packages with real DMC "
            "contacts, full itineraries, prices &amp; two PDFs per package (your full copy "
            "and a no-price operator copy). Umrah &amp; Hajj aware.</p></div>",
            unsafe_allow_html=True)

<<<<<<< HEAD
# 🔒 Password gate — nothing below renders (and no OpenAI call can fire) until login.
auth.require_login()

with st.sidebar:
    st.subheader("⚙️ Status")
    auth.logout_button()
=======
with st.sidebar:
    st.subheader("⚙️ Status")
>>>>>>> cc002af36067b30f97bc2563e88f27c612b8d4c9
    if settings.has_openai:
        st.success(f"OpenAI ready · model {settings.openai_model} · web search "
                   f"{'on' if settings.enable_web_search else 'off'}")
    else:
        st.error("OPENAI_API_KEY not set. Add it to .streamlit/secrets.toml (local) "
                 "or the app Secrets (Streamlit Cloud).")
    st.caption("This app runs the generator in-process — no separate backend server needed.")


@st.cache_data(show_spinner=False)
def country_list(): return geo.list_countries()
@st.cache_data(show_spinner=False)
def city_list(country): return geo.cities_for(country)


def _stars(rating):
    return int(rating[0]) if rating and rating[0].isdigit() else 3


# ======================= REQUEST =======================
st.subheader("Request")

a = st.columns([2, 1, 1, 1])
name = a[0].text_input("Package name (optional)")
number_of_days = a[1].number_input("Days", 1, 60, 5)
seats_per_tour = a[2].number_input("Seats / tour", 1, 500, 20)
group_size = a[3].number_input("Group size", 1, 500, 20)

b = st.columns([1, 2, 2])
regions = meta.region_options()
region = b[0].selectbox("Region", regions, index=regions.index("Asia") if "Asia" in regions else 0)
clist = country_list()
default_idx = clist.index("Saudi Arabia") if "Saudi Arabia" in clist else 0
country = b[1].selectbox("Country *", clist, index=default_idx)
city_opts = city_list(country)
cities_sel = b[2].multiselect("Cities (from country)", city_opts,
                              default=city_opts[:2] if city_opts else [])
extra_cities = st.text_input("Add other cities (comma separated, optional)")
cities = cities_sel + [c.strip() for c in extra_cities.split(",") if c.strip()]
landmarks = [x.strip() for x in st.text_input("Landmarks of interest (comma separated)").split(",") if x.strip()]

c = st.columns(3)
package_moods = c[0].multiselect("Package mood (incl. Umrah / Hajj)", meta.mood_options(), [])
package_types = c[1].multiselect("Traveler type", meta.traveler_options(), [])
transfer_types = c[2].multiselect("Transfer type", meta.transfer_options(), ["Coach / Bus"])

d = st.columns(4)
ratings = meta.rating_options()
hotel_rating = d[0].selectbox("Hotel rating", ratings,
                              index=ratings.index("3-Star") if "3-Star" in ratings else 0)
accommodation_type = d[1].multiselect("Accommodation type", meta.accommodation_options(), [])
room_category = d[2].selectbox("Room category", ["(any)"] + meta.room_category_options())
meal_preferences = d[3].multiselect("Meal preferences", meta.meal_options(), [])

e = st.columns(4)
ages = meta.age_options()
age_range = e[0].selectbox("Age range", ages, index=ages.index("0-99") if "0-99" in ages else 0)
child_ages = meta.child_age_options()
child_age_range = e[1].selectbox("Child age range", child_ages)
guide_languages = e[2].multiselect("Guide languages", meta.guide_language_options(), ["English"])
currency = e[3].selectbox("Currency", ["USD", "EUR", "GBP", "AED", "SAR", "PKR", "INR", "NPR", "TRY", "THB"])

f = st.columns(3)
travel_days = f[0].multiselect("Operating days", meta.day_options(), [])
travel_months = f[1].multiselect("Months", meta.month_options(), [])
travel_years = f[2].multiselect("Years", meta.year_options(), ["2026"] if "2026" in meta.year_options() else [])

g = st.columns([1, 2])
package_count = g[0].number_input("How many packages?", 1, 10, 3,
                                  help="Distinct packages for the same location.")
special_requirements = g[1].text_input("Special requirements (optional)")

h = st.columns(2)
must_include = [x.strip() for x in h[0].text_area("Must include (one per line)", height=90).split("\n") if x.strip()]
must_exclude = [x.strip() for x in h[1].text_area("Must exclude (one per line)", height=90).split("\n") if x.strip()]

i = st.columns(6)
is_child_friendly = i[0].toggle("Child friendly", True)
is_handicap_accessible = i[1].toggle("Accessible", False)
is_insurance_required = i[2].toggle("Insurance", False)
is_active = i[3].toggle("Active", True)
is_top_rated = i[4].toggle("Top rated", False)
ubidtours_policy = i[5].toggle("Ubidtours policy", False)

go = st.button(f"🚀 Generate {int(package_count)} package(s)", type="primary", use_container_width=True)


def _run(payload: dict):
    """Generate in-process and build both PDFs per package; return a plain dict."""
    inp = UserInput(**payload)
    result = generate(inp)
    tmp = tempfile.mkdtemp(prefix="dmcpkg_")
    packages = []
    for v in result.variants:
        pdfs = {}
        for kind in ("full", "dmc"):
            try:
                p = build_package_pdf(v.package, v.dmc, v.references, result.sources,
                                      v.currency, tmp, result.request_id, v.index,
                                      engine=result.engine, mode=kind)
                with open(p, "rb") as fh:
                    pdfs[kind] = fh.read()
            except Exception as exc:  # noqa: BLE001
                result.warnings.append(f"PDF ({kind}) for package {v.index} failed: {exc}")
                pdfs[kind] = b""
        packages.append({
            "index": v.index, "package": v.package.as_json(),
            "dmc_info": v.dmc.model_dump() if v.dmc else None,
            "price_references": [r.model_dump() for r in v.references],
            "currency": v.currency, "pdf_full": pdfs.get("full", b""),
            "pdf_dmc": pdfs.get("dmc", b""),
        })
    return {"request_id": result.request_id, "engine": result.engine,
            "count": len(packages), "packages": packages,
            "sources": result.sources, "warnings": result.warnings}


if go:
    if not settings.has_openai:
        st.error("OPENAI_API_KEY missing — set it in Secrets and rerun.")
        st.stop()
    if not country.strip():
        st.error("Please choose a country.")
        st.stop()
    payload = {
        "name": name or None, "number_of_days": int(number_of_days),
        "seats_per_tour": int(seats_per_tour), "group_size": int(group_size),
        "region": region, "country": country, "cities": cities, "landmarks": landmarks,
        "package_moods": package_moods, "package_types": package_types,
        "age_range": age_range, "child_age_range": child_age_range,
        "min_hotel_stars": _stars(hotel_rating), "hotel_rating": hotel_rating,
        "accommodation_type": accommodation_type,
        "room_category": None if room_category == "(any)" else room_category,
        "guide_languages": guide_languages,
        "transfer_types": transfer_types, "meal_preferences": meal_preferences,
        "travel_days": travel_days, "travel_months": travel_months, "travel_years": travel_years,
        "currency": currency, "must_include": must_include, "must_exclude": must_exclude,
        "special_requirements": special_requirements or None,
        "is_child_friendly": is_child_friendly, "is_handicap_accessible": is_handicap_accessible,
        "is_insurance_required": is_insurance_required, "is_active": is_active,
        "is_top_rated": is_top_rated, "ubidtours_policy": ubidtours_policy,
        "package_count": int(package_count),
    }
    with st.spinner(f"Researching live & building {int(package_count)} package(s)… "
                    "this can take a couple of minutes."):
        try:
            st.session_state["result"] = _run(payload)
        except OpenAIError as exc:
            st.error(f"Generation failed: {exc}")
            st.stop()
        except Exception as exc:  # noqa: BLE001
            st.error(f"Error: {exc}")
            st.stop()


# ======================= RESPONSE =======================
data = st.session_state.get("result")
if data:
    st.subheader("Response")
    st.success(f"{data['count']} package(s) generated · engine: {data.get('engine')}")
    if data.get("warnings"):
        with st.expander("Notes / warnings"):
            for w in data["warnings"]:
                st.write("• " + w)

    def money(v, c):
        try:
            return f"{c} {float(v):,.0f}"
        except Exception:
            return "—"

    for item in data["packages"]:
        pkg = item["package"]
        dmc = item.get("dmc_info")
        cur = item.get("currency", "USD")
        nights = max(pkg["numberOfDays"] - 1, 0)
        dest = ", ".join(ci["value"] for d in pkg["destinations"] for ci in d["city"]) or \
            (pkg["destinations"][0]["country"]["value"] if pkg["destinations"] else "")
        tags = "".join(f"<span class='tag'>{m['value']}</span>" for m in pkg["packageMood"])

        st.markdown(
            f"<div class='card'><div class='card-head'>"
            f"<div class='t'>Package {item['index']} · {pkg['name']}</div>"
            f"<div class='s'>{dest} · {pkg['numberOfDays']} Days / {nights} Nights · "
            f"Group up to {pkg['groupSize']} · {money(pkg['basePrice'], cur)} net/person</div>"
            f"<div style='margin-top:6px'>{tags}</div></div>", unsafe_allow_html=True)

        if dmc:
            vbadge = ("<span class='verified'>✔ verified source</span>" if dmc.get("verified")
                      else "<span class='unverified'>to be verified</span>")
            st.markdown(
                f"<div class='dmc'><div class='lbl'>Offered by (DMC)</div>"
                f"<div style='font-size:16px;font-weight:700'>{dmc.get('name','—')}</div>"
                f"<div style='font-size:12px;color:#244;margin-top:4px'>"
                f"📞 {dmc.get('phone') or '—'} &nbsp; 💬 {dmc.get('whatsapp') or '—'} &nbsp; "
                f"✉️ {dmc.get('email') or '—'}</div>"
                f"<div style='font-size:12px;color:#244'>🌐 {dmc.get('website') or '—'}</div>"
                f"<div style='font-size:12px;color:#244'>📍 {dmc.get('address') or '—'} "
                f"({dmc.get('city') or '—'}, {dmc.get('country') or '—'})</div>"
                f"<div style='font-size:12px;color:#244'>🗣️ {', '.join(dmc.get('languages') or []) or '—'} · "
                f"{dmc.get('specialisation') or '—'}</div>"
                f"<div style='font-size:12px;color:#467'>{dmc.get('why_recommended') or ''}</div>"
                f"<div style='font-size:11px;margin-top:4px'>{vbadge} · "
                f"{dmc.get('source_url') or 'no source'}</div></div>", unsafe_allow_html=True)

        kf = st.columns(5)
        kf[0].metric("Net / person", money(pkg["basePrice"], cur))
        kf[1].metric("Selling / person", money(pkg["adminBasePrice"], cur))
        kf[2].metric("Child (net)", money(pkg["childDiscountPrice"], cur))
        kf[3].metric("Single supp.", money(pkg["singleSuplimentPrc"], cur))
        kf[4].metric("Days / Nights", f"{pkg['numberOfDays']} / {nights}")

        st.markdown("<div class='sec'>Overview</div>", unsafe_allow_html=True)
        st.write(pkg["tourDetail"])

        colL, colR = st.columns([3, 2])
        with colL:
            st.markdown("<div class='sec'>Itinerary</div>", unsafe_allow_html=True)
            for d in pkg["itineraryDetail"]:
                with st.expander(f"Day {d['day']}"):
                    st.write(d["detail"])
            st.markdown("<div class='sec'>Transfers</div>", unsafe_allow_html=True)
            st.table([{"Day": t["day"], "From": t["from"]["location"], "To": t["to"]["location"],
                       "Type": ", ".join(x["value"] for x in t["availableType"])}
                      for t in pkg["transportation"]])
        with colR:
            st.markdown("<div class='sec'>Hotels</div>", unsafe_allow_html=True)
            for ac in pkg["tourPlan"]["accommodation"]:
                room = ", ".join(ac.get("roomId") or [])
                st.write(f"🏨 **{ac['serviceId']}** — {ac['city']['value']} "
                         f"({ac['noOfNights']}n{', ' + room if room else ''})")
            st.markdown("<div class='sec'>Rates</div>", unsafe_allow_html=True)
            st.table([
                {"Rate": "Base", "Net": money(pkg["basePrice"], cur), "Selling": money(pkg["adminBasePrice"], cur)},
                {"Rate": "Child", "Net": money(pkg["childDiscountPrice"], cur), "Selling": money(pkg["adminChildDiscountPrice"], cur)},
                {"Rate": "Single supp.", "Net": money(pkg["singleSuplimentPrc"], cur), "Selling": "—"},
            ])

        inc, exc = st.columns(2)
        inc.markdown("<div class='sec'>Included</div>", unsafe_allow_html=True)
        for x in pkg["travelService"]["included"]:
            inc.write(f"✓ {x}")
        exc.markdown("<div class='sec'>Not included</div>", unsafe_allow_html=True)
        for x in pkg["travelService"]["notIncluded"]:
            exc.write(f"✗ {x}")

        if item.get("price_references"):
            st.markdown("<div class='sec'>Price references</div>", unsafe_allow_html=True)
            st.table([{"Item": r["item"], "Estimate": f"{r.get('currency','')} {r.get('estimate','')}",
                       "Basis": r.get("basis", ""), "Source": r.get("source_url", "")}
                      for r in item["price_references"]])

        st.markdown("<div class='sec'>Downloads</div>", unsafe_allow_html=True)
        dl1, dl2 = st.columns(2)
        if item.get("pdf_full"):
            dl1.download_button(f"⬇ My copy — full (prices + DMC) · Pkg {item['index']}",
                                item["pdf_full"], file_name=f"package-{item['index']}-full.pdf",
                                mime="application/pdf",
                                key=f"full_{data['request_id']}_{item['index']}", use_container_width=True)
        if item.get("pdf_dmc"):
            dl2.download_button(f"⬇ For DMC — no prices/DMC · Pkg {item['index']}",
                                item["pdf_dmc"], file_name=f"package-{item['index']}-for-DMC.pdf",
                                mime="application/pdf",
                                key=f"dmc_{data['request_id']}_{item['index']}", use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)
