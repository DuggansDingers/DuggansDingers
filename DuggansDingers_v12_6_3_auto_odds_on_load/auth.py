from __future__ import annotations

import hashlib
import hmac
import os
import time
import streamlit as st
from dotenv import load_dotenv

load_dotenv()


def _secret(name: str, default: str = "") -> str:
    try:
        value = st.secrets.get(name, None)
        if value is not None:
            return str(value)
    except Exception:
        pass
    return str(os.getenv(name, default))


def _cookie_manager():
    try:
        from streamlit_cookies_manager import EncryptedCookieManager
        manager = EncryptedCookieManager(
            prefix="dd_v13_",
            password=_secret("COOKIE_PASSWORD", _secret("APP_PASSWORD", "change-me")),
        )
        if not manager.ready():
            st.stop()
        return manager
    except Exception:
        return None


def _token(username: str, expires: int) -> str:
    key = (_secret("COOKIE_PASSWORD", "") or _secret("APP_PASSWORD", "")).encode()
    payload = f"{username}|{expires}"
    signature = hmac.new(key, payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}|{signature}"


def _valid_token(token: str, expected_user: str) -> bool:
    try:
        username, expires, signature = token.split("|", 2)
        if username != expected_user or int(expires) < int(time.time()):
            return False
        expected_signature = _token(username, int(expires)).rsplit("|", 1)[1]
        return hmac.compare_digest(expected_signature, signature)
    except Exception:
        return False


def require_login() -> None:
    configured_user = _secret("APP_USERNAME", "friends")
    configured_password = _secret("APP_PASSWORD", "")
    cookies = _cookie_manager()

    if st.session_state.get("dd_authenticated", False):
        return
    if cookies and _valid_token(cookies.get("auth_token", ""), configured_user):
        st.session_state.dd_authenticated = True
        st.session_state.dd_username = configured_user
        return

    st.markdown(
        '''
<style>
[data-testid="stSidebar"],[data-testid="stSidebarCollapsedControl"]{display:none!important}
.block-container{max-width:520px!important;padding:4vh 18px 30px!important}
.dd-login-shell{padding:28px 24px 22px;border:1px solid rgba(77,195,255,.42);border-radius:24px;background:linear-gradient(150deg,rgba(11,31,54,.98),rgba(3,11,22,.98));box-shadow:0 28px 80px rgba(0,0,0,.48),0 0 42px rgba(35,146,255,.14);text-align:center;overflow:hidden;position:relative}
.dd-login-shell:before{content:"";position:absolute;inset:-50% 25% auto -25%;height:260px;background:radial-gradient(circle,rgba(30,160,255,.25),transparent 64%);pointer-events:none}
.dd-login-mark{font-family:Impact,'Arial Black',sans-serif;font-style:italic;font-size:2.45rem;line-height:.88;letter-spacing:.02em;color:#fff;text-shadow:0 3px 0 #124ca2,0 0 22px rgba(54,179,255,.48);position:relative}
.dd-login-mark span{display:block;color:#4db9ff;text-shadow:0 3px 0 #5225c7,0 0 22px rgba(184,66,255,.55)}
.dd-login-kicker{margin-top:10px;color:#8ddcff;font-size:.72rem;font-weight:900;letter-spacing:.24em;text-transform:uppercase}
.dd-login-copy{color:#aebed0;margin:18px auto 0;max-width:360px;font-size:.92rem}
.dd-login-divider{height:1px;background:linear-gradient(90deg,transparent,#2c79b7,transparent);margin:22px 0 5px}
div[data-testid="stTextInput"] input{min-height:48px;border-radius:12px!important;background:#071727!important;border:1px solid #285e89!important}
.stButton>button{min-height:50px;border-radius:12px!important;font-weight:900!important;background:linear-gradient(90deg,#168cff,#6f3cff)!important;border:1px solid #62d3ff!important;box-shadow:0 10px 25px rgba(22,140,255,.25)!important}
@media(max-width:600px){.block-container{padding:2vh 14px 24px!important}.dd-login-shell{padding:24px 18px 18px}.dd-login-mark{font-size:2.05rem}}
</style>
<div class="dd-login-shell"><div class="dd-login-mark">DUGGAN'S <span>DINGERS</span></div><div class="dd-login-kicker">Home Run Intelligence</div><div class="dd-login-copy">Private access for invited friends. Sign in to open today’s live model board.</div><div class="dd-login-divider"></div></div>
''',
        unsafe_allow_html=True,
    )

    if not configured_password:
        st.error("Login is not configured. Add APP_PASSWORD to Streamlit Secrets.")
        st.stop()

    remembered_user = cookies.get("remembered_user", "") if cookies else ""
    with st.form("dd_login_form", clear_on_submit=False):
        username = st.text_input("Username", value=remembered_user, autocomplete="username", placeholder="Enter username")
        password = st.text_input("Password", type="password", autocomplete="current-password", placeholder="Enter password")
        c1, c2 = st.columns(2)
        remember = c1.checkbox("Remember username", value=bool(remembered_user))
        keep_signed_in = c2.checkbox("Keep me signed in", value=False, help="Stay signed in on this device for 30 days.")
        submitted = st.form_submit_button("Sign in securely", use_container_width=True)

    if submitted:
        valid_user = hmac.compare_digest(username.strip(), configured_user)
        valid_password = hmac.compare_digest(password, configured_password)
        if valid_user and valid_password:
            st.session_state.dd_authenticated = True
            st.session_state.dd_username = username.strip()
            if cookies:
                cookies["remembered_user"] = username.strip() if remember else ""
                if keep_signed_in:
                    expires = int(time.time()) + 30 * 24 * 60 * 60
                    cookies["auth_token"] = _token(username.strip(), expires)
                else:
                    cookies["auth_token"] = ""
                cookies.save()
            st.rerun()
        else:
            st.error("That username or password is incorrect.")

    st.caption("Your login and API keys stay encrypted in Streamlit Secrets.")
    st.stop()


def render_logout() -> None:
    columns = st.columns([8, 1.2])
    with columns[1]:
        if st.button("Log out", use_container_width=True, key="dd_logout"):
            cookies = _cookie_manager()
            if cookies:
                cookies["auth_token"] = ""
                cookies.save()
            for key in ("dd_authenticated", "dd_username"):
                st.session_state.pop(key, None)
            st.rerun()
