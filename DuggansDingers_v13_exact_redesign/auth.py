from __future__ import annotations

import hmac
import os

import streamlit as st
from dotenv import load_dotenv

load_dotenv()


def _secret(name: str, default: str = "") -> str:
    """Read a value from Streamlit secrets, then fall back to local environment."""
    try:
        value = st.secrets.get(name, None)
        if value is not None:
            return str(value)
    except Exception:
        pass
    return str(os.getenv(name, default))


def require_login() -> None:
    """Stop the app until the visitor enters the configured shared login."""
    if st.session_state.get("dd_authenticated", False):
        return

    configured_user = _secret("APP_USERNAME", "friends")
    configured_password = _secret("APP_PASSWORD", "")

    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {display: none;}
        .dd-login-wrap {
            max-width: 430px;
            margin: 7vh auto 1rem auto;
            padding: 1.25rem 1.35rem .4rem 1.35rem;
            border: 1px solid rgba(255,255,255,.15);
            border-radius: 18px;
            background: rgba(10, 31, 68, .92);
            box-shadow: 0 18px 55px rgba(0,0,0,.28);
            text-align: center;
        }
        .dd-login-title {font-size: 2rem; font-weight: 800; margin-bottom: .2rem;}
        .dd-login-subtitle {opacity: .82; margin-bottom: .7rem;}
        @media (max-width: 600px) {
            .block-container {padding: 1rem 1rem 2rem 1rem;}
            .dd-login-wrap {margin-top: 3vh; padding: 1rem .8rem .3rem .8rem;}
            .dd-login-title {font-size: 1.65rem;}
        }
        </style>
        <div class="dd-login-wrap">
          <div class="dd-login-title">⚾ DuggansDingers</div>
          <div class="dd-login-subtitle">Private access for invited friends</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not configured_password:
        st.error("Login is not configured yet. Add APP_PASSWORD to Streamlit Secrets or your local .env file.")
        st.stop()

    with st.form("dd_login_form", clear_on_submit=False):
        username = st.text_input("Username", autocomplete="username")
        password = st.text_input("Password", type="password", autocomplete="current-password")
        submitted = st.form_submit_button("Log in", use_container_width=True)

    if submitted:
        user_ok = hmac.compare_digest(username.strip(), configured_user)
        password_ok = hmac.compare_digest(password, configured_password)
        if user_ok and password_ok:
            st.session_state.dd_authenticated = True
            st.session_state.dd_username = username.strip()
            st.rerun()
        else:
            st.error("Incorrect username or password.")

    st.caption("Your sportsbook and data-service keys remain hidden on the server.")
    st.stop()


def render_logout() -> None:
    """Add a compact logout control to the sidebar."""
    with st.sidebar:
        st.divider()
        st.caption(f"Signed in as {st.session_state.get('dd_username', 'friend')}")
        if st.button("Log out", use_container_width=True):
            for key in ("dd_authenticated", "dd_username"):
                st.session_state.pop(key, None)
            st.rerun()
