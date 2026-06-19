# Deploy on Streamlit Community Cloud (FREE) — step by step

Your app has TWO parts: a FastAPI backend and a Streamlit UI. Streamlit Cloud's
free plan runs only ONE process, so `streamlit_app.py` has been made to run the
**generator in-process** — it does NOT need the FastAPI server. You just deploy
the Streamlit app. (FastAPI in `backend/main.py` is still there for your own API.)

## 0) What you need
- A GitHub account (free) and a Streamlit Community Cloud account (sign in with GitHub at https://share.streamlit.io).
- Your OpenAI API key.

## 1) Put the project on GitHub
From the project folder:
```bash
git init
git add .
git commit -m "DMC Package Generator"
git branch -M main
git remote add origin https://github.com/<your-username>/dmc-package-generator.git
git push -u origin main
```
The `.gitignore` already keeps your real key (`.streamlit/secrets.toml`, `.env`) OUT of git.
Make sure these ARE committed: `streamlit_app.py`, `backend/`, `data/metadata.json`,
`data/countries_cities.json`, `requirements.txt`.

## 2) Create the app on Streamlit Cloud
1. Go to https://share.streamlit.io → **Create app** → **Deploy a public app from GitHub**.
2. Repository: `<your-username>/dmc-package-generator`  ·  Branch: `main`
   ·  Main file path: `streamlit_app.py`.
3. (Optional) **Advanced settings** → Python version: **3.12**.

## 3) Add your secret key
In **Advanced settings → Secrets** (or later: app menu → Settings → Secrets), paste:
```toml
OPENAI_API_KEY = "sk-...your-real-key..."
OPENAI_MODEL = "gpt-4o"
OPENAI_RESEARCH_MODEL = "gpt-4o"
ENABLE_WEB_SEARCH = "true"
ADMIN_MARGIN = "0.28"
<<<<<<< HEAD

# Login password (REQUIRED — the app is locked until this is set)
APP_PASSWORD = "choose-a-strong-password"
# OR multiple users instead of APP_PASSWORD:
# [passwords]
# ali  = "ali-strong-pw"
# sara = "sara-strong-pw"
```

> 🔒 **Login is mandatory.** If neither `APP_PASSWORD` nor a `[passwords]` table is
> set, the app stays locked (fail-closed) so it can never be left open to API abuse.
> After login, users stay signed in for the session; a **Log out** button is in the sidebar.
> 5 wrong attempts trigger a 60-second lockout.
=======
```
>>>>>>> cc002af36067b30f97bc2563e88f27c612b8d4c9
Click **Save**.

## 4) Deploy
Click **Deploy**. First build takes a few minutes (installing requirements). When it's
live you get a public URL like `https://<your-app>.streamlit.app`.

## Updating later
Just `git push` to `main` — Streamlit Cloud redeploys automatically. Changed secrets?
Edit them in the app's Settings → Secrets.

## Run locally (optional)
```bash
pip install -r requirements.txt
mkdir -p .streamlit && cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # add your key
streamlit run streamlit_app.py
```

## Notes / limits (free tier)
- One process, ~1 GB RAM — fine for this app. The app sleeps after inactivity and
  wakes on the next visit.
- Generation calls OpenAI live (research + one call per package), so a run of several
  packages can take 1–3 minutes; the spinner shows progress.
- Keep `package_count` modest (e.g. 3–5) for snappy runs and lower API cost.
- Your OpenAI usage is billed by OpenAI, not Streamlit.
