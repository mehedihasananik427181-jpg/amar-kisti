import json
import os
from datetime import datetime, date, timedelta

import pandas as pd
import streamlit as st


# =========================================================
# আমার সমিতি - Micro-Finance / Somity Management
# =========================================================

st.set_page_config(
    page_title="আমার সমিতি",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_FILE = "database.json"
ADMIN_USER = "admin"
ADMIN_PASS = "somity2026"

MENU = [
    "🏠 ড্যাশবোর্ড",
    "👥 সদস্য ব্যবস্থাপনা",
    "💰 সঞ্চয় জমা",
    "🏦 DPS / FDR মেয়াদি সঞ্চয়",
    "💸 ঋণ প্রদান",
    "💳 ঋণের টাকা বা কিস্তি আদায়",
    "📋 সদস্য স্টেটমেন্ট (Statement)",
    "📊 রিপোর্ট",
    "💾 ব্যাকআপ ও ডাটা",
]


# =========================================================
# CSS
# =========================================================
def apply_css():
    st.markdown(
        """
        <style>
        /* Main */
        .stApp {
            background:
                radial-gradient(circle at 10% 10%, rgba(220,245,221,.75), transparent 28%),
                radial-gradient(circle at 90% 20%, rgba(235,250,236,.8), transparent 30%),
                #f8fcf8;
        }

        .block-container {
            max-width: 1250px;
            padding-top: 1.5rem;
            padding-bottom: 2rem;
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #f2fbf2 0%, #e7f5e8 100%);
            border-right: 1px solid #d8ead9;
        }

        [data-testid="stSidebar"] .stRadio label {
            border-radius: 12px;
            padding: 8px 10px;
            margin: 2px 0;
        }

        /* Compact Login */
        .login-shell {
            max-width: 1120px;
            margin: 8px auto 0;
        }

        .brand-panel {
            min-height: 0;
            border-radius: 24px;
            padding: 34px 30px;
            background:
                radial-gradient(circle at 18% 15%, rgba(255,255,255,.8), transparent 24%),
                linear-gradient(145deg, #edf9ed 0%, #d8f0d8 55%, #c5e8c3 100%);
            border: 1px solid #d6ebd5;
            box-shadow: 0 14px 38px rgba(35,100,43,.09);
            text-align: center;
            overflow: hidden;
        }

        .brand-icon {
            width: 72px;
            height: 72px;
            margin: 0 auto 12px;
            border-radius: 50%;
            background: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 38px;
            box-shadow: 0 6px 20px rgba(39,102,45,.12);
            border: 4px solid rgba(255,255,255,.7);
        }

        .brand-title {
            font-size: clamp(38px, 4vw, 58px);
            font-weight: 900;
            color: #17652b;
            line-height: 1.1;
            margin-bottom: 8px;
        }

        .brand-subtitle {
            font-size: 18px;
            color: #4d5e50;
            margin-bottom: 16px;
        }

        .secure-pill {
            display: inline-block;
            margin: 0 auto 18px;
            padding: 8px 16px;
            border-radius: 999px;
            background: rgba(255,255,255,.65);
            border: 1px solid #c8e6c6;
            color: #2f7b39;
            font-weight: 700;
            font-size: 14px;
        }

        .feature-card {
            min-height: 92px;
            margin-top: 10px;
            padding: 13px 8px;
            text-align: center;
            background: rgba(255,255,255,.82);
            border: 1px solid #d9ead9;
            border-radius: 16px;
            box-shadow: 0 7px 18px rgba(35,100,43,.06);
        }

        .feature-icon {
            font-size: 23px;
            line-height: 1;
            margin-bottom: 7px;
        }

        .feature-title {
            font-weight: 800;
            font-size: 13px;
            color: #34513a;
        }

        .feature-text {
            font-size: 11px;
            margin-top: 3px;
            color: #68766b;
        }

        .login-footer {
            text-align: center;
            color: #7a847b;
            margin-top: 14px;
            font-size: 12px;
        }

        .login-card {
            min-height: 0;
            border-radius: 24px;
            padding: 34px 32px;
            background: rgba(255,255,255,.97);
            border: 1px solid #e1e9e2;
            box-shadow: 0 14px 38px rgba(27,75,35,.10);
        }

        .login-lock {
            width: 62px;
            height: 62px;
            margin: 0 auto 12px;
            border-radius: 50%;
            background: #eaf7e9;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 31px;
        }

        .login-title {
            text-align: center;
            font-size: 32px;
            font-weight: 850;
            color: #17243a;
            margin-bottom: 4px;
        }

        .login-help {
            text-align: center;
            color: #6d756f;
            margin-bottom: 20px;
            font-size: 14px;
        }

        @media (max-width: 900px) {
            .brand-panel, .login-card {
                padding: 28px 22px;
            }
            .login-shell {
                margin-top: 10px;
            }
        }

        @media (max-width: 600px) {
            .brand-title {
                font-size: 38px;
            }
            .login-title {
                font-size: 28px;
            }
        }

        /* Buttons */
        .stButton > button {
            border-radius: 11px;
            font-weight: 700;
            min-height: 42px;
        }

        /* Cards */
        .section-card {
            background: white;
            border: 1px solid #e4ece5;
            border-radius: 18px;
            padding: 18px;
            box-shadow: 0 8px 28px rgba(30,75,35,.06);
            margin-bottom: 18px;
        }

        .metric-card {
            background: white;
            border: 1px solid #e4ece5;
            border-radius: 18px;
            padding: 20px;
            box-shadow: 0 8px 28px rgba(30,75,35,.06);
        }

        .metric-label {
            color: #6c786e;
            font-size: 14px;
            font-weight: 700;
        }

        .metric-value {
            color: #17652b;
            font-size: 28px;
            font-weight: 900;
            margin-top: 5px;
        }

        .page-title {
            color: #17652b;
            font-weight: 900;
            margin-bottom: 2px;
        }

        .page-subtitle {
            color: #68756b;
            margin-bottom: 22px;
        }

        @media (max-width: 900px) {
            .brand-panel, .login-card {
                min-height: auto;
                padding: 35px 24px;
            }
            .feature-grid {
                grid-template-columns: repeat(2, 1fr);
            }
            .feature:nth-child(2) {
                border-right: 0;
            }
            .feature:nth-child(-n+2) {
                border-bottom: 1px solid #d9ead9;
            }
        }

        @media (max-width: 600px) {
            .brand-title {
                font-size: 42px;
            }
            .login-title {
                font-size: 30px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# Database helpers
# =========================================================
def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def parse_dt(value):
    if not value:
        return None
    try:
        return datetime.strptime(str(value), "%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return None


def money(value):
    try:
        return f"৳{float(value):,.2f}"
    except (ValueError, TypeError):
        return "৳0.00"


def load_data():
    if not os.path.exists(DB_FILE):
        return {"members": {}}

    try:
        with open(DB_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
    except (json.JSONDecodeError, OSError):
        return {"members": {}}

    if not isinstance(data, dict):
        data = {"members": {}}

    data.setdefault("members", {})
    return data


def save_data(data):
    temp_file = DB_FILE + ".tmp"
    with open(temp_file, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
    os.replace(temp_file, DB_FILE)


def ensure_member_defaults(member):
    member.setdefault("name", "")
    member.setdefault("savings", 0.0)
    member.setdefault("loan_principal", 0.0)
    member.setdefault("loan_interest", 0.0)
    member.setdefault("loan_type", "নাই")
    member.setdefault("loan_date", "")
    member.setdefault("loan_rate", 0.0)
    member.setdefault("loan_duration", 0)
    member.setdefault("loan_duration_unit", "Months")
    member.setdefault("loan_status", "closed")
    member.setdefault("loan_original_principal", 0.0)
    member.setdefault("loan_original_interest", 0.0)
    member.setdefault("loan_paid_principal", 0.0)
    member.setdefault("loan_paid_interest", 0.0)
    member.setdefault("loan_last_payment", member.get("loan_date", ""))
    member.setdefault("loan_installment_count", 0)
    member.setdefault("loan_total_installments", 0)
    member.setdefault("loan_schedule", [])
    member.setdefault("term_deposits", [])
    if not isinstance(member["term_deposits"], list):
        member["term_deposits"] = []
    member.setdefault("history", [])
    if not isinstance(member["history"], list):
        member["history"] = []
    if not isinstance(member["loan_schedule"], list):
        member["loan_schedule"] = []


def add_history(member, text):
    ensure_member_defaults(member)
    member["history"].append(f"{now_str()} - {text}")


def normalize_data(data):
    for member in data.get("members", {}).values():
        ensure_member_defaults(member)
    return data


def save_and_rerun(data):
    save_data(data)
    st.success("সফলভাবে সংরক্ষণ হয়েছে।")
    st.rerun()


# =========================================================
# Loan calculations
# =========================================================
def duration_days(duration, unit, start_date=None):
    start_date = start_date or date.today()
    duration = max(int(duration), 0)

    if unit == "Days":
        return duration
    if unit == "Weeks":
        return duration * 7
    # Months: calendar month approximation for loan calculations.
    return duration * 30


def period_days(unit):
    if unit == "Days":
        return 1
    if unit == "Weeks":
        return 7
    return 30


def calculate_schedule(principal, annual_rate, duration, unit, start_dt):
    """
    Reducing-balance schedule.
    Annual rate is converted to the actual installment period by days/365.
    Principal is divided equally across installments; interest is calculated
    on the opening principal balance of each installment period.
    """
    principal = float(principal)
    annual_rate = float(annual_rate)
    duration = int(duration)

    if principal <= 0 or duration <= 0:
        return []

    p_per_installment = principal / duration
    p_balance = principal
    schedule = []
    pdays = period_days(unit)

    for i in range(1, duration + 1):
        interest = p_balance * (annual_rate / 100.0) * (pdays / 365.0)
        principal_part = min(p_per_installment, p_balance)
        installment = principal_part + interest

        due_dt = start_dt + timedelta(days=pdays * i)

        schedule.append(
            {
                "installment_no": i,
                "due_date": due_dt.strftime("%Y-%m-%d"),
                "principal": round(principal_part, 2),
                "interest": round(interest, 2),
                "installment": round(installment, 2),
                "paid": 0.0,
                "status": "বাকি",
            }
        )
        p_balance -= principal_part

    return schedule


def outstanding_principal(member):
    return max(float(member.get("loan_principal", 0.0)), 0.0)


def elapsed_interest(member, settlement_dt=None):
    """
    Fair early-settlement interest:
    charge only for actual elapsed days on the current outstanding principal,
    instead of charging future scheduled interest.
    """
    settlement_dt = settlement_dt or datetime.now()

    principal = outstanding_principal(member)
    if principal <= 0:
        return 0.0

    annual_rate = float(member.get("loan_rate", 0.0))
    last_payment = parse_dt(member.get("loan_last_payment"))
    loan_start = parse_dt(member.get("loan_date"))

    base_dt = last_payment or loan_start
    if not base_dt:
        return 0.0

    elapsed = max((settlement_dt - base_dt).total_seconds() / 86400.0, 0.0)
    return principal * (annual_rate / 100.0) * (elapsed / 365.0)


def remaining_scheduled_interest(member):
    total = 0.0
    for row in member.get("loan_schedule", []):
        if row.get("status") != "পরিশোধ":
            total += float(row.get("interest", 0.0))
    return total


def mark_schedule_payment(member, amount):
    """
    Applies payment to oldest unpaid scheduled installments.
    Interest is paid first, then principal.
    """
    amount = float(amount)
    remaining = amount

    for row in member.get("loan_schedule", []):
        if remaining <= 0:
            break

        due_interest = max(float(row.get("interest", 0.0)) - float(row.get("paid_interest", 0.0)), 0.0)
        due_principal = max(float(row.get("principal", 0.0)) - float(row.get("paid_principal", 0.0)), 0.0)

        interest_paid = min(remaining, due_interest)
        remaining -= interest_paid

        principal_paid = min(remaining, due_principal)
        remaining -= principal_paid

        row["paid_interest"] = round(float(row.get("paid_interest", 0.0)) + interest_paid, 2)
        row["paid_principal"] = round(float(row.get("paid_principal", 0.0)) + principal_paid, 2)
        row["paid"] = round(float(row.get("paid", 0.0)) + interest_paid + principal_paid, 2)

        if (
            row["paid_interest"] >= float(row.get("interest", 0.0)) - 0.01
            and row["paid_principal"] >= float(row.get("principal", 0.0)) - 0.01
        ):
            row["status"] = "পরিশোধ"

    return remaining


# =========================================================
# Login
# =========================================================
def login_page():
    apply_css()

    st.markdown('<div class="login-shell">', unsafe_allow_html=True)
    left, right = st.columns([1.02, 0.98], gap="large")

    with left:
        st.markdown(
            '<div class="brand-panel">'
            '<div class="brand-icon">🌿</div>'
            '<div class="brand-title">আমার সমিতি</div>'
            '<div class="brand-subtitle">আপনার সমিতি, আপনার উন্নতি</div>'
            '<div class="secure-pill">🛡️ নিরাপদ · সহজ · স্মার্ট সমাধান</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        f1, f2 = st.columns(2, gap="small")
        f3, f4 = st.columns(2, gap="small")
        features = [
            (f1, "👥", "সদস্য ব্যবস্থাপনা", "সদস্য যোগ ও তালিকা"),
            (f2, "🐷", "সঞ্চয় ব্যবস্থাপনা", "সঞ্চয় জমা ও হিসাব"),
            (f3, "💰", "ঋণ ব্যবস্থাপনা", "ঋণ ও কিস্তি হিসাব"),
            (f4, "📊", "রিপোর্ট ও স্টেটমেন্ট", "স্বচ্ছ হিসাব ও রিপোর্ট"),
        ]
        for col, icon, title, text in features:
            with col:
                st.markdown(
                    f"""<div class="feature-card">
                        <div class="feature-icon">{icon}</div>
                        <div class="feature-title">{title}</div>
                        <div class="feature-text">{text}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )

    with right:
        st.markdown(
            '<div class="login-card">'
            '<div class="login-lock">🔐</div>'
            '<div class="login-title">Admin Login</div>'
            '<div class="login-help">আপনার অ্যাডমিন অ্যাকাউন্ট দিয়ে লগইন করুন</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        username = st.text_input(
            "Username",
            placeholder="আপনার ইউজারনেম লিখুন",
            key="login_username",
        )
        password = st.text_input(
            "Password",
            type="password",
            placeholder="আপনার পাসওয়ার্ড লিখুন",
            key="login_password",
        )
        remember = st.checkbox("আমাকে মনে রাখুন", key="login_remember")

        if st.button("🔐  লগইন করুন", use_container_width=True, type="primary"):
            if username.strip() == ADMIN_USER and password == ADMIN_PASS:
                st.session_state["logged_in"] = True
                st.session_state["remember"] = remember
                st.rerun()
            else:
                st.error("ইউজারনেম অথবা পাসওয়ার্ড সঠিক নয়।")

        st.markdown(
            '<div class="login-footer">'
            '🔒 আপনার তথ্য নিরাপদ ও গোপন রাখা হবে<br><br>'
            '© 2026 আমার সমিতি · সর্বস্বত্ব সংরক্ষিত'
            '</div>',
            unsafe_allow_html=True,
        )

    st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# Shared UI helpers
# =========================================================
def page_header(title, subtitle=""):
    st.markdown(f'<h1 class="page-title">{title}</h1>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="page-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def member_options(data):
    members = data.get("members", {})
    return list(members.keys())


def member_label(member_id, member):
    return f"{member.get('name', 'নাম নেই')} — {member_id}"


# =========================================================
# Page 1: Dashboard
# =========================================================
def dashboard_page(data):
    page_header("🏠 ড্যাশবোর্ড", "সমিতির বর্তমান আর্থিক অবস্থার সংক্ষিপ্ত চিত্র")

    members = data.get("members", {})
    total_members = len(members)
    total_savings = sum(float(m.get("savings", 0)) for m in members.values())
    total_loan = sum(float(m.get("loan_principal", 0)) for m in members.values())
    active_loans = sum(
        1 for m in members.values() if float(m.get("loan_principal", 0)) > 0.009
    )

    c1, c2, c3, c4 = st.columns(4)
    metrics = [
        ("👥 মোট সদস্য", total_members),
        ("💰 মোট সঞ্চয়", money(total_savings)),
        ("💸 বকেয়া ঋণ", money(total_loan)),
        ("📌 চলমান ঋণ", active_loans),
    ]

    for col, (label, value) in zip([c1, c2, c3, c4], metrics):
        with col:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">{label}</div>
                    <div class="metric-value">{value}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.write("")
    left, right = st.columns(2)

    with left:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("👥 সদস্যদের তালিকা")
        if members:
            rows = []
            for mid, m in members.items():
                rows.append(
                    {
                        "সদস্য": m.get("name", ""),
                        "মোবাইল": mid,
                        "সঞ্চয়": float(m.get("savings", 0)),
                        "ঋণ বকেয়া": float(m.get("loan_principal", 0)),
                        "অবস্থা": "ঋণ চলমান" if float(m.get("loan_principal", 0)) > 0.009 else "ঋণ নেই",
                    }
                )
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info("এখনও কোনো সদস্য যোগ করা হয়নি।")
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("🕐 সাম্প্রতিক লেনদেন")
        transactions = []
        for mid, m in members.items():
            for item in m.get("history", [])[-5:]:
                transactions.append(
                    {
                        "মোবাইল": mid,
                        "সদস্য": m.get("name", ""),
                        "লেনদেন": item,
                    }
                )

        if transactions:
            transactions = transactions[-10:][::-1]
            st.dataframe(pd.DataFrame(transactions), use_container_width=True, hide_index=True)
        else:
            st.info("কোনো transaction history নেই।")
        st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# Page 2: Member management
# =========================================================
def member_management_page(data):
    page_header("👥 সদস্য ব্যবস্থাপনা", "নতুন সদস্য যোগ করুন অথবা সদস্যের তথ্য দেখুন")

    tab1, tab2 = st.tabs(["➕ নতুন সদস্য", "📋 সদস্য তালিকা"])

    with tab1:
        with st.form("add_member_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                mobile = st.text_input("মোবাইল নম্বর", placeholder="017XXXXXXXX")
            with c2:
                name = st.text_input("সদস্যের নাম", placeholder="পূর্ণ নাম")

            initial_savings = st.number_input(
                "প্রাথমিক সঞ্চয়",
                min_value=0.0,
                step=100.0,
                value=0.0,
            )

            submitted = st.form_submit_button("💾 সদস্য সংরক্ষণ", use_container_width=True)

        if submitted:
            mobile = mobile.strip()
            name = name.strip()

            if not mobile or not name:
                st.error("মোবাইল নম্বর এবং সদস্যের নাম দিন।")
            elif mobile in data["members"]:
                st.error("এই মোবাইল নম্বর দিয়ে সদস্য ইতিমধ্যে আছে।")
            else:
                data["members"][mobile] = {
                    "name": name,
                    "savings": float(initial_savings),
                    "loan_principal": 0.0,
                    "loan_interest": 0.0,
                    "loan_type": "নাই",
                    "loan_date": "",
                    "loan_rate": 0.0,
                    "loan_duration": 0,
                    "loan_duration_unit": "Months",
                    "loan_status": "closed",
                    "loan_original_principal": 0.0,
                    "loan_original_interest": 0.0,
                    "loan_paid_principal": 0.0,
                    "loan_paid_interest": 0.0,
                    "loan_last_payment": "",
                    "loan_installment_count": 0,
                    "loan_total_installments": 0,
                    "loan_schedule": [],
                    "history": [],
                }

                add_history(
                    data["members"][mobile],
                    f"হিসাব খোলা হয়েছে। প্রাথমিক সঞ্চয়: {money(initial_savings)}",
                )
                save_and_rerun(data)

    with tab2:
        if not data["members"]:
            st.info("এখনও কোনো সদস্য নেই।")
            return

        rows = []
        for mid, m in data["members"].items():
            rows.append(
                {
                    "নাম": m.get("name", ""),
                    "মোবাইল": mid,
                    "সঞ্চয়": float(m.get("savings", 0)),
                    "ঋণ বকেয়া": float(m.get("loan_principal", 0)),
                    "ঋণের হার %": float(m.get("loan_rate", 0)),
                    "ঋণ অবস্থা": "চলমান" if float(m.get("loan_principal", 0)) > 0.009 else "নেই",
                }
            )

        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# =========================================================
# DPS / FDR calculations
# =========================================================
def add_months(base_date, months):
    """Add calendar months without external dependencies."""
    month_index = base_date.month - 1 + int(months)
    year = base_date.year + month_index // 12
    month = month_index % 12 + 1
    # Last valid day of target month
    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)
    last_day = (next_month - timedelta(days=1)).day
    return date(year, month, min(base_date.day, last_day))


def deposit_maturity_date(start_dt, term_months):
    return datetime.combine(
        add_months(start_dt.date(), term_months),
        start_dt.time(),
    )


def term_deposit_interest(deposit, as_of=None):
    """
    Maturity interest calculation.
    FDR: principal earns annual simple interest for actual elapsed days.
    DPS: every contribution earns annual simple interest from its own
    contribution timestamp until maturity/as_of.
    """
    as_of = as_of or datetime.now()
    rate = float(deposit.get("annual_rate", 0.0))

    if deposit.get("product") == "FDR":
        principal = float(deposit.get("principal", 0.0))
        start = parse_dt(deposit.get("start_at")) or as_of
        end = min(as_of, parse_dt(deposit.get("maturity_at")) or as_of)
        days = max((end - start).total_seconds() / 86400.0, 0.0)
        return round(principal * rate / 100.0 * days / 365.0, 2)

    total = 0.0
    for contribution in deposit.get("contributions", []):
        amount = float(contribution.get("amount", 0.0))
        cdt = parse_dt(contribution.get("date")) or as_of
        end = min(as_of, parse_dt(deposit.get("maturity_at")) or as_of)
        days = max((end - cdt).total_seconds() / 86400.0, 0.0)
        total += amount * rate / 100.0 * days / 365.0
    return round(total, 2)


def term_deposit_principal(deposit):
    if deposit.get("product") == "FDR":
        return round(float(deposit.get("principal", 0.0)), 2)
    return round(
        sum(float(x.get("amount", 0.0)) for x in deposit.get("contributions", [])),
        2,
    )


def active_term_deposits(member):
    return [x for x in member.get("term_deposits", []) if x.get("status") == "active"]


# =========================================================
# Page: DPS / FDR
# =========================================================
def term_deposit_page(data):
    page_header(
        "🏦 DPS / FDR মেয়াদি সঞ্চয়",
        "৩, ৬, ৯ বা ১২ মাসের জন্য টাকা রেখে মেয়াদ শেষে মূলধন ও সুদ প্রদান করুন",
    )

    if not data["members"]:
        st.warning("প্রথমে সদস্য ব্যবস্থাপনা থেকে সদস্য যোগ করুন।")
        return

    ids = member_options(data)
    selected = st.selectbox(
        "সদস্য নির্বাচন করুন",
        ids,
        format_func=lambda x: member_label(x, data["members"][x]),
        key="term_member",
    )
    member = data["members"][selected]
    ensure_member_defaults(member)

    c1, c2, c3 = st.columns(3)
    c1.metric("💰 সাধারণ সঞ্চয়", money(member.get("savings", 0)))
    c2.metric(
        "🏦 মেয়াদি আমানত",
        money(sum(term_deposit_principal(x) for x in active_term_deposits(member))),
    )
    c3.metric("📌 সক্রিয় DPS/FDR", len(active_term_deposits(member)))

    st.markdown("---")
    st.subheader("➕ নতুন DPS / FDR খুলুন")

    with st.form("term_deposit_form"):
        product = st.selectbox("সঞ্চয়ের ধরন", ["FDR", "DPS"])
        term_months = st.selectbox("মেয়াদ", [3, 6, 9, 12], format_func=lambda x: f"{x} মাস")
        annual_rate = st.number_input(
            "বার্ষিক সুদের হার (%)",
            min_value=0.0,
            max_value=100.0,
            value=10.0 if product == "FDR" else 8.0,
            step=0.25,
        )
        amount = st.number_input(
            "জমার পরিমাণ" if product == "FDR" else "প্রতি মাসের DPS কিস্তি",
            min_value=100.0,
            step=100.0,
            value=1000.0,
        )
        open_date = st.date_input("শুরুর তারিখ", value=date.today())
        submit = st.form_submit_button(
            "🏦 মেয়াদি সঞ্চয় চালু করুন",
            use_container_width=True,
            type="primary",
        )

    if submit:
        start_dt = datetime.combine(open_date, datetime.now().time())
        maturity_dt = deposit_maturity_date(start_dt, term_months)

        if float(member.get("savings", 0.0)) < float(amount):
            st.error(
                f"সাধারণ সঞ্চয়ে পর্যাপ্ত টাকা নেই। প্রয়োজন {money(amount)}, "
                f"বর্তমানে আছে {money(member.get('savings', 0))}."
            )
        else:
            deposit_id = f"TD-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
            if product == "FDR":
                deposit = {
                    "id": deposit_id,
                    "product": "FDR",
                    "principal": round(float(amount), 2),
                    "annual_rate": float(annual_rate),
                    "term_months": int(term_months),
                    "start_at": start_dt.strftime("%Y-%m-%d %H:%M:%S"),
                    "maturity_at": maturity_dt.strftime("%Y-%m-%d %H:%M:%S"),
                    "status": "active",
                    "contributions": [],
                }
                member["savings"] = round(float(member.get("savings", 0)) - amount, 2)
                add_history(
                    member,
                    f"FDR খোলা: {money(amount)} | মেয়াদ: {term_months} মাস | "
                    f"হার: {annual_rate:.2f}% | পরিপক্বতা: {maturity_dt.strftime('%Y-%m-%d %H:%M:%S')}",
                )
            else:
                contribution = {
                    "amount": round(float(amount), 2),
                    "date": start_dt.strftime("%Y-%m-%d %H:%M:%S"),
                }
                deposit = {
                    "id": deposit_id,
                    "product": "DPS",
                    "annual_rate": float(annual_rate),
                    "term_months": int(term_months),
                    "monthly_amount": round(float(amount), 2),
                    "start_at": start_dt.strftime("%Y-%m-%d %H:%M:%S"),
                    "maturity_at": maturity_dt.strftime("%Y-%m-%d %H:%M:%S"),
                    "status": "active",
                    "contributions": [contribution],
                }
                member["savings"] = round(float(member.get("savings", 0)) - amount, 2)
                add_history(
                    member,
                    f"DPS চালু: প্রথম কিস্তি {money(amount)} | মেয়াদ: {term_months} মাস | "
                    f"হার: {annual_rate:.2f}% | পরিপক্বতা: {maturity_dt.strftime('%Y-%m-%d %H:%M:%S')}",
                )

            member["term_deposits"].append(deposit)
            save_and_rerun(data)

    st.markdown("---")
    st.subheader("📋 সক্রিয় DPS / FDR")

    active = active_term_deposits(member)
    if not active:
        st.info("এই সদস্যের কোনো সক্রিয় DPS/FDR নেই।")
        return

    for dep in active:
        principal = term_deposit_principal(dep)
        maturity = parse_dt(dep.get("maturity_at")) or datetime.now()
        estimated_interest = term_deposit_interest(dep, min(datetime.now(), maturity))
        matured = datetime.now() >= maturity
        label = f"{dep.get('product')} • {money(principal)} • {dep.get('term_months')} মাস"

        with st.expander(label, expanded=matured):
            d1, d2, d3, d4 = st.columns(4)
            d1.metric("মূলধন", money(principal))
            d2.metric("হার", f"{float(dep.get('annual_rate', 0)):.2f}%")
            d3.metric("আনুমানিক সুদ", money(estimated_interest))
            d4.metric("মেয়াদ", dep.get("term_months", 0), "মাস")

            st.write(f"**শুরু:** {dep.get('start_at', '')}")
            st.write(f"**মেয়াদ পূর্তি:** {dep.get('maturity_at', '')}")

            if dep.get("product") == "DPS":
                st.write(f"**মাসিক কিস্তি:** {money(dep.get('monthly_amount', 0))}")
                st.write(f"**জমা কিস্তির সংখ্যা:** {len(dep.get('contributions', []))}")

                if not matured:
                    if st.button(
                        "💰 DPS কিস্তি জমা করুন",
                        key=f"dps_add_{dep['id']}",
                        use_container_width=True,
                    ):
                        monthly = float(dep.get("monthly_amount", 0))
                        if float(member.get("savings", 0)) < monthly:
                            st.error("সাধারণ সঞ্চয়ে এই কিস্তির জন্য পর্যাপ্ত টাকা নেই।")
                        else:
                            now = datetime.now()
                            dep.setdefault("contributions", []).append(
                                {
                                    "amount": round(monthly, 2),
                                    "date": now.strftime("%Y-%m-%d %H:%M:%S"),
                                }
                            )
                            member["savings"] = round(float(member.get("savings", 0)) - monthly, 2)
                            add_history(
                                member,
                                f"DPS কিস্তি জমা: {money(monthly)} | "
                                f"চুক্তি: {dep['id']}",
                            )
                            save_and_rerun(data)

            if matured:
                final_interest = term_deposit_interest(dep, maturity)
                total_payout = round(principal + final_interest, 2)
                st.success(
                    f"✅ মেয়াদ পূর্ণ হয়েছে। মোট ফেরত: {money(total_payout)} "
                    f"(মূলধন {money(principal)} + সুদ {money(final_interest)})"
                )
                if st.button(
                    "🏁 মেয়াদি সঞ্চয় ভাঙিয়ে টাকা ও সুদ প্রদান করুন",
                    key=f"mature_{dep['id']}",
                    type="primary",
                    use_container_width=True,
                ):
                    member["savings"] = round(float(member.get("savings", 0)) + total_payout, 2)
                    dep["status"] = "matured_paid"
                    dep["paid_at"] = now_str()
                    dep["paid_interest"] = final_interest
                    add_history(
                        member,
                        f"{dep.get('product')} মেয়াদ পূর্তি ও পরিশোধ: "
                        f"মূলধন {money(principal)} + সুদ {money(final_interest)} = "
                        f"মোট {money(total_payout)} | চুক্তি: {dep['id']}",
                    )
                    save_and_rerun(data)

    st.markdown("---")
    st.subheader("🗂️ এই সদস্যের মেয়াদি সঞ্চয়ের ইতিহাস")
    history_rows = []
    for dep in member.get("term_deposits", []):
        principal = term_deposit_principal(dep)
        paid_interest = float(dep.get("paid_interest", 0.0))
        history_rows.append(
            {
                "ধরন": dep.get("product", ""),
                "চুক্তি": dep.get("id", ""),
                "মূলধন": round(principal, 2),
                "হার": f"{float(dep.get('annual_rate', 0)):.2f}%",
                "মেয়াদ": f"{dep.get('term_months', 0)} মাস",
                "শুরু": dep.get("start_at", ""),
                "মেয়াদ পূর্তি": dep.get("maturity_at", ""),
                "সুদ প্রদান": round(paid_interest, 2),
                "অবস্থা": dep.get("status", ""),
            }
        )
    if history_rows:
        st.dataframe(pd.DataFrame(history_rows), use_container_width=True, hide_index=True)


# =========================================================
# Page 3: Savings deposit
# =========================================================
def savings_page(data):
    page_header("💰 সঞ্চয় জমা", "সদস্যের সঞ্চয় হিসাব বাড়ান এবং transaction history সংরক্ষণ করুন")

    if not data["members"]:
        st.warning("প্রথমে সদস্য ব্যবস্থাপনা থেকে সদস্য যোগ করুন।")
        return

    ids = member_options(data)
    selected = st.selectbox(
        "সদস্য নির্বাচন করুন",
        ids,
        format_func=lambda x: member_label(x, data["members"][x]),
    )
    member = data["members"][selected]

    c1, c2 = st.columns(2)
    with c1:
        st.info(f"বর্তমান সঞ্চয়: **{money(member.get('savings', 0))}**")
    with c2:
        st.info(f"মোবাইল: **{selected}**")

    with st.form("savings_form"):
        amount = st.number_input(
            "সঞ্চয়ের পরিমাণ",
            min_value=1.0,
            step=100.0,
            value=100.0,
        )
        note = st.text_input("নোট (ঐচ্ছিক)", placeholder="যেমন: সাপ্তাহিক সঞ্চয়")
        submit = st.form_submit_button("💰 সঞ্চয় জমা করুন", use_container_width=True)

    if submit:
        member["savings"] = round(float(member.get("savings", 0)) + amount, 2)
        text = f"সঞ্চয় জমা: {money(amount)}"
        if note.strip():
            text += f" — {note.strip()}"
        add_history(member, text)
        save_and_rerun(data)


# =========================================================
# Page 4: Loan disbursement
# =========================================================
def loan_page(data):
    page_header(
        "💸 ঋণ প্রদান",
        "Days / Weeks / Months অনুযায়ী reducing-balance installment schedule তৈরি করুন",
    )

    if not data["members"]:
        st.warning("প্রথমে সদস্য যোগ করুন।")
        return

    ids = member_options(data)
    selected = st.selectbox(
        "সদস্য নির্বাচন করুন",
        ids,
        format_func=lambda x: member_label(x, data["members"][x]),
    )
    member = data["members"][selected]

    if outstanding_principal(member) > 0.009:
        st.warning(
            f"এই সদস্যের বর্তমান বকেয়া ঋণ {money(member.get('loan_principal', 0))}। "
            "নতুন ঋণ দেওয়ার আগে বর্তমান ঋণ নিষ্পত্তি করুন।"
        )
        return

    with st.form("loan_form"):
        c1, c2 = st.columns(2)
        with c1:
            principal = st.number_input(
                "ঋণের পরিমাণ",
                min_value=1.0,
                step=1000.0,
                value=10000.0,
            )
        with c2:
            annual_rate = st.number_input(
                "বার্ষিক সুদের হার (%)",
                min_value=0.0,
                max_value=100.0,
                step=0.5,
                value=10.0,
            )

        c3, c4 = st.columns(2)
        with c3:
            duration = st.number_input(
                "ঋণের মেয়াদ",
                min_value=1,
                max_value=1000,
                step=1,
                value=10,
            )
        with c4:
            unit = st.selectbox("মেয়াদের ধরন", ["Days", "Weeks", "Months"], index=2)

        loan_type = st.text_input("ঋণের ধরন", value="সাধারণ ঋণ")
        loan_date = st.date_input("ঋণ প্রদানের তারিখ", value=date.today())

        preview = st.form_submit_button("💸 ঋণ প্রদান ও Schedule তৈরি", use_container_width=True)

    start_dt = datetime.combine(loan_date, datetime.min.time())

    if preview:
        schedule = calculate_schedule(
            principal,
            annual_rate,
            duration,
            unit,
            start_dt,
        )

        total_interest = sum(float(x["interest"]) for x in schedule)
        total_payable = principal + total_interest

        member["loan_principal"] = round(float(principal), 2)
        member["loan_interest"] = round(total_interest, 2)
        member["loan_type"] = loan_type.strip() or "সাধারণ ঋণ"
        member["loan_date"] = start_dt.strftime("%Y-%m-%d %H:%M:%S")
        member["loan_rate"] = float(annual_rate)
        member["loan_duration"] = int(duration)
        member["loan_duration_unit"] = unit
        member["loan_status"] = "active"
        member["loan_original_principal"] = round(float(principal), 2)
        member["loan_original_interest"] = round(total_interest, 2)
        member["loan_paid_principal"] = 0.0
        member["loan_paid_interest"] = 0.0
        member["loan_last_payment"] = start_dt.strftime("%Y-%m-%d %H:%M:%S")
        member["loan_installment_count"] = 0
        member["loan_total_installments"] = int(duration)
        member["loan_schedule"] = schedule

        add_history(
            member,
            f"ঋণ প্রদান: {money(principal)} | হার: {annual_rate:.2f}% বার্ষিক | "
            f"মেয়াদ: {duration} {unit} | মোট নির্ধারিত সুদ: {money(total_interest)} | "
            f"মোট পরিশোধযোগ্য: {money(total_payable)}",
        )
        save_and_rerun(data)

    # Current loan summary
    if outstanding_principal(member) > 0.009:
        st.markdown("---")
        st.subheader("📊 বর্তমান ঋণের তথ্য")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("মূল ঋণ", money(member.get("loan_original_principal", 0)))
        c2.metric("বকেয়া মূলধন", money(member.get("loan_principal", 0)))
        c3.metric("নির্ধারিত সুদ", money(member.get("loan_original_interest", 0)))
        c4.metric("কিস্তি", f"{member.get('loan_total_installments', 0)}")

        if member.get("loan_schedule"):
            st.dataframe(
                pd.DataFrame(member["loan_schedule"]),
                use_container_width=True,
                hide_index=True,
            )


# =========================================================
# Page 5: Installment / loan collection
# =========================================================
def collection_page(data):
    page_header(
        "💳 ঋণের টাকা বা কিস্তি আদায়",
        "Reducing balance অনুযায়ী payment নিন, আংশিক payment সমর্থিত",
    )

    active_ids = [
        mid
        for mid, m in data["members"].items()
        if outstanding_principal(m) > 0.009
    ]

    if not active_ids:
        st.info("কোনো চলমান ঋণ নেই।")
        return

    selected = st.selectbox(
        "ঋণগ্রহীতা নির্বাচন করুন",
        active_ids,
        format_func=lambda x: member_label(x, data["members"][x]),
    )
    member = data["members"][selected]

    principal_balance = outstanding_principal(member)
    annual_rate = float(member.get("loan_rate", 0.0))
    accrued = elapsed_interest(member)

    c1, c2, c3 = st.columns(3)
    c1.metric("বকেয়া মূলধন", money(principal_balance))
    c2.metric("বার্ষিক হার", f"{annual_rate:.2f}%")
    c3.metric("বর্তমান accrued interest", money(accrued))

    st.markdown("### 🧾 কিস্তি / ঋণের টাকা আদায়")

    with st.form("collection_form"):
        amount = st.number_input(
            "আদায়ের পরিমাণ",
            min_value=0.01,
            max_value=max(principal_balance + accrued, 0.01),
            step=100.0,
            value=min(
                max(
                    round(
                        principal_balance
                        / max(int(member.get("loan_total_installments", 1)), 1),
                        2,
                    ),
                    1.0,
                ),
                max(principal_balance + accrued, 0.01),
            ),
        )
        note = st.text_input("নোট (ঐচ্ছিক)")
        submit = st.form_submit_button("💳 টাকা আদায় করুন", use_container_width=True)

    if submit:
        payment = float(amount)

        # Current elapsed interest is charged first.
        interest_due = elapsed_interest(member)
        interest_paid = min(payment, interest_due)
        principal_paid = min(max(payment - interest_paid, 0.0), principal_balance)

        member["loan_interest"] = round(
            max(float(member.get("loan_interest", 0)) - interest_paid, 0.0), 2
        )
        member["loan_principal"] = round(
            max(principal_balance - principal_paid, 0.0), 2
        )
        member["loan_paid_interest"] = round(
            float(member.get("loan_paid_interest", 0)) + interest_paid, 2
        )
        member["loan_paid_principal"] = round(
            float(member.get("loan_paid_principal", 0)) + principal_paid, 2
        )
        member["loan_installment_count"] = int(
            member.get("loan_installment_count", 0)
        ) + 1
        member["loan_last_payment"] = now_str()

        # Keep schedule progress in sync.
        mark_schedule_payment(member, payment)

        if note.strip():
            note_text = f" — {note.strip()}"
        else:
            note_text = ""

        add_history(
            member,
            f"ঋণ আদায়: {money(payment)} | মূলধন: {money(principal_paid)} | "
            f"সুদ: {money(interest_paid)} | অবশিষ্ট মূলধন: "
            f"{money(member['loan_principal'])}{note_text}",
        )

        if outstanding_principal(member) <= 0.009:
            member["loan_principal"] = 0.0
            member["loan_interest"] = 0.0
            member["loan_status"] = "closed"
            member["loan_last_payment"] = now_str()
            add_history(member, "ঋণ সম্পূর্ণ পরিশোধ হয়েছে।")

        save_and_rerun(data)

    st.markdown("---")
    st.subheader("⚡ Early Settlement")

    early_interest = elapsed_interest(member)
    future_interest = remaining_scheduled_interest(member)
    settlement_total = principal_balance + early_interest

    st.info(
        f"আজ Early Settlement করলে আনুমানিক পরিশোধযোগ্য: **{money(settlement_total)}**। "
        f"ভবিষ্যতের নির্ধারিত সুদ **{money(future_interest)}** আর নেওয়া হবে না।"
    )

    confirm = st.checkbox(
        "আমি বুঝেছি যে Early Settlement করলে বর্তমান বকেয়া মূলধন + বাস্তবে অতিবাহিত সময়ের সুদ নেওয়া হবে এবং ভবিষ্যতের সুদ মওকুফ হবে।",
        key=f"early_confirm_{selected}",
    )

    if st.button(
        "⚡ Early Settlement করে ঋণ বন্ধ করুন",
        use_container_width=True,
        disabled=not confirm,
    ):
        member["loan_principal"] = 0.0
        member["loan_interest"] = 0.0
        member["loan_status"] = "closed"
        member["loan_paid_principal"] = round(
            float(member.get("loan_paid_principal", 0)) + principal_balance, 2
        )
        member["loan_paid_interest"] = round(
            float(member.get("loan_paid_interest", 0)) + early_interest, 2
        )
        member["loan_last_payment"] = now_str()

        for row in member.get("loan_schedule", []):
            if row.get("status") != "পরিশোধ":
                row["status"] = "Early Settlement"
                row["paid"] = round(float(row.get("paid", 0)) + 0.0, 2)

        add_history(
            member,
            f"Early Settlement: মোট আদায় {money(settlement_total)} | "
            f"মূলধন {money(principal_balance)} | বাস্তব সময়ের সুদ {money(early_interest)} | "
            f"ভবিষ্যৎ সুদ মওকুফ {money(future_interest)}",
        )
        add_history(member, "ঋণ Early Settlement-এর মাধ্যমে সম্পূর্ণ বন্ধ হয়েছে।")

        save_and_rerun(data)


# =========================================================
# Page 6: Statement
# =========================================================
def statement_page(data):
    page_header(
        "📋 সদস্য স্টেটমেন্ট (Statement)",
        "সদস্যের সঞ্চয়, ঋণ এবং সম্পূর্ণ transaction history দেখুন",
    )

    if not data["members"]:
        st.info("কোনো সদস্য নেই।")
        return

    ids = member_options(data)
    selected = st.selectbox(
        "সদস্য নির্বাচন করুন",
        ids,
        format_func=lambda x: member_label(x, data["members"][x]),
    )
    member = data["members"][selected]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("সঞ্চয়", money(member.get("savings", 0)))
    c2.metric("বকেয়া ঋণ", money(member.get("loan_principal", 0)))
    c3.metric("বকেয়া সুদ", money(member.get("loan_interest", 0)))
    c4.metric(
        "DPS/FDR",
        money(sum(term_deposit_principal(x) for x in active_term_deposits(member))),
    )

    st.markdown("### 👤 সদস্যের তথ্য")
    info = {
        "সদস্যের নাম": member.get("name", ""),
        "মোবাইল": selected,
        "ঋণের ধরন": member.get("loan_type", "নাই"),
        "ঋণের হার": f"{float(member.get('loan_rate', 0)):.2f}%",
        "মেয়াদ": f"{member.get('loan_duration', 0)} {member.get('loan_duration_unit', '')}",
        "ঋণ শুরু": member.get("loan_date", "") or "নাই",
        "ঋণের অবস্থা": member.get("loan_status", "closed"),
        "মোট কিস্তি": member.get("loan_total_installments", 0),
        "পরিশোধিত কিস্তি/লেনদেন": member.get("loan_installment_count", 0),
    }
    st.dataframe(
        pd.DataFrame(list(info.items()), columns=["বিষয়", "তথ্য"]),
        use_container_width=True,
        hide_index=True,
    )

    if member.get("loan_schedule"):
        st.markdown("### 📅 কিস্তির Schedule")
        st.dataframe(
            pd.DataFrame(member["loan_schedule"]),
            use_container_width=True,
            hide_index=True,
        )

    if member.get("term_deposits"):
        st.markdown("### 🏦 DPS / FDR হিসাব")
        td_rows = []
        for dep in member.get("term_deposits", []):
            td_rows.append(
                {
                    "ধরন": dep.get("product", ""),
                    "চুক্তি": dep.get("id", ""),
                    "মূলধন": term_deposit_principal(dep),
                    "হার": f"{float(dep.get('annual_rate', 0)):.2f}%",
                    "মেয়াদ": f"{dep.get('term_months', 0)} মাস",
                    "মেয়াদ পূর্তি": dep.get("maturity_at", ""),
                    "অবস্থা": dep.get("status", ""),
                }
            )
        st.dataframe(pd.DataFrame(td_rows), use_container_width=True, hide_index=True)

    st.markdown("### 🕐 সম্পূর্ণ Transaction History")

    history = member.get("history", [])
    if history:
        history_df = pd.DataFrame(
            [{"তারিখ ও সময়": item[:19], "লেনদেন": item[22:] if len(item) > 22 else item} for item in history]
        )
        st.dataframe(
            history_df,
            use_container_width=True,
            hide_index=True,
        )

        csv_bytes = history_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "📥 Statement CSV ডাউনলোড",
            data=csv_bytes,
            file_name=f"statement_{selected}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    else:
        st.info("এই সদস্যের কোনো history নেই।")




# =========================================================
# Page 7: Reports
# =========================================================

def reports_page(data):
    page_header(
        "📊 রিপোর্ট",
        "সমিতির সঞ্চয়, ঋণ, আদায় ও সদস্যদের সামগ্রিক হিসাব",
    )

    members = data.get("members", {})
    total_members = len(members)
    total_savings = sum(float(m.get("savings", 0)) for m in members.values())
    active_loans = [
        m for m in members.values() if outstanding_principal(m) > 0.009
    ]
    total_loan_disbursed = sum(
        float(m.get("loan_original_principal", 0)) for m in members.values()
    )
    total_loan_outstanding = sum(
        outstanding_principal(m) for m in members.values()
    )
    total_term_deposit = sum(
        term_deposit_principal(dep)
        for m in members.values()
        for dep in active_term_deposits(m)
    )
    total_principal_paid = sum(
        float(m.get("loan_paid_principal", 0)) for m in members.values()
    )
    total_interest_paid = sum(
        float(m.get("loan_paid_interest", 0)) for m in members.values()
    )

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("👥 মোট সদস্য", total_members)
    c2.metric("💰 মোট সঞ্চয়", money(total_savings))
    c3.metric("🏦 DPS/FDR", money(total_term_deposit))
    c4.metric("💸 চলমান ঋণ", len(active_loans))
    c5.metric("📌 বকেয়া মূলধন", money(total_loan_outstanding))

    st.markdown("---")
    st.subheader("📈 আর্থিক সারসংক্ষেপ")

    r1, r2, r3 = st.columns(3)
    r1.metric("মোট ঋণ বিতরণ", money(total_loan_disbursed))
    r2.metric("আদায় করা মূলধন", money(total_principal_paid))
    r3.metric("আদায় করা সুদ", money(total_interest_paid))

    report_rows = []
    for mid, m in members.items():
        report_rows.append(
            {
                "সদস্য": m.get("name", ""),
                "মোবাইল": mid,
                "সঞ্চয়": round(float(m.get("savings", 0)), 2),
                "ঋণ বিতরণ": round(float(m.get("loan_original_principal", 0)), 2),
                "মূলধন আদায়": round(float(m.get("loan_paid_principal", 0)), 2),
                "বকেয়া মূলধন": round(outstanding_principal(m), 2),
                "সুদ আদায়": round(float(m.get("loan_paid_interest", 0)), 2),
                "DPS/FDR": round(
                    sum(term_deposit_principal(x) for x in active_term_deposits(m)), 2
                ),
                "অবস্থা": "চলমান" if outstanding_principal(m) > 0.009 else "ঋণ নেই",
            }
        )

    if report_rows:
        report_df = pd.DataFrame(report_rows)
        st.subheader("👥 সদস্যভিত্তিক রিপোর্ট")
        st.dataframe(report_df, use_container_width=True, hide_index=True)

        csv_bytes = report_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "📥 রিপোর্ট CSV ডাউনলোড",
            data=csv_bytes,
            file_name="somity_report.csv",
            mime="text/csv",
            use_container_width=True,
        )

    st.subheader("🕐 সাম্প্রতিক লেনদেন")
    transactions = []
    for mid, m in members.items():
        for item in m.get("history", []):
            transactions.append(
                {
                    "মোবাইল": mid,
                    "সদস্য": m.get("name", ""),
                    "তারিখ ও সময়": item[:19],
                    "লেনদেন": item[22:] if len(item) > 22 else item,
                }
            )

    transactions = sorted(
        transactions,
        key=lambda x: x["তারিখ ও সময়"],
        reverse=True,
    )

    if transactions:
        st.dataframe(
            pd.DataFrame(transactions[:50]),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("এখনও কোনো লেনদেন নেই।")


# =========================================================
# Page 8: Backup & Data
# =========================================================

def backup_page(data):
    page_header(
        "💾 ব্যাকআপ ও ডাটা",
        "database.json-এর নিরাপদ ব্যাকআপ রাখুন এবং প্রয়োজনে ডাটা Restore করুন",
    )

    members = data.get("members", {})
    total_savings = sum(float(m.get("savings", 0)) for m in members.values())
    active_loans = sum(
        1 for m in members.values() if outstanding_principal(m) > 0.009
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("মোট সদস্য", len(members))
    c2.metric("মোট সঞ্চয়", money(total_savings))
    c3.metric("চলমান ঋণ", active_loans)

    st.markdown("---")
    st.subheader("📥 ডাটা Backup")

    backup_payload = json.dumps(
        data,
        ensure_ascii=False,
        indent=2,
    ).encode("utf-8")

    st.download_button(
        "💾 সম্পূর্ণ Backup Download",
        data=backup_payload,
        file_name=f"somity_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json",
        use_container_width=True,
    )

    st.caption(
        "Backup ফাইলটি নিরাপদ জায়গায় রাখুন। এতে সদস্য, সঞ্চয়, ঋণ এবং transaction history থাকবে।"
    )

    st.markdown("---")
    st.subheader("📤 Backup Restore")

    uploaded = st.file_uploader(
        "আগের Backup JSON নির্বাচন করুন",
        type=["json"],
        help="শুধু এই অ্যাপের বৈধ database backup JSON ব্যবহার করুন।",
    )

    if uploaded is not None:
        try:
            restored = json.load(uploaded)
            restored = normalize_data(restored)

            if not isinstance(restored, dict) or not isinstance(
                restored.get("members"), dict
            ):
                st.error("এই ফাইলটি বৈধ সমিতি Backup নয়।")
            else:
                st.warning(
                    f"Restore করলে বর্তমান {len(members)} জন সদস্যের ডাটা "
                    f"এর জায়গায় Backup-এর {len(restored['members'])} জন সদস্যের ডাটা আসবে।"
                )

                confirm = st.checkbox(
                    "আমি নিশ্চিত, এই Backup Restore করতে চাই।",
                    key="restore_confirm",
                )

                if st.button(
                    "♻️ Backup Restore করুন",
                    type="primary",
                    use_container_width=True,
                    disabled=not confirm,
                ):
                    save_data(restored)
                    st.session_state["restore_success"] = True
                    st.rerun()

        except (json.JSONDecodeError, UnicodeDecodeError):
            st.error("JSON ফাইলটি পড়া যায়নি। সঠিক Backup ফাইল নির্বাচন করুন।")
        except Exception as exc:
            st.error(f"Restore করা যায়নি: {exc}")

    if st.session_state.pop("restore_success", False):
        st.success("✅ Backup সফলভাবে Restore হয়েছে।")

    st.markdown("---")
    st.subheader("⚠️ গুরুত্বপূর্ণ")
    st.info(
        "Streamlit Cloud-এ database.json-এর পরিবর্তন GitHub-এর মতো স্থায়ী storage নয়। "
        "নিয়মিত Backup Download করে নিজের কম্পিউটার/নিরাপদ cloud storage-এ রাখুন।"
    )


# =========================================================
# Main app
# =========================================================
def main():
    apply_css()

    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        login_page()
        return

    data = normalize_data(load_data())

    with st.sidebar:
        st.markdown(
            """
            <div style="text-align:center;padding:12px 0 18px 0;">
                <div style="font-size:38px;">🌿</div>
                <div style="font-size:24px;font-weight:900;color:#17652b;">
                    আমার সমিতি
                </div>
                <div style="font-size:12px;color:#6b786e;">
                    Micro-Finance Management
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        page = st.radio(
            "মেনু",
            MENU,
            index=0,
            key="main_menu",
        )

        st.markdown("---")

        if st.button("🚪 Logout", use_container_width=True):
            st.session_state["logged_in"] = False
            st.rerun()

        st.caption("© 2026 আমার সমিতি")

    # IMPORTANT:
    # Sidebar menu text and conditions are EXACTLY the same.
    if page == "🏠 ড্যাশবোর্ড":
        dashboard_page(data)

    elif page == "👥 সদস্য ব্যবস্থাপনা":
        member_management_page(data)

    elif page == "💰 সঞ্চয় জমা":
        savings_page(data)

    elif page == "🏦 DPS / FDR মেয়াদি সঞ্চয়":
        term_deposit_page(data)

    elif page == "💸 ঋণ প্রদান":
        loan_page(data)

    elif page == "💳 ঋণের টাকা বা কিস্তি আদায়":
        collection_page(data)

    elif page == "📋 সদস্য স্টেটমেন্ট (Statement)":
        statement_page(data)

    elif page == "📊 রিপোর্ট":
        reports_page(data)

    elif page == "💾 ব্যাকআপ ও ডাটা":
        backup_page(data)


if __name__ == "__main__":
    main()
