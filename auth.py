"""Lightweight password gate for the Streamlit app.

Credentials live in Streamlit Secrets (never in code). Two modes:

  1) Single shared password:
        APP_PASSWORD = "your-strong-password"

  2) Multiple named users (takes priority if present):
        [passwords]
        ali = "pw1"
        sara = "pw2"

Call require_login() at the very top of the app (after set_page_config). If the
visitor is not authenticated it renders a sign-in form and st.stop()s, so NO
other widgets render and NO OpenAI calls can be triggered. If no password is
configured at all, access is blocked by default (fail-closed) so the deployed
app is never left open.
"""
from __future__ import annotations

import hmac
import os
import time

import streamlit as st

MAX_ATTEMPTS = 5
LOCK_SECONDS = 60


def _secret(name: str, default: str = "") -> str:
    try:
        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:
        pass
    return os.getenv(name, default)


def _password_table() -> dict:
    try:
        if "passwords" in st.secrets:
            return {str(k): str(v) for k, v in dict(st.secrets["passwords"]).items()}
    except Exception:
        pass
    return {}


def _verify(username: str, password: str):
    """Return True / False, or None if no credentials are configured."""
    table = _password_table()
    if table:
        stored = table.get(username)
        if stored is None:
            hmac.compare_digest("x" * 12, "y" * 12)  # constant-ish time
            return False
        return hmac.compare_digest(stored, str(password))
    app_pw = _secret("APP_PASSWORD", "")
    if app_pw:
        return hmac.compare_digest(app_pw, str(password))
    return None


def require_login():
    if st.session_state.get("auth_ok"):
        return

    table = _password_table()
    configured = bool(table) or bool(_secret("APP_PASSWORD", ""))

    st.markdown("### 🔒 Sign in to continue")
    if not configured:
        st.error("Access is locked: no password is configured. In the app **Secrets**, "
                 "add `APP_PASSWORD = \"...\"` (or a `[passwords]` table), then reload.")
        st.stop()

    now = time.time()
    locked_until = st.session_state.get("lock_until", 0)
    if now < locked_until:
        st.error(f"Too many attempts. Try again in {int(locked_until - now)}s.")
        st.stop()

    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Username") if table else ""
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in", use_container_width=True)

    if submitted:
        if _verify(username, password):
            st.session_state["auth_ok"] = True
            st.session_state["auth_user"] = username or "user"
            st.session_state.pop("attempts", None)
            st.session_state.pop("lock_until", None)
            st.rerun()
        else:
            st.session_state["attempts"] = st.session_state.get("attempts", 0) + 1
            if st.session_state["attempts"] >= MAX_ATTEMPTS:
                st.session_state["lock_until"] = time.time() + LOCK_SECONDS
                st.session_state["attempts"] = 0
                st.error(f"Too many failed attempts. Locked for {LOCK_SECONDS}s.")
            else:
                left = MAX_ATTEMPTS - st.session_state["attempts"]
                st.error(f"Incorrect credentials. {left} attempt(s) left.")
    st.caption("Authorised users only. This protects the app from misuse and API abuse.")
    st.stop()


def logout_button(container=None):
    if not st.session_state.get("auth_ok"):
        return
    c = container or st.sidebar
    c.caption(f"Signed in as **{st.session_state.get('auth_user', 'user')}**")
    if c.button("🚪 Log out", use_container_width=True):
        for k in ("auth_ok", "auth_user"):
            st.session_state.pop(k, None)
        st.rerun()
