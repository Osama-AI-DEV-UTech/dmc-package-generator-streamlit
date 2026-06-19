# 🧭 Enterprise DMC Package Generator (v4)

Enter a few details → get **N distinct, ready-to-sell ground packages** for the
same destination, each with a **real DMC's full contact details**, a realistic
day-by-day itinerary (airport → hotel → excursions → airport), live-sourced
prices, and **two PDFs per package**:

- **Full copy (your copy)** — everything: DMC details **+** prices + all package data.
- **DMC / operator copy** — **no DMC details, no prices**, everything else intact
  (itinerary, hotels, transfers, meals, inclusions, availability, policy, data sheet).

Each PDF has its **own download button**. Provider: **OpenAI only** (web search for
live DMCs / hotels / fares).


## 🚀 Deploy free on Streamlit Cloud
This UI runs the generator **in-process** (no separate FastAPI server needed), so it deploys as a single Streamlit app. Full step-by-step in **DEPLOY.md**.

## Platform metadata (data/metadata.json)
All dropdown options and every id/value the generator emits come from the
platform's authoritative `dmcCustomPackage` metadata, so packages are natively
compatible. Categories used: packageMood, pkgType, availableType (transfers),
availableMealPref, region, countries, cities, ageGroups, childAgeRange, rating,
accommodation, roomCategory, guideLanguages, pkgDays, pkgMonths, pkgYears.
Values outside the metadata (e.g. a city not on the curated list) get a stable
deterministic UUID so output always validates.

### Umrah & Hajj
Added on top of the platform moods: **Umrah**, **Hajj**, **Religious & Pilgrimage**.
When selected (or country = Saudi Arabia), the engine applies pilgrimage
intelligence: Ihram/Tawaf/Sa'i (and Hajj rites), Makkah & Madinah Ziyarat,
Haram-distance hotels, and Jeddah/Madinah transfer logistics.

## What it does
- **How many packages?** (1–10) → that many *different* packages (different DMC,
  hotels, route/angle) for the same location.
- **Complete DMC card** per package: name, phone, WhatsApp, email, website,
  address, languages, specialisation, source — never fabricated (null if unknown).
- **Realistic itinerary + granular transfers** built from real excursions.
- Output package object matches the platform's `package.json` **exactly**
  (including the reserved `from` key in transportation).
- Global **country dropdown → related cities dropdown** (+ free-text cities).
- Metadata-driven inputs: hotel rating, accommodation type, room category
  (→ `roomId`), guide languages, age range, child age range, region.

## Setup
```bash
pip install -r requirements.txt
cp .env.example .env          # then put your OPENAI_API_KEY in .env
```

## Run
```bash
uvicorn backend.main:app --port 8000     # terminal 1
streamlit run streamlit_app.py           # terminal 2
```
Or simply: `bash run.sh`

## API
- `POST /api/generate` → `{ request_id, count, packages:[{ index, package, dmc_info,
  price_references, currency, pdf_url_full, pdf_url_dmc }], sources, warnings }`
- `GET  /api/download/{request_id}/{index}/{kind}` → `kind` ∈ {`full`, `dmc`}
- `GET  /api/request/{request_id}` → stored result as JSON
- `GET  /health`

## Layout
```
backend/
  config.py        settings (.env)
  metadata.py      authoritative platform metadata (real ids) + Umrah/Hajj moods
  countries.py     country dropdown (metadata) + city dropdown (global data)
  inputs.py        user input model
  schema.py        exact package.json models + DMCInfo + PriceReference
  prompts.py       ATLAS (research) + FORGE (structure), pilgrimage-aware
  openai_client.py OpenAI Responses (web search) + Chat Completions
  generator.py     1 research pass → N distinct variants (isolated + retry)
  pdf.py           two enterprise PDFs per package (full / dmc)
  main.py          FastAPI app
data/
  metadata.json           platform metadata payload
  countries_cities.json   250 countries / 142k cities
streamlit_app.py   advanced UI (request + response only)
```

## Notes
Prices are AI estimates from the listed sources — confirm with the DMC before
selling. System fields (skuId / dmcId / packageId / timestamps) are generated
server-side per package.
