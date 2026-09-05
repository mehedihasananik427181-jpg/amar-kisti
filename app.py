import os
import json
from datetime import datetime

import pandas as pd
import streamlit as st


# ============================================================
# APP SETTINGS
# ============================================================

st.set_page_config(
    page_title="আমার সমিতি",
    page_icon="💰",
    layout="wide"
)

DB_FILE = "database.json"

ADMIN_USER = "admin"
ADMIN_PASS = "somity2026"


# ============================================================
# BASIC FUNCTIONS
# ============================================================

def now_string():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def parse_datetime(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


def load_data():
    if not os.path.exists(DB_FILE):
        return {"members": {}}

    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            data = {"members": {}}

        if "members" not in data or not isinstance(data["members"], dict):
            data["members"] = {}

        return data

    except Exception as e:
        st.error(f"database.json পড়তে সমস্যা হয়েছে: {e}")
        return {"members": {}}


def save_data(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def add_history(member, message):
    if "history" not in member or not isinstance(member["history"], list):
        member["history"] = []

    member["history"].append(
        f"{now_string()} - {message}"
    )


def normalize_member(member):
    defaults = {
        "name": "",
        "savings": 0.0,
        "loan_principal": 0.0,
        "loan_interest": 0.0,
        "loan_type": "নাই",
        "loan_date": "",
        "loan_rate": 0.0,
        "loan_duration": 0,
        "loan_duration_unit": "Months",

        "loan_installment": 0.0,
        "loan_total_payable": 0.0,
        "loan_total_paid": 0.0,

        "loan_principal_paid": 0.0,
        "loan_interest_paid": 0.0,

        "loan_remaining_principal": 0.0,
        "loan_remaining_interest": 0.0,

        "loan_active": False,
        "loan_settled": False,

        "loan_start_date": "",
        "loan_last_payment_date": "",

        "loan_next_installment": 1,
        "loan_payments": [],
        "history": []
    }

    for key, value in defaults.items():
        if key not in member:
            member[key] = value

    if not isinstance(member["loan_payments"], list):
        member["loan_payments"] = []

    if not isinstance(member["history"], list):
        member["history"] = []

    # Compatibility with the old database structure.
    if (
        float(member.get("loan_principal", 0)) > 0
        and not member.get("loan_remaining_principal")
        and member.get("loan_active") is not False
    ):
        member["loan_remaining_principal"] = float(
            member.get("loan_principal", 0)
        )

    if not member.get("loan_start_date"):
        member["loan_start_date"] = member.get("loan_date", "")

    if not member.get("loan_last_payment_date"):
        member["loan_last_payment_date"] = member.get(
            "loan_start_date",
            member.get("loan_date", "")
        )

    return member


def prepare_database(data):
    for member_id in data["members"]:
        data["members"][member_id] = normalize_member(
            data["members"][member_id]
        )
    return data


# ============================================================
# LOAN CALCULATION
# ============================================================

def periods_per_year(unit):
    if unit == "Days":
        return 365
    if unit == "Weeks":
        return 52
    return 12


def periodic_rate(annual_rate, unit):
    return (float(annual_rate) / 100) / periods_per_year(unit)


def calculate_emi(principal, annual_rate, duration, unit):
    principal = float(principal)
    annual_rate = float(annual_rate)
    duration = int(duration)

    if principal <= 0 or duration <= 0:
        return 0.0

    rate = periodic_rate(annual_rate, unit)

    if rate == 0:
        return round(principal / duration, 2)

    emi = (
        principal
        * rate
        * (1 + rate) ** duration
        / ((1 + rate) ** duration - 1)
    )

    return round(emi, 2)


def build_schedule(principal, annual_rate, duration, unit):
    principal = float(principal)
    annual_rate = float(annual_rate)
    duration = int(duration)

    if principal <= 0 or duration <= 0:
        return []

    rate = periodic_rate(annual_rate, unit)
    emi = calculate_emi(
        principal,
        annual_rate,
        duration,
        unit
    )

    balance = principal
    schedule = []

    for number in range(1, duration + 1):
        if balance <= 0.005:
            break

        interest = balance * rate
        principal_part = emi - interest

        if principal_part > balance:
            principal_part = balance

        payment = principal_part + interest
        closing = max(0.0, balance - principal_part)

        schedule.append({
            "installment": number,
            "opening_balance": round(balance, 2),
            "interest": round(interest, 2),
            "principal": round(principal_part, 2),
            "payment": round(payment, 2),
            "closing_balance": round(closing, 2)
        })

        balance = closing

    return schedule


def days_since(value):
    dt = parse_datetime(value)

    if dt is None:
        return 0

    return max(
        0,
        (datetime.now() - dt).days
    )


def fair_early_settlement(member):
    """
    Early settlement:
    - Full outstanding principal is payable.
    - Only interest accrued since the last payment is charged.
    - Future scheduled interest is waived.
    """

    principal = float(
        member.get("loan_remaining_principal", 0)
    )

    scheduled_interest = float(
        member.get("loan_remaining_interest", 0)
    )

    annual_rate = float(
        member.get("loan_rate", 0)
    )

    last_payment_date = member.get(
        "loan_last_payment_date",
        member.get("loan_start_date", "")
    )

    elapsed = days_since(last_payment_date)

    accrued_interest = (
        principal
        * (annual_rate / 100)
        * (elapsed / 365)
    )

    accrued_interest = round(
        max(0.0, accrued_interest),
        2
    )

    # Never charge more than the remaining scheduled interest.
    fair_interest = min(
        accrued_interest,
        scheduled_interest
    )

    fair_interest = round(
        max(0.0, fair_interest),
        2
    )

    discount = max(
        0.0,
        scheduled_interest - fair_interest
    )

    total = principal + fair_interest

    return {
        "principal": round(principal, 2),
        "scheduled_interest": round(scheduled_interest, 2),
        "fair_interest": round(fair_interest, 2),
        "discount": round(discount, 2),
        "elapsed_days": elapsed,
        "total": round(total, 2)
    }


# ============================================================
# LOGIN
# ============================================================

def login_page():
    st.title("💰 আমার সমিতি")
    st.subheader("🔐 Admin Login")

    left, center, right = st.columns([1, 2, 1])

    with center:
        username = st.text_input("Username")
        password = st.text_input(
            "Password",
            type="password"
        )

        if st.button(
            "Login",
            type="primary",
            use_container_width=True
        ):
            if (
                username == ADMIN_USER
                and password == ADMIN_PASS
            ):
                st.session_state["logged_in"] = True
                st.rerun()
            else:
                st.error("Username অথবা Password ভুল।")


# ============================================================
# DASHBOARD
# ============================================================

def dashboard_page(data):
    st.title("🏠 ড্যাশবোর্ড")

    members = data["members"]

    total_members = len(members)

    total_savings = sum(
        float(m.get("savings", 0))
        for m in members.values()
    )

    active_members = [
        m for m in members.values()
        if m.get("loan_active", False)
    ]

    total_principal = sum(
        float(m.get("loan_remaining_principal", 0))
        for m in active_members
    )

    total_interest = sum(
        float(m.get("loan_remaining_interest", 0))
        for m in active_members
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "মোট সদস্য",
        total_members
    )

    c2.metric(
        "মোট সঞ্চয়",
        f"৳ {total_savings:,.2f}"
    )

    c3.metric(
        "বাকি ঋণের মূলধন",
        f"৳ {total_principal:,.2f}"
    )

    c4.metric(
        "বাকি Interest",
        f"৳ {total_interest:,.2f}"
    )

    st.divider()

    if not members:
        st.info("এখনো কোনো সদস্য যোগ করা হয়নি।")
        return

    rows = []

    for member_id, member in members.items():
        rows.append({
            "সদস্য ID": member_id,
            "নাম": member.get("name", ""),
            "সঞ্চয়": float(member.get("savings", 0)),
            "বাকি মূলধন": float(
                member.get("loan_remaining_principal", 0)
            ),
            "বাকি Interest": float(
                member.get("loan_remaining_interest", 0)
            ),
            "ঋণ Status": (
                "চলমান"
                if member.get("loan_active", False)
                else "নাই"
            )
        })

    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# MEMBER MANAGEMENT
# ============================================================

def member_page(data):
    st.title("👥 সদস্য ব্যবস্থাপনা")

    tab1, tab2 = st.tabs([
        "➕ নতুন সদস্য",
        "📋 সদস্য তালিকা"
    ])

    with tab1:
        member_id = st.text_input(
            "সদস্য ID / মোবাইল নম্বর"
        ).strip()

        name = st.text_input(
            "সদস্যের নাম"
        ).strip()

        savings = st.number_input(
            "প্রাথমিক সঞ্চয়",
            min_value=0.0,
            step=100.0
        )

        if st.button(
            "সদস্য যোগ করুন",
            type="primary"
        ):
            if not member_id:
                st.error("সদস্য ID দিন।")
                return

            if not name:
                st.error("সদস্যের নাম দিন।")
                return

            if member_id in data["members"]:
                st.error("এই সদস্য ইতিমধ্যে আছে।")
                return

            timestamp = now_string()

            data["members"][member_id] = {
                "name": name,
                "savings": float(savings),

                "loan_principal": 0.0,
                "loan_interest": 0.0,
                "loan_type": "নাই",
                "loan_date": "",
                "loan_rate": 0.0,
                "loan_duration": 0,
                "loan_duration_unit": "Months",

                "loan_installment": 0.0,
                "loan_total_payable": 0.0,
                "loan_total_paid": 0.0,
                "loan_principal_paid": 0.0,
                "loan_interest_paid": 0.0,

                "loan_remaining_principal": 0.0,
                "loan_remaining_interest": 0.0,

                "loan_active": False,
                "loan_settled": False,

                "loan_start_date": timestamp,
                "loan_last_payment_date": timestamp,
                "loan_next_installment": 1,

                "loan_payments": [],

                "history": [
                    f"{timestamp} - হিসাব খোলা হয়েছে।"
                ]
            }

            save_data(data)

            st.success("সদস্য সফলভাবে যোগ হয়েছে।")
            st.rerun()

    with tab2:
        if not data["members"]:
            st.info("কোনো সদস্য নেই।")
            return

        rows = []

        for member_id, member in data["members"].items():
            rows.append({
                "সদস্য ID": member_id,
                "নাম": member.get("name", ""),
                "সঞ্চয়": float(member.get("savings", 0)),
                "বাকি ঋণ": float(
                    member.get("loan_remaining_principal", 0)
                ),
                "Status": (
                    "চলমান"
                    if member.get("loan_active", False)
                    else "নাই"
                )
            })

        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# SAVINGS
# ============================================================

def savings_page(data):
    st.title("💰 সঞ্চয় জমা / উত্তোলন")

    if not data["members"]:
        st.warning("আগে সদস্য যোগ করুন।")
        return

    member_id = st.selectbox(
        "সদস্য নির্বাচন করুন",
        list(data["members"].keys()),
        format_func=lambda x:
            f"{x} - {data['members'][x].get('name', '')}"
    )

    member = data["members"][member_id]

    current_savings = float(
        member.get("savings", 0)
    )

    st.info(
        f"বর্তমান সঞ্চয়: ৳ {current_savings:,.2f}"
    )

    transaction_type = st.radio(
        "Transaction",
        ["জমা", "উত্তোলন"],
        horizontal=True
    )

    amount = st.number_input(
        "টাকার পরিমাণ",
        min_value=0.0,
        step=100.0
    )

    note = st.text_input("নোট")

    if st.button(
        "Transaction সম্পন্ন করুন",
        type="primary"
    ):
        if amount <= 0:
            st.error("টাকার পরিমাণ দিন।")
            return

        if (
            transaction_type == "উত্তোলন"
            and amount > current_savings
        ):
            st.error("পর্যাপ্ত সঞ্চয় নেই।")
            return

        if transaction_type == "জমা":
            member["savings"] = (
                current_savings + amount
            )
            message = (
                f"সঞ্চয় জমা: ৳ {amount:,.2f}"
            )
        else:
            member["savings"] = (
                current_savings - amount
            )
            message = (
                f"সঞ্চয় উত্তোলন: ৳ {amount:,.2f}"
            )

        if note.strip():
            message += f" | {note.strip()}"

        add_history(member, message)

        save_data(data)

        st.success("Transaction সফল হয়েছে।")
        st.rerun()


# ============================================================
# LOAN DISBURSEMENT
# ============================================================

def loan_page(data):
    st.title("🏦 ঋণ প্রদান")

    if not data["members"]:
        st.warning("আগে সদস্য যোগ করুন।")
        return

    member_id = st.selectbox(
        "সদস্য নির্বাচন করুন",
        list(data["members"].keys()),
        format_func=lambda x:
            f"{x} - {data['members'][x].get('name', '')}"
    )

    member = data["members"][member_id]

    if member.get("loan_active", False):
        st.error(
            "এই সদস্যের একটি চলমান ঋণ আছে।"
        )
        return

    c1, c2 = st.columns(2)

    with c1:
        principal = st.number_input(
            "ঋণের পরিমাণ",
            min_value=0.0,
            step=1000.0
        )

        annual_rate = st.number_input(
            "বার্ষিক Interest Rate (%)",
            min_value=0.0,
            max_value=100.0,
            value=10.0,
            step=0.5
        )

        loan_type = st.text_input(
            "ঋণের ধরন",
            value="সাধারণ ঋণ"
        )

    with c2:
        duration = st.number_input(
            "ঋণের মেয়াদ",
            min_value=1,
            max_value=3650,
            value=10,
            step=1
        )

        duration_unit = st.selectbox(
            "মেয়াদের একক",
            ["Days", "Weeks", "Months"],
            format_func=lambda x: {
                "Days": "দিন",
                "Weeks": "সপ্তাহ",
                "Months": "মাস"
            }[x]
        )

    schedule = build_schedule(
        principal,
        annual_rate,
        duration,
        duration_unit
    )

    installment = calculate_emi(
        principal,
        annual_rate,
        duration,
        duration_unit
    )

    total_payable = round(
        sum(row["payment"] for row in schedule),
        2
    )

    total_interest = round(
        total_payable - float(principal),
        2
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "প্রতি কিস্তি",
        f"৳ {installment:,.2f}"
    )

    c2.metric(
        "মোট Interest",
        f"৳ {total_interest:,.2f}"
    )

    c3.metric(
        "মোট পরিশোধ",
        f"৳ {total_payable:,.2f}"
    )

    if schedule:
        with st.expander(
            "📊 Reducing Balance Schedule"
        ):
            schedule_df = pd.DataFrame(schedule)

            schedule_df.columns = [
                "কিস্তি",
                "শুরুর Balance",
                "Interest",
                "মূলধন",
                "Payment",
                "শেষ Balance"
            ]

            st.dataframe(
                schedule_df,
                use_container_width=True,
                hide_index=True
            )

    if st.button(
        "💵 ঋণ প্রদান করুন",
        type="primary",
        use_container_width=True
    ):
        if principal <= 0:
            st.error("ঋণের পরিমাণ দিন।")
            return

        if duration <= 0:
            st.error("মেয়াদ সঠিকভাবে দিন।")
            return

        timestamp = now_string()

        member["loan_principal"] = float(principal)
        member["loan_interest"] = float(total_interest)
        member["loan_type"] = (
            loan_type.strip()
            if loan_type.strip()
            else "সাধারণ ঋণ"
        )
        member["loan_date"] = timestamp
        member["loan_start_date"] = timestamp
        member["loan_last_payment_date"] = timestamp

        member["loan_rate"] = float(annual_rate)
        member["loan_duration"] = int(duration)
        member["loan_duration_unit"] = duration_unit

        member["loan_installment"] = float(installment)
        member["loan_total_payable"] = float(total_payable)
        member["loan_total_paid"] = 0.0

        member["loan_principal_paid"] = 0.0
        member["loan_interest_paid"] = 0.0

        member["loan_remaining_principal"] = float(principal)
        member["loan_remaining_interest"] = float(total_interest)

        member["loan_active"] = True
        member["loan_settled"] = False

        member["loan_next_installment"] = 1
        member["loan_payments"] = []

        add_history(
            member,
            (
                f"ঋণ প্রদান: ৳ {principal:,.2f} | "
                f"Interest Rate: {annual_rate}% | "
                f"মেয়াদ: {duration} {duration_unit} | "
                f"কিস্তি: ৳ {installment:,.2f}"
            )
        )

        save_data(data)

        st.success("ঋণ সফলভাবে প্রদান করা হয়েছে।")
        st.rerun()


# ============================================================
# LOAN COLLECTION
# ============================================================

def collection_page(data):
    st.title("💳 ঋণের টাকা বা কিস্তি আদায়")

    active_members = {
        member_id: member
        for member_id, member in data["members"].items()
        if member.get("loan_active", False)
    }

    if not active_members:
        st.info("বর্তমানে কোনো চলমান ঋণ নেই।")
        return

    member_id = st.selectbox(
        "ঋণগ্রহীতা নির্বাচন করুন",
        list(active_members.keys()),
        format_func=lambda x:
            f"{x} - {active_members[x].get('name', '')}"
    )

    member = active_members[member_id]

    principal_remaining = float(
        member.get("loan_remaining_principal", 0)
    )

    interest_remaining = float(
        member.get("loan_remaining_interest", 0)
    )

    total_remaining = (
        principal_remaining + interest_remaining
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "বাকি মূলধন",
        f"৳ {principal_remaining:,.2f}"
    )

    c2.metric(
        "বাকি Interest",
        f"৳ {interest_remaining:,.2f}"
    )

    c3.metric(
        "মোট বাকি",
        f"৳ {total_remaining:,.2f}"
    )

    st.divider()

    st.write(
        f"নির্ধারিত কিস্তি: "
        f"৳ {float(member.get('loan_installment', 0)):,.2f}"
    )

    st.write(
        f"পরবর্তী কিস্তি: "
        f"{int(member.get('loan_next_installment', 1))}"
    )

    payment_amount = st.number_input(
        "আদায়ের পরিমাণ",
        min_value=0.0,
        step=100.0
    )

    note = st.text_input(
        "নোট",
        placeholder="যেমন: ১ম কিস্তি"
    )

    if st.button(
        "💰 কিস্তি / টাকা আদায় করুন",
        type="primary",
        use_container_width=True
    ):
        if payment_amount <= 0:
            st.error("আদায়ের পরিমাণ দিন।")
            return

        if payment_amount > total_remaining + 0.01:
            st.error(
                f"সর্বোচ্চ ৳ {total_remaining:,.2f} "
                f"আদায় করা যাবে।"
            )
            return

        unit = member.get(
            "loan_duration_unit",
            "Months"
        )

        annual_rate = float(
            member.get("loan_rate", 0)
        )

        rate = periodic_rate(
            annual_rate,
            unit
        )

        # Current reducing-balance period interest.
        period_interest = round(
            principal_remaining * rate,
            2
        )

        # Never exceed remaining scheduled interest.
        period_interest = min(
            period_interest,
            interest_remaining
        )

        # Payment first covers current period interest,
        # then reduces principal.
        interest_paid = min(
            float(payment_amount),
            period_interest
        )

        principal_paid = max(
            0.0,
            float(payment_amount) - interest_paid
        )

        principal_paid = min(
            principal_paid,
            principal_remaining
        )

        # If a tiny rounding amount remains, add it to interest.
        allocated = interest_paid + principal_paid

        if allocated < payment_amount:
            extra = payment_amount - allocated
            interest_paid += extra

        new_principal = max(
            0.0,
            principal_remaining - principal_paid
        )

        new_interest = max(
            0.0,
            interest_remaining - interest_paid
        )

        timestamp = now_string()

        member["loan_remaining_principal"] = round(
            new_principal,
            2
        )

        member["loan_remaining_interest"] = round(
            new_interest,
            2
        )

        member["loan_total_paid"] = round(
            float(member.get("loan_total_paid", 0))
            + float(payment_amount),
            2
        )

        member["loan_principal_paid"] = round(
            float(member.get("loan_principal_paid", 0))
            + principal_paid,
            2
        )

        member["loan_interest_paid"] = round(
            float(member.get("loan_interest_paid", 0))
            + interest_paid,
            2
        )

        member["loan_last_payment_date"] = timestamp

        payment_record = {
            "date": timestamp,
            "amount": round(float(payment_amount), 2),
            "interest_paid": round(interest_paid, 2),
            "principal_paid": round(principal_paid, 2),
            "type": "কিস্তি / আদায়",
            "installment": int(
                member.get("loan_next_installment", 1)
            ),
            "note": note.strip()
        }

        if "loan_payments" not in member:
            member["loan_payments"] = []

        member["loan_payments"].append(
            payment_record
        )

        add_history(
            member,
            (
                f"ঋণ আদায়: ৳ {payment_amount:,.2f} | "
                f"Interest: ৳ {interest_paid:,.2f} | "
                f"মূলধন: ৳ {principal_paid:,.2f}"
                + (
                    f" | {note.strip()}"
                    if note.strip()
                    else ""
                )
            )
        )

        member["loan_next_installment"] = int(
            member.get("loan_next_installment", 1)
        ) + 1

        if (
            member["loan_remaining_principal"] <= 0.01
            and member["loan_remaining_interest"] <= 0.01
        ):
            member["loan_remaining_principal"] = 0.0
            member["loan_remaining_interest"] = 0.0
            member["loan_active"] = False
            member["loan_settled"] = True

            add_history(
                member,
                "ঋণ সম্পূর্ণ পরিশোধ হয়েছে।"
            )

        save_data(data)

        st.success("কিস্তি/টাকা সফলভাবে আদায় হয়েছে।")
        st.rerun()

    # ========================================================
    # EARLY SETTLEMENT
    # ========================================================

    st.divider()
    st.subheader("⚡ Early Settlement")

    settlement = fair_early_settlement(member)

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Outstanding Principal",
        f"৳ {settlement['principal']:,.2f}"
    )

    c2.metric(
        "Fair Interest",
        f"৳ {settlement['fair_interest']:,.2f}"
    )

    c3.metric(
        "Settlement Amount",
        f"৳ {settlement['total']:,.2f}"
    )

    st.write(
        f"শেষ transaction থেকে অতিবাহিত দিন: "
        f"**{settlement['elapsed_days']} দিন**"
    )

    st.success(
        f"Future Interest Discount: "
        f"৳ {settlement['discount']:,.2f}"
    )

    st.caption(
        "Early Settlement-এ ভবিষ্যতের scheduled interest "
        "নেওয়া হবে না; outstanding principal এবং "
        "শেষ payment-এর পর বাস্তবে accrued হওয়া fair interest "
        "ধরা হবে।"
    )

    confirm = st.checkbox(
        "আমি settlement amount দেখে ঋণটি সম্পূর্ণ বন্ধ করতে চাই।"
    )

    if confirm:
        if st.button(
            "⚡ Early Settlement করুন",
            type="secondary",
            use_container_width=True
        ):
            settlement_amount = settlement["total"]
            principal_paid = settlement["principal"]
            interest_paid = settlement["fair_interest"]

            timestamp = now_string()

            member["loan_total_paid"] = round(
                float(member.get("loan_total_paid", 0))
                + settlement_amount,
                2
            )

            member["loan_principal_paid"] = round(
                float(member.get("loan_principal_paid", 0))
                + principal_paid,
                2
            )

            member["loan_interest_paid"] = round(
                float(member.get("loan_interest_paid", 0))
                + interest_paid,
                2
            )

            member["loan_remaining_principal"] = 0.0
            member["loan_remaining_interest"] = 0.0

            member["loan_active"] = False
            member["loan_settled"] = True
            member["loan_last_payment_date"] = timestamp

            if "loan_payments" not in member:
                member["loan_payments"] = []

            member["loan_payments"].append({
                "date": timestamp,
                "amount": settlement_amount,
                "interest_paid": interest_paid,
                "principal_paid": principal_paid,
                "type": "Early Settlement",
                "installment": int(
                    member.get("loan_next_installment", 1)
                ),
                "note": (
                    f"Future Interest Discount: "
                    f"৳ {settlement['discount']:,.2f}"
                )
            })

            add_history(
                member,
                (
                    f"Early Settlement: "
                    f"৳ {settlement_amount:,.2f} | "
                    f"মূলধন: ৳ {principal_paid:,.2f} | "
                    f"Fair Interest: ৳ {interest_paid:,.2f} | "
                    f"Discount: ৳ {settlement['discount']:,.2f}"
                )
            )

            add_history(
                member,
                "Early Settlement-এর মাধ্যমে ঋণ সম্পূর্ণ বন্ধ হয়েছে।"
            )

            save_data(data)

            st.success(
                "Early Settlement সফল হয়েছে।"
            )
            st.rerun()

    # ========================================================
    # PAYMENT HISTORY
    # ========================================================

    if member.get("loan_payments"):
        st.divider()
        st.subheader("📋 Loan Payment History")

        payment_df = pd.DataFrame(
            member["loan_payments"]
        )

        if not payment_df.empty:
            rename_map = {
                "date": "তারিখ ও সময়",
                "amount": "আদায়",
                "interest_paid": "Interest",
                "principal_paid": "মূলধন",
                "type": "ধরন",
                "installment": "কিস্তি",
                "note": "নোট"
            }

            payment_df.rename(
                columns=rename_map,
                inplace=True
            )

            st.dataframe(
                payment_df,
                use_container_width=True,
                hide_index=True
            )


# ============================================================
# MEMBER STATEMENT
# ============================================================

def statement_page(data):
    st.title("📄 সদস্য স্টেটমেন্ট (Statement)")

    if not data["members"]:
        st.info("কোনো সদস্য নেই।")
        return

    member_id = st.selectbox(
        "সদস্য নির্বাচন করুন",
        list(data["members"].keys()),
        format_func=lambda x:
            f"{x} - {data['members'][x].get('name', '')}"
    )

    member = data["members"][member_id]

    st.subheader(
        f"👤 {member.get('name', '')}"
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "সঞ্চয়",
        f"৳ {float(member.get('savings', 0)):,.2f}"
    )

    c2.metric(
        "বাকি মূলধন",
        f"৳ {float(member.get('loan_remaining_principal', 0)):,.2f}"
    )

    c3.metric(
        "বাকি Interest",
        f"৳ {float(member.get('loan_remaining_interest', 0)):,.2f}"
    )

    st.divider()

    st.subheader("🏦 Loan Details")

    loan_details = [
        ["ঋণের ধরন", member.get("loan_type", "নাই")],
        ["ঋণ প্রদানের তারিখ", member.get("loan_date", "")],
        ["বার্ষিক Interest Rate", f"{member.get('loan_rate', 0)}%"],
        [
            "মেয়াদ",
            f"{member.get('loan_duration', 0)} "
            f"{member.get('loan_duration_unit', '')}"
        ],
        [
            "প্রতি কিস্তি",
            f"৳ {float(member.get('loan_installment', 0)):,.2f}"
        ],
        [
            "মূল ঋণ",
            f"৳ {float(member.get('loan_principal', 0)):,.2f}"
        ],
        [
            "Original Interest",
            f"৳ {float(member.get('loan_interest', 0)):,.2f}"
        ],
        [
            "মোট পরিশোধ",
            f"৳ {float(member.get('loan_total_paid', 0)):,.2f}"
        ],
        [
            "বাকি মূলধন",
            f"৳ {float(member.get('loan_remaining_principal', 0)):,.2f}"
        ],
        [
            "বাকি Interest",
            f"৳ {float(member.get('loan_remaining_interest', 0)):,.2f}"
        ],
        [
            "Loan Status",
            (
                "চলমান"
                if member.get("loan_active", False)
                else (
                    "সম্পূর্ণ পরিশোধ"
                    if member.get("loan_settled", False)
                    else "নাই"
                )
            )
        ]
    ]

    st.dataframe(
        pd.DataFrame(
            loan_details,
            columns=["বিষয়", "তথ্য"]
        ),
        use_container_width=True,
        hide_index=True
    )

    # ========================================================
    # PAYMENT HISTORY
    # ========================================================

    if member.get("loan_payments"):
        st.subheader("💳 Loan Payment History")

        payment_df = pd.DataFrame(
            member["loan_payments"]
        )

        rename_map = {
            "date": "তারিখ ও সময়",
            "amount": "আদায়",
            "interest_paid": "Interest",
            "principal_paid": "মূলধন",
            "type": "ধরন",
            "installment": "কিস্তি",
            "note": "নোট"
        }

        payment_df.rename(
            columns=rename_map,
            inplace=True
        )

        st.dataframe(
            payment_df,
            use_container_width=True,
            hide_index=True
        )

    # ========================================================
    # COMPLETE HISTORY
    # ========================================================

    st.subheader("📜 সম্পূর্ণ Transaction History")

    history = member.get("history", [])

    if not history:
        st.info("কোনো history নেই।")
        return

    rows = []

    for item in history:
        if " - " in item:
            timestamp, description = item.split(
                " - ",
                1
            )
        else:
            timestamp = ""
            description = item

        rows.append({
            "তারিখ ও সময়": timestamp,
            "বিবরণ": description
        })

    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# MAIN
# ============================================================

def main():

    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        login_page()
        return

    data = prepare_database(
        load_data()
    )

    # --------------------------------------------------------
    # SIDEBAR
    # --------------------------------------------------------

    st.sidebar.title("💰 আমার সমিতি")
    st.sidebar.success("Admin Logged In")

    pages = [
        "🏠 ড্যাশবোর্ড",
        "👥 সদস্য ব্যবস্থাপনা",
        "💰 সঞ্চয় জমা / উত্তোলন",
        "🏦 ঋণ প্রদান",
        "💳 ঋণের টাকা বা কিস্তি আদায়",
        "📄 সদস্য স্টেটমেন্ট (Statement)"
    ]

    selected_page = st.sidebar.radio(
        "Menu",
        pages
    )

    st.sidebar.divider()

    if st.sidebar.button(
        "🚪 Logout",
        use_container_width=True
    ):
        st.session_state["logged_in"] = False
        st.rerun()

    # --------------------------------------------------------
    # PAGE ROUTING
    # --------------------------------------------------------

    if selected_page == "🏠 ড্যাশবোর্ড":
        dashboard_page(data)

    elif selected_page == "👥 সদস্য ব্যবস্থাপনা":
        member_page(data)

    elif selected_page == "💰 সঞ্চয় জমা / উত্তোলন":
        savings_page(data)

    elif selected_page == "🏦 ঋণ প্রদান":
        loan_page(data)

    elif selected_page == "💳 ঋণের টাকা বা কিস্তি আদায়":
        collection_page(data)

    elif selected_page == "📄 সদস্য স্টেটমেন্ট (Statement)":
        statement_page(data)


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()
