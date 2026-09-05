import streamlit as st
import json
import os
import math
from datetime import datetime, date

# ============================================================
# আমার সমিতি — Micro-Finance / Somity Management System
# Clean single-file Streamlit application
# ============================================================

st.set_page_config(
    page_title="আমার সমিতি",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------
# Configuration
# -----------------------------
DB_FILE = "database.json"
LEGACY_DB_FILE = "database"
ADMIN_USER = "admin"
ADMIN_PASS = "somity2026"

MENU_ITEMS = [
    "ড্যাশবোর্ড ও সদস্য তালিকা",
    "নতুন সদস্য যুক্ত করুন",
    "কিস্তি বা টাকা জমা নিন",
    "ঋণ বা লোন বিতরণ (Loan)",
    "ঋণের টাকা বা কিস্তি আদায়",
    "সদস্য স্টেটমেন্ট (Statement)",
]

# -----------------------------
# Utility functions
# -----------------------------
def now_text():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def money(value):
    return f"৳ {float(value or 0):,.2f}"


def safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def parse_dt(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(str(value), fmt)
        except ValueError:
            pass
    return None


def add_history(info, message):
    if "history" not in info or not isinstance(info["history"], list):
        info["history"] = []
    info["history"].append(f"{now_text()} - {message}")


def ensure_member_schema(info):
    """Keep compatibility with the user's existing database format."""
    info.setdefault("name", "")
    info["savings"] = safe_float(info.get("savings", 0))
    info["loan_principal"] = safe_float(
        info.get("loan_principal", info.get("loan", 0))
    )
    info["loan_interest"] = safe_float(info.get("loan_interest", 0))
    info.setdefault("loan_type", "নাই")
    info.setdefault("loan_date", "")
    info["loan_rate"] = safe_float(info.get("loan_rate", 0))
    info["loan_duration"] = safe_float(info.get("loan_duration", 0))
    info.setdefault("loan_duration_unit", "Months")
    info.setdefault("loan_status", "Closed" if info["loan_principal"] <= 0 else "Active")
    info.setdefault("loan_last_payment_date", info.get("loan_date", ""))
    info.setdefault("loan_original_principal", info["loan_principal"])
    info.setdefault("loan_total_interest_charged", 0.0)
    info.setdefault("loan_total_paid", 0.0)
    info.setdefault("loan_installment", 0.0)
    info.setdefault("loan_expected_total", 0.0)
    info.setdefault("loan_next_due_date", "")
    if "history" not in info or not isinstance(info["history"], list):
        info["history"] = []
    return info


def load_data():
    # Prefer the requested database.json format.
    source = DB_FILE
    if not os.path.exists(source) and os.path.exists(LEGACY_DB_FILE):
        source = LEGACY_DB_FILE

    if not os.path.exists(source):
        return {"members": {}}

    try:
        with open(source, "r", encoding="utf-8") as f:
            raw = json.load(f)
        if not isinstance(raw, dict):
            return {"members": {}}
        raw.setdefault("members", {})
        for member in raw["members"].values():
            ensure_member_schema(member)
        return raw
    except (json.JSONDecodeError, OSError):
        return {"members": {}}


def save_data(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def duration_days(duration, unit):
    duration = max(0, safe_float(duration))
    if unit == "Days":
        return max(1, int(round(duration)))
    if unit == "Weeks":
        return max(1, int(round(duration * 7)))
    return max(1, int(round(duration * 30.4375)))


def periodic_rate(annual_rate, unit):
    annual_rate = max(0.0, safe_float(annual_rate)) / 100.0
    if unit == "Days":
        return annual_rate / 365.0
    if unit == "Weeks":
        return annual_rate / 52.0
    return annual_rate / 12.0


def calculate_reducing_emi(principal, annual_rate, duration, unit):
    """
    Fixed installment using reducing-balance interest.
    Days -> daily periods, Weeks -> weekly periods, Months -> monthly periods.
    """
    p = max(0.0, safe_float(principal))
    n = max(1, int(round(safe_float(duration))))
    r = periodic_rate(annual_rate, unit)

    if p <= 0:
        return 0.0

    if r == 0:
        return p / n

    emi = p * r * ((1 + r) ** n) / (((1 + r) ** n) - 1)
    return emi


def amortization_preview(principal, annual_rate, duration, unit):
    """Return scheduled reducing-balance totals for display."""
    p = max(0.0, safe_float(principal))
    n = max(1, int(round(safe_float(duration))))
    r = periodic_rate(annual_rate, unit)
    emi = calculate_reducing_emi(p, annual_rate, n, unit)

    balance = p
    total_interest = 0.0
    rows = []

    for period in range(1, n + 1):
        interest = balance * r
        principal_part = min(balance, max(0.0, emi - interest))
        payment = interest + principal_part
        balance = max(0.0, balance - principal_part)
        total_interest += interest
        rows.append({
            "কিস্তি": period,
            "কিস্তির পরিমাণ": payment,
            "সুদ": interest,
            "মূলধন": principal_part,
            "অবশিষ্ট মূলধন": balance,
        })
        if balance <= 0.005:
            break

    return emi, total_interest, rows


def current_accrued_interest(info):
    """Interest accrued since the last loan event, using reducing balance."""
    principal = safe_float(info.get("loan_principal", 0))
    rate = safe_float(info.get("loan_rate", 0))
    unit = info.get("loan_duration_unit", "Months")
    last_dt = parse_dt(info.get("loan_last_payment_date") or info.get("loan_date"))

    if principal <= 0 or rate <= 0 or not last_dt:
        return 0.0, 0

    elapsed_days = max(0, (datetime.now() - last_dt).days)
    if elapsed_days <= 0:
        return 0.0, 0

    # Accrue continuously by day against current outstanding principal.
    accrued = principal * (rate / 100.0) * (elapsed_days / 365.0)
    return accrued, elapsed_days


def projected_due_amount(info):
    accrued, _ = current_accrued_interest(info)
    return max(0.0, safe_float(info.get("loan_principal", 0)) + accrued + safe_float(info.get("loan_interest", 0)))


def member_options(data, active_only=False):
    result = {}
    for phone, raw in data.get("members", {}).items():
        info = ensure_member_schema(raw)
        if active_only and safe_float(info.get("loan_principal", 0)) <= 0:
            continue
        result[f"{info.get('name', 'সদস্য')} ({phone})"] = phone
    return result


def loan_is_active(info):
    return safe_float(info.get("loan_principal", 0)) > 0.005


def total_savings(data):
    return sum(safe_float(m.get("savings", 0)) for m in data.get("members", {}).values())


def total_principal(data):
    return sum(safe_float(m.get("loan_principal", 0)) for m in data.get("members", {}).values())


def total_loan_interest(data):
    return sum(safe_float(m.get("loan_interest", 0)) for m in data.get("members", {}).values())


# -----------------------------
# Professional visual design
# -----------------------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Bengali:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Noto Sans Bengali', sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at 8% 8%, rgba(88, 170, 83, .12), transparent 28%),
        radial-gradient(circle at 92% 16%, rgba(145, 205, 125, .13), transparent 25%),
        linear-gradient(135deg, #f7fbf5 0%, #ffffff 48%, #f3faf2 100%);
}

.main .block-container {
    padding-top: 1.4rem;
    padding-bottom: 2rem;
    max-width: 1250px;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #f2faef 0%, #ffffff 52%, #edf8eb 100%);
    border-right: 1px solid #d9ead5;
}

section[data-testid="stSidebar"] .block-container {
    padding-top: 1.2rem;
}

.brand {
    text-align: center;
    padding: 8px 4px 18px;
}

.brand-logo {
    width: 76px;
    height: 76px;
    margin: 0 auto 10px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 38px;
    background: linear-gradient(145deg, #2f7d32, #66ad55);
    box-shadow: 0 10px 28px rgba(42, 103, 44, .22);
    border: 5px solid #e9f5e5;
}

.brand h1 {
    color: #176b2b;
    font-size: 30px;
    font-weight: 800;
    margin: 0;
}

.brand p {
    color: #5f6f63;
    margin: 3px 0 0;
    font-size: 13px;
}

.login-shell {
    min-height: 84vh;
    display: grid;
    grid-template-columns: 1.05fr .95fr;
    gap: 26px;
    align-items: center;
}

.login-left {
    position: relative;
    min-height: 690px;
    border-radius: 28px;
    padding: 48px 40px;
    overflow: hidden;
    background:
        radial-gradient(circle at 15% 18%, rgba(255,255,255,.9), transparent 24%),
        linear-gradient(180deg, #eef9ea 0%, #dff1d8 55%, #c5e6bc 100%);
    border: 1px solid #d5ead0;
    box-shadow: 0 18px 50px rgba(46, 96, 50, .10);
}

.login-left:after {
    content: "";
    position: absolute;
    left: -10%;
    right: -10%;
    bottom: -22%;
    height: 55%;
    border-radius: 50% 50% 0 0;
    background: linear-gradient(180deg, #a7d995, #80bd73);
    opacity: .65;
}

.login-copy {
    position: relative;
    z-index: 4;
    text-align: center;
}

.login-copy .big-logo {
    width: 96px;
    height: 96px;
    border-radius: 50%;
    margin: 0 auto 18px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #ffffff;
    border: 7px solid #dcefd8;
    box-shadow: 0 10px 26px rgba(39, 99, 42, .18);
    font-size: 50px;
}

.login-copy h1 {
    color: #17652a;
    font-size: clamp(42px, 5vw, 68px);
    line-height: 1.05;
    margin: 0;
    font-weight: 800;
    letter-spacing: -1px;
}

.login-copy .tagline {
    color: #52665a;
    font-size: 21px;
    margin-top: 12px;
}

.trust-pill {
    display: inline-block;
    margin-top: 18px;
    padding: 9px 19px;
    border-radius: 999px;
    background: rgba(236, 249, 232, .9);
    border: 1px solid #cfe9c9;
    color: #3d7e3b;
    font-weight: 600;
}

.landscape {
    position: absolute;
    z-index: 2;
    left: -5%;
    right: -5%;
    bottom: 0;
    height: 45%;
}

.hill-a, .hill-b {
    position: absolute;
    left: -10%;
    width: 120%;
    border-radius: 50% 50% 0 0;
}

.hill-a {
    bottom: 5%;
    height: 46%;
    background: #b8dfa9;
}

.hill-b {
    bottom: -8%;
    height: 48%;
    background: #86c776;
}

.house-row {
    position: absolute;
    z-index: 5;
    bottom: 15%;
    left: 16%;
    right: 16%;
    display: flex;
    justify-content: center;
    gap: 14px;
    align-items: flex-end;
}

.house {
    width: 92px;
    height: 68px;
    background: #f8f2dd;
    border: 3px solid #a98e61;
    position: relative;
    border-radius: 4px;
}

.house:before {
    content: "";
    position: absolute;
    left: -9px;
    top: -28px;
    border-left: 55px solid transparent;
    border-right: 55px solid transparent;
    border-bottom: 30px solid #826744;
}

.house:after {
    content: "";
    position: absolute;
    width: 18px;
    height: 28px;
    left: 35px;
    bottom: 0;
    background: #9c7a50;
}

.tree {
    position: absolute;
    z-index: 6;
    left: 39%;
    bottom: 17%;
    width: 18px;
    height: 105px;
    background: #795433;
    border-radius: 8px;
}

.tree:before {
    content: "";
    position: absolute;
    width: 115px;
    height: 115px;
    left: -49px;
    top: -82px;
    border-radius: 50%;
    background: #4e9c45;
    box-shadow: 36px 12px 0 #65ad51, -24px 25px 0 #5da84c;
}

.feature-row {
    position: relative;
    z-index: 8;
    margin-top: 330px;
    background: rgba(255,255,255,.92);
    border: 1px solid #e1eee0;
    border-radius: 22px;
    padding: 20px 10px;
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    box-shadow: 0 14px 35px rgba(38, 83, 40, .12);
}

.feature {
    text-align: center;
    padding: 5px 10px;
    border-right: 1px solid #e6eee4;
}

.feature:last-child { border-right: 0; }

.feature .icon { font-size: 28px; }

.feature b {
    display: block;
    color: #254d2b;
    margin-top: 4px;
    font-size: 14px;
}

.feature span {
    color: #718076;
    font-size: 11px;
}

.login-card {
    background: rgba(255,255,255,.96);
    border: 1px solid #e5ece4;
    border-radius: 28px;
    padding: 38px 42px 30px;
    box-shadow: 0 22px 65px rgba(32, 73, 35, .14);
}

.login-icon {
    width: 78px;
    height: 78px;
    margin: 0 auto 14px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #eaf6e6;
    border: 1px solid #d5ebd0;
    font-size: 34px;
}

.login-card h2 {
    text-align: center;
    color: #14233a;
    font-size: 34px;
    margin: 0;
}

.login-card .sub {
    text-align: center;
    color: #758078;
    margin: 8px 0 28px;
}

.login-footer {
    text-align: center;
    color: #6d7770;
    font-size: 12px;
    margin-top: 22px;
}

div.stButton > button {
    border-radius: 11px;
    min-height: 44px;
    font-weight: 600;
}

.login-card div.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #2d8b39, #55ae49);
    border: 0;
    color: white;
    min-height: 50px;
    font-size: 17px;
}

.page-title {
    background: linear-gradient(135deg, #ffffff, #f1f9ef);
    border: 1px solid #e0ecde;
    border-radius: 18px;
    padding: 17px 22px;
    margin-bottom: 18px;
    box-shadow: 0 8px 24px rgba(48, 91, 51, .06);
}

.page-title h1 {
    margin: 0;
    color: #205c2a;
    font-size: 28px;
}

.page-title p {
    margin: 4px 0 0;
    color: #718078;
    font-size: 13px;
}

.metric-card {
    background: white;
    border: 1px solid #e4eee1;
    border-radius: 18px;
    padding: 18px;
    box-shadow: 0 8px 25px rgba(48, 91, 51, .06);
}

.metric-card .label {
    color: #718078;
    font-size: 13px;
}

.metric-card .value {
    color: #1f682b;
    font-size: 27px;
    font-weight: 800;
    margin-top: 5px;
}

.member-card {
    background: #fff;
    border: 1px solid #e4eee1;
    border-radius: 16px;
    padding: 16px;
    margin: 9px 0;
    box-shadow: 0 5px 18px rgba(48, 91, 51, .05);
}

.section-card {
    background: #ffffff;
    border: 1px solid #e4eee1;
    border-radius: 20px;
    padding: 22px;
    margin-bottom: 18px;
    box-shadow: 0 8px 25px rgba(48, 91, 51, .05);
}

.stTextInput input, .stNumberInput input, .stDateInput input,
.stSelectbox div[data-baseweb="select"], .stTextArea textarea {
    border-radius: 10px !important;
}

.sidebar-note {
    margin-top: 16px;
    padding: 12px;
    border-radius: 13px;
    background: #eaf6e7;
    border: 1px solid #d5eacf;
    color: #54725a;
    font-size: 12px;
    text-align: center;
}

@media (max-width: 900px) {
    .login-shell { grid-template-columns: 1fr; }
    .login-left { min-height: 580px; }
    .feature-row { margin-top: 250px; }
}

@media (max-width: 600px) {
    .login-left { padding: 28px 15px; min-height: 510px; }
    .login-card { padding: 28px 20px; }
    .login-copy h1 { font-size: 43px; }
    .feature-row { grid-template-columns: repeat(2, 1fr); }
    .feature:nth-child(2) { border-right: 0; }
    .feature:nth-child(-n+2) { border-bottom: 1px solid #e6eee4; padding-bottom: 12px; }
}
</style>
""",
    unsafe_allow_html=True,
)

# -----------------------------
# Session state
# -----------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "page" not in st.session_state:
    st.session_state.page = MENU_ITEMS[0]


# ============================================================
# Login
# ============================================================
def login_page():
    st.markdown(
        """
<div class="login-shell">
  <div class="login-left">
    <div class="login-copy">
      <div class="big-logo">🌿</div>
      <h1>আমার সমিতি</h1>
      <div class="tagline">আপনার সমিতি, আপনার উন্নতি</div>
      <div class="trust-pill">🛡️ নিরাপদ • সহজ • স্মার্ট সমাধান</div>
    </div>

    <div class="landscape">
      <div class="hill-a"></div>
      <div class="hill-b"></div>
      <div class="tree"></div>
      <div class="house-row">
        <div class="house"></div>
        <div class="house"></div>
        <div class="house"></div>
        <div class="house"></div>
      </div>
    </div>

    <div class="feature-row">
      <div class="feature">
        <div class="icon">👥</div>
        <b>সদস্য ব্যবস্থাপনা</b>
        <span>সহজে সদস্য যোগ ও তালিকা</span>
      </div>
      <div class="feature">
        <div class="icon">🐷</div>
        <b>সঞ্চয় ব্যবস্থাপনা</b>
        <span>সঞ্চয় জমা ও উত্তোলন</span>
      </div>
      <div class="feature">
        <div class="icon">💰</div>
        <b>ঋণ ব্যবস্থাপনা</b>
        <span>ঋণ, কিস্তি ও হিসাব</span>
      </div>
      <div class="feature">
        <div class="icon">📊</div>
        <b>রিপোর্ট ও স্টেটমেন্ট</b>
        <span>স্বচ্ছ হিসাব ও রিপোর্ট</span>
      </div>
    </div>
  </div>

  <div class="login-card">
    <div class="login-icon">🔒</div>
    <h2>Admin Login</h2>
    <div class="sub">অনুগ্রহ করে আপনার অ্যাকাউন্ট দিয়ে লগইন করুন</div>
    """,
        unsafe_allow_html=True,
    )

    with st.form("secure_login_form"):
        username = st.text_input("Username", placeholder="আপনার ইউজারনেম লিখুন")
        password = st.text_input("Password", type="password", placeholder="আপনার পাসওয়ার্ড লিখুন")
        remember = st.checkbox("আমাকে মনে রাখুন", value=False)
        submitted = st.form_submit_button("🔐  লগইন করুন", type="primary", use_container_width=True)

        if submitted:
            if username.strip() == ADMIN_USER and password == ADMIN_PASS:
                st.session_state.logged_in = True
                st.session_state.remember_login = remember
                st.session_state.page = MENU_ITEMS[0]
                st.rerun()
            else:
                st.error("ইউজারনেম অথবা পাসওয়ার্ড সঠিক নয়।")

    st.markdown(
        """
    <div class="login-footer">
      🔒 আপনার তথ্য নিরাপদ ও গোপন রাখা হয়<br><br>
      © 2026 আমার সমিতি • সর্বস্বত্ব সংরক্ষিত
    </div>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )


# ============================================================
# Common UI
# ============================================================
def page_header(title, subtitle):
    st.markdown(
        f"""
<div class="page-title">
  <h1>{title}</h1>
  <p>{subtitle}</p>
</div>
""",
        unsafe_allow_html=True,
    )


def member_select(data, label, active_only=False, key=None):
    options = member_options(data, active_only=active_only)
    if not options:
        st.warning("কোনো উপযুক্ত সদস্য পাওয়া যায়নি।")
        return None
    selected = st.selectbox(label, list(options.keys()), key=key)
    return options[selected]


def sidebar():
    with st.sidebar:
        st.markdown(
            """
<div class="brand">
  <div class="brand-logo">🌿</div>
  <h1>আমার সমিতি</h1>
  <p>Micro-Finance Management</p>
</div>
""",
            unsafe_allow_html=True,
        )

        st.markdown("---")

        current_index = MENU_ITEMS.index(st.session_state.page) if st.session_state.page in MENU_ITEMS else 0
        selected = st.radio(
            "মেনু",
            MENU_ITEMS,
            index=current_index,
            key="sidebar_menu",
        )
        st.session_state.page = selected

        st.markdown("---")

        if st.button("🔒 নিরাপদ লগআউট", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

        st.markdown(
            """
<div class="sidebar-note">
  🔐 নিরাপদ ব্যবস্থাপনা<br>
  📅 স্বয়ংক্রিয় তারিখ ও সময় সংরক্ষণ
</div>
""",
            unsafe_allow_html=True,
        )


# ============================================================
# Page 1 — Dashboard
# ============================================================
def dashboard_page(data):
    page_header("📊 ড্যাশবোর্ড ও সদস্য তালিকা", "সমিতির বর্তমান সদস্য, সঞ্চয় ও ঋণের সারসংক্ষেপ")

    members = data.get("members", {})
    active_loans = sum(1 for m in members.values() if loan_is_active(m))

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="metric-card"><div class="label">মোট সদস্য</div><div class="value">{len(members)}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card"><div class="label">মোট সঞ্চয়</div><div class="value">{money(total_savings(data))}</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="metric-card"><div class="label">চলতি ঋণের মূলধন</div><div class="value">{money(total_principal(data))}</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="metric-card"><div class="label">চলতি ঋণ</div><div class="value">{active_loans}</div></div>', unsafe_allow_html=True)

    st.write("")

    if not members:
        st.info("বর্তমানে কোনো সদস্য নিবন্ধিত নেই। বাম পাশের মেনু থেকে নতুন সদস্য যুক্ত করুন।")
        return

    st.markdown("### 👥 সদস্য তালিকা")

    search = st.text_input("🔎 সদস্যের নাম বা মোবাইল দিয়ে খুঁজুন", placeholder="যেমন: Mehedi বা 017...")
    shown = 0

    for phone, raw in members.items():
        info = ensure_member_schema(raw)
        query = search.strip().lower()

        if query and query not in str(phone).lower() and query not in str(info.get("name", "")).lower():
            continue

        loan = safe_float(info.get("loan_principal", 0))
        status = "🟢 চলতি" if loan_is_active(info) else "⚪ ঋণ নেই"

        st.markdown(
            f"""
<div class="member-card">
<b>👤 {info.get('name', 'নাম নেই')}</b> &nbsp; <span style="color:#758078">📱 {phone}</span><br>
<span style="color:#54725a">💰 সঞ্চয়: <b>{money(info.get('savings', 0))}</b></span>
&nbsp;&nbsp; | &nbsp;&nbsp;
<span style="color:#7a5b35">📉 ঋণের মূলধন: <b>{money(loan)}</b></span>
&nbsp;&nbsp; | &nbsp;&nbsp;
{status}
</div>
""",
            unsafe_allow_html=True,
        )
        shown += 1

    if shown == 0:
        st.info("আপনার দেওয়া অনুসন্ধানের সাথে কোনো সদস্য পাওয়া যায়নি।")


# ============================================================
# Page 2 — New member
# ============================================================
def new_member_page(data):
    page_header("➕ নতুন সদস্য যুক্ত করুন", "নতুন সদস্যের হিসাব খুলুন এবং প্রাথমিক সঞ্চয় সংরক্ষণ করুন")

    with st.container():
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        col1, col2 = st.columns(2)

        with col1:
            phone = st.text_input("📱 সদস্যের মোবাইল নম্বর", placeholder="01XXXXXXXXX")
            name = st.text_input("👤 সদস্যের পূর্ণ নাম", placeholder="সদস্যের নাম")

        with col2:
            initial_savings = st.number_input(
                "💵 প্রাথমিক সঞ্চয় (টাকা)",
                min_value=0.0,
                step=100.0,
                value=0.0,
            )
            opening_date = st.date_input("📅 হিসাব খোলার তারিখ", value=date.today())

        st.markdown("</div>", unsafe_allow_html=True)

        if st.button("💾 সদস্যের হিসাব তৈরি করুন", type="primary", use_container_width=True):
            phone = phone.strip()
            name = name.strip()

            if not phone or not name:
                st.warning("দয়া করে সদস্যের নাম এবং মোবাইল নম্বর দিন।")
            elif not phone.isdigit() or len(phone) < 10:
                st.warning("সঠিক মোবাইল নম্বর দিন।")
            elif phone in data["members"]:
                st.error("এই মোবাইল নম্বরে ইতিমধ্যে একজন সদস্য আছেন।")
            else:
                timestamp = datetime.combine(opening_date, datetime.now().time()).strftime("%Y-%m-%d %H:%M:%S")
                info = {
                    "name": name,
                    "savings": initial_savings,
                    "loan_principal": 0.0,
                    "loan_interest": 0.0,
                    "loan_type": "নাই",
                    "loan_date": timestamp,
                    "loan_rate": 0.0,
                    "loan_duration": 0,
                    "loan_duration_unit": "Months",
                    "loan_status": "Closed",
                    "loan_last_payment_date": "",
                    "loan_original_principal": 0.0,
                    "loan_total_interest_charged": 0.0,
                    "loan_total_paid": 0.0,
                    "loan_installment": 0.0,
                    "loan_expected_total": 0.0,
                    "loan_next_due_date": "",
                    "history": [
                        f"{timestamp} - হিসাব খোলা হয়েছে। প্রাথমিক সঞ্চয় {money(initial_savings)}।"
                    ],
                }
                data["members"][phone] = info
                save_data(data)
                st.success(f"🎉 {name}-এর সদস্য হিসাব সফলভাবে তৈরি হয়েছে।")
                st.rerun()


# ============================================================
# Page 3 — Savings
# ============================================================
def savings_page(data):
    page_header("💰 কিস্তি বা টাকা জমা নিন", "সদস্যের সঞ্চয়/কিস্তির টাকা গ্রহণ করুন এবং সঙ্গে সঙ্গে হিসাব আপডেট করুন")

    phone = member_select(data, "📞 সদস্য নির্বাচন করুন", key="savings_member")
    if not phone:
        return

    info = ensure_member_schema(data["members"][phone])

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            f'<div class="metric-card"><div class="label">সদস্য</div><div class="value" style="font-size:20px">{info["name"]}</div></div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f'<div class="metric-card"><div class="label">বর্তমান সঞ্চয়</div><div class="value">{money(info["savings"])}</div></div>',
            unsafe_allow_html=True,
        )

    st.write("")

    amount = st.number_input("💵 জমার পরিমাণ (টাকা)", min_value=0.0, step=100.0, value=0.0)
    note = st.text_input("📝 নোট (ঐচ্ছিক)", placeholder="যেমন: সাপ্তাহিক সঞ্চয়")

    if st.button("✔️ জমা গ্রহণ করুন", type="primary", use_container_width=True):
        if amount <= 0:
            st.warning("জমার পরিমাণ ০-এর বেশি হতে হবে।")
        else:
            info["savings"] += amount
            message = f"সঞ্চয় জমা: +{money(amount)}"
            if note.strip():
                message += f" — {note.strip()}"
            add_history(info, message)
            save_data(data)
            st.success(f"✅ {money(amount)} সঞ্চয় সফলভাবে জমা হয়েছে।")
            st.rerun()


# ============================================================
# Page 4 — Loan disbursement
# ============================================================
def loan_page(data):
    page_header("💸 ঋণ বা লোন বিতরণ (Loan)", "Reducing Balance পদ্ধতিতে নতুন ঋণ তৈরি করুন")

    phone = member_select(data, "📞 ঋণগ্রহীতা সদস্য নির্বাচন করুন", key="loan_member")
    if not phone:
        return

    info = ensure_member_schema(data["members"][phone])

    if loan_is_active(info):
        st.warning(f"এই সদস্যের একটি চলতি ঋণ আছে: {money(info['loan_principal'])} মূলধন। নতুন ঋণ দেওয়ার আগে সেটি নিষ্পত্তি করুন।")
        return

    st.markdown(
        f'<div class="section-card"><b>👤 {info["name"]}</b><br>📱 {phone}<br>💰 বর্তমান সঞ্চয়: {money(info["savings"])}</div>',
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        principal = st.number_input("💵 ঋণের পরিমাণ (মূলধন)", min_value=0.0, step=1000.0, value=0.0)
        loan_type = st.text_input("🏷️ ঋণের ধরন", value="সাধারণ ঋণ")

    with c2:
        annual_rate = st.number_input("📊 বার্ষিক সুদের হার (%)", min_value=0.0, max_value=100.0, value=10.0, step=0.5)
        duration_unit = st.selectbox("⏱️ সময়ের একক", ["Days", "Weeks", "Months"])

    duration = st.number_input(
        f"📅 ঋণের মেয়াদ ({duration_unit})",
        min_value=1,
        max_value=1000,
        value=10 if duration_unit == "Months" else (10 if duration_unit == "Weeks" else 30),
        step=1,
    )

    if principal > 0:
        emi, scheduled_interest, schedule = amortization_preview(
            principal, annual_rate, duration, duration_unit
        )
        st.markdown(
            f"""
<div class="section-card">
<b>📉 Reducing Balance হিসাব</b><br><br>
প্রতি {duration_unit.lower()} কিস্তি: <b>{money(emi)}</b><br>
আনুমানিক মোট সুদ: <b>{money(scheduled_interest)}</b><br>
আনুমানিক মোট পরিশোধ: <b>{money(principal + scheduled_interest)}</b><br>
মেয়াদ: <b>{duration} {duration_unit}</b>
</div>
""",
            unsafe_allow_html=True,
        )

        with st.expander("📋 কিস্তির পূর্ণ হিসাব দেখুন"):
            import pandas as pd
            df = pd.DataFrame(schedule)
            for col in ["কিস্তির পরিমাণ", "সুদ", "মূলধন", "অবশিষ্ট মূলধন"]:
                df[col] = df[col].map(lambda x: round(x, 2))
            st.dataframe(df, use_container_width=True, hide_index=True)

    if st.button("🚀 ঋণ অনুমোদন ও বিতরণ করুন", type="primary", use_container_width=True):
        if principal <= 0:
            st.warning("ঋণের পরিমাণ ০-এর বেশি হতে হবে।")
            return

        timestamp = now_text()
        emi, scheduled_interest, _ = amortization_preview(
            principal, annual_rate, duration, duration_unit
        )

        info["loan_principal"] = principal
        info["loan_interest"] = 0.0
        info["loan_type"] = loan_type.strip() or "সাধারণ ঋণ"
        info["loan_date"] = timestamp
        info["loan_rate"] = annual_rate
        info["loan_duration"] = duration
        info["loan_duration_unit"] = duration_unit
        info["loan_status"] = "Active"
        info["loan_last_payment_date"] = timestamp
        info["loan_original_principal"] = principal
        info["loan_total_interest_charged"] = 0.0
        info["loan_total_paid"] = 0.0
        info["loan_installment"] = emi
        info["loan_expected_total"] = principal + scheduled_interest

        add_history(
            info,
            f"ঋণ বিতরণ: {money(principal)}; ধরন: {info['loan_type']}; "
            f"হার: {annual_rate:.2f}% বার্ষিক; মেয়াদ: {duration} {duration_unit}; "
            f"Red.-Balance কিস্তি: {money(emi)}।"
        )

        save_data(data)
        st.success(f"✅ {money(principal)} ঋণ সফলভাবে বিতরণ করা হয়েছে।")
        st.rerun()


# ============================================================
# Page 5 — Loan collection + early settlement
# ============================================================
def loan_collection_page(data):
    page_header("📉 ঋণের টাকা বা কিস্তি আদায়", "Reducing Balance অনুযায়ী কিস্তি গ্রহণ, সুদ হিসাব এবং Early Settlement")

    phone = member_select(data, "📞 চলতি ঋণ থাকা সদস্য নির্বাচন করুন", active_only=True, key="collection_member")
    if not phone:
        st.info("বর্তমানে কোনো সক্রিয় ঋণ নেই।")
        return

    info = ensure_member_schema(data["members"][phone])

    accrued, elapsed = current_accrued_interest(info)
    principal = safe_float(info.get("loan_principal", 0))
    stored_interest = safe_float(info.get("loan_interest", 0))
    current_due = principal + stored_interest + accrued

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="metric-card"><div class="label">মূলধন বাকি</div><div class="value">{money(principal)}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card"><div class="label">এখন পর্যন্ত বকেয়া সুদ</div><div class="value">{money(stored_interest + accrued)}</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="metric-card"><div class="label">আনুমানিক বর্তমান পাওনা</div><div class="value">{money(current_due)}</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="metric-card"><div class="label">শেষ লেনদেন থেকে</div><div class="value">{elapsed} দিন</div></div>', unsafe_allow_html=True)

    st.write("")

    st.markdown(
        f"""
<div class="section-card">
<b>👤 {info["name"]}</b> &nbsp; 📱 {phone}<br>
ঋণের ধরন: <b>{info.get("loan_type", "সাধারণ ঋণ")}</b> &nbsp; | &nbsp;
হার: <b>{safe_float(info.get("loan_rate", 0)):.2f}%</b> &nbsp; | &nbsp;
মেয়াদ: <b>{info.get("loan_duration", 0)} {info.get("loan_duration_unit", "Months")}</b><br>
নির্ধারিত কিস্তি: <b>{money(info.get("loan_installment", 0))}</b>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown("### 💳 কিস্তি / আংশিক পরিশোধ")

    repay = st.number_input(
        "💵 আজ কত টাকা গ্রহণ করবেন?",
        min_value=0.0,
        max_value=max(0.0, current_due),
        step=100.0,
        value=0.0,
        key="repay_amount",
    )

    allocation_preview = ""
    if repay > 0:
        interest_part = min(repay, stored_interest + accrued)
        principal_part = max(0.0, repay - interest_part)
        principal_part = min(principal_part, principal)
        allocation_preview = (
            f"সুদের অংশ: {money(interest_part)} | "
            f"মূলধন কমবে: {money(principal_part)}"
        )

    if allocation_preview:
        st.info("📌 " + allocation_preview)

    if st.button("✔️ কিস্তি / পরিশোধ গ্রহণ করুন", type="primary", use_container_width=True):
        if repay <= 0:
            st.warning("পরিশোধের পরিমাণ ০-এর বেশি হতে হবে।")
        else:
            total_interest_due = stored_interest + accrued
            interest_part = min(repay, total_interest_due)
            principal_part = min(principal, max(0.0, repay - interest_part))

            info["loan_interest"] = max(0.0, total_interest_due - interest_part)
            info["loan_principal"] = max(0.0, principal - principal_part)
            info["loan_total_paid"] = safe_float(info.get("loan_total_paid", 0)) + repay
            info["loan_total_interest_charged"] = safe_float(
                info.get("loan_total_interest_charged", 0)
            ) + interest_part
            info["loan_last_payment_date"] = now_text()

            if info["loan_principal"] <= 0.005 and info["loan_interest"] <= 0.005:
                info["loan_principal"] = 0.0
                info["loan_interest"] = 0.0
                info["loan_status"] = "Closed"
                message = f"ঋণ সম্পূর্ণ পরিশোধ: {money(repay)}। ঋণ বন্ধ হয়েছে।"
            else:
                info["loan_status"] = "Active"
                message = (
                    f"ঋণ/কিস্তি পরিশোধ: {money(repay)}; "
                    f"সুদে সমন্বয় {money(interest_part)}, "
                    f"মূলধনে সমন্বয় {money(principal_part)}।"
                )

            add_history(info, message)
            save_data(data)
            st.success("✅ পরিশোধ সফলভাবে হিসাবের সঙ্গে সমন্বয় হয়েছে।")
            st.rerun()

    st.markdown("---")
    st.markdown("### ⚡ Early Settlement")

    # Fair early settlement:
    # charge only accrued interest up to today + outstanding principal;
    # all future scheduled interest is waived.
    future_interest_waived = max(
        0.0,
        safe_float(info.get("loan_expected_total", 0))
        - safe_float(info.get("loan_total_paid", 0))
        - principal
        - stored_interest
        - accrued,
    )
    early_amount = max(0.0, principal + stored_interest + accrued)

    st.info(
        f"আজ ঋণটি সম্পূর্ণ বন্ধ করলে আনুমানিক পরিশোধযোগ্য: "
        f"**{money(early_amount)}**। "
        f"ভবিষ্যতের আনুমানিক সুদ থেকে প্রায় **{money(future_interest_waived)}** "
        f"মওকুফ হবে।"
    )

    confirm = st.checkbox(
        "আমি বুঝেছি যে Early Settlement করলে ভবিষ্যতের সুদ আর নেওয়া হবে না এবং ঋণটি সম্পূর্ণ বন্ধ হবে।",
        key="early_confirm",
    )

    if st.button("⚡ Early Settlement — ঋণ সম্পূর্ণ বন্ধ করুন", use_container_width=True):
        if not confirm:
            st.warning("আগে নিশ্চিতকরণ বক্সটি টিক দিন।")
        else:
            settlement = early_amount
            waived = future_interest_waived

            info["loan_principal"] = 0.0
            info["loan_interest"] = 0.0
            info["loan_status"] = "Closed"
            info["loan_total_paid"] = safe_float(info.get("loan_total_paid", 0)) + settlement
            info["loan_total_interest_charged"] = safe_float(
                info.get("loan_total_interest_charged", 0)
            ) + stored_interest + accrued
            info["loan_last_payment_date"] = now_text()

            add_history(
                info,
                f"Early Settlement: {money(settlement)} গ্রহণ করে ঋণ সম্পূর্ণ বন্ধ। "
                f"ভবিষ্যতের আনুমানিক সুদ ছাড়: {money(waived)}।"
            )
            save_data(data)
            st.success(f"🎉 Early Settlement সম্পন্ন। {money(waived)} ভবিষ্যৎ সুদ মওকুফ করা হয়েছে।")
            st.rerun()


# ============================================================
# Page 6 — Statement
# ============================================================
def statement_page(data):
    page_header("📋 সদস্য স্টেটমেন্ট (Statement)", "সদস্যের সঞ্চয়, ঋণ এবং তারিখ-সময় সহ সম্পূর্ণ লেনদেন ইতিহাস")

    phone = member_select(data, "📞 স্টেটমেন্ট দেখতে সদস্য নির্বাচন করুন", key="statement_member")
    if not phone:
        return

    info = ensure_member_schema(data["members"][phone])

    st.markdown(
        f"""
<div class="section-card">
<h3 style="margin-top:0;color:#205c2a">👤 {info["name"]}</h3>
📱 মোবাইল: <b>{phone}</b><br>
💰 বর্তমান সঞ্চয়: <b>{money(info.get("savings", 0))}</b><br>
📉 অবশিষ্ট ঋণ মূলধন: <b>{money(info.get("loan_principal", 0))}</b><br>
📊 ঋণের অবস্থা: <b>{info.get("loan_status", "Closed")}</b>
</div>
""",
        unsafe_allow_html=True,
    )

    if loan_is_active(info):
        accrued, elapsed = current_accrued_interest(info)
        st.info(
            f"চলতি ঋণ: মূলধন {money(info.get('loan_principal', 0))} | "
            f"বর্তমান accrued interest {money(accrued)} | "
            f"শেষ লেনদেন থেকে {elapsed} দিন।"
        )

    st.markdown("### 📜 লেনদেনের ইতিহাস")

    history = info.get("history", [])
    if not history:
        st.info("এই সদস্যের কোনো লেনদেনের ইতিহাস নেই।")
    else:
        for idx, log in enumerate(reversed(history), 1):
            st.markdown(
                f"""
<div class="member-card">
<b>{idx}.</b> {log}
</div>
""",
                unsafe_allow_html=True,
            )

    # Downloadable statement
    statement_text = (
        f"আমার সমিতি — সদস্য স্টেটমেন্ট\n"
        f"নাম: {info['name']}\n"
        f"মোবাইল: {phone}\n"
        f"সঞ্চয়: {money(info.get('savings', 0))}\n"
        f"অবশিষ্ট ঋণ: {money(info.get('loan_principal', 0))}\n"
        f"ঋণের অবস্থা: {info.get('loan_status', 'Closed')}\n\n"
        f"লেনদেনের ইতিহাস:\n" + "\n".join(history)
    )

    st.download_button(
        "📥 স্টেটমেন্ট ডাউনলোড করুন",
        data=statement_text.encode("utf-8"),
        file_name=f"statement_{phone}.txt",
        mime="text/plain",
        use_container_width=True,
    )


# ============================================================
# Main application
# ============================================================
if not st.session_state.logged_in:
    login_page()
else:
    data = load_data()

    sidebar()

    # Exact menu names intentionally match these conditions.
    if st.session_state.page == "ড্যাশবোর্ড ও সদস্য তালিকা":
        dashboard_page(data)

    elif st.session_state.page == "নতুন সদস্য যুক্ত করুন":
        new_member_page(data)

    elif st.session_state.page == "কিস্তি বা টাকা জমা নিন":
        savings_page(data)

    elif st.session_state.page == "ঋণ বা লোন বিতরণ (Loan)":
        loan_page(data)

    elif st.session_state.page == "ঋণের টাকা বা কিস্তি আদায়":
        loan_collection_page(data)

    elif st.session_state.page == "সদস্য স্টেটমেন্ট (Statement)":
        statement_page(data)
