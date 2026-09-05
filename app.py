```python
import os
import json
import math
from datetime import datetime, date

import streamlit as st
import pandas as pd


# ============================================================
# APP CONFIG
# ============================================================

st.set_page_config(
    page_title="আমার সমিতি",
    page_icon="💰",
    layout="wide"
)


# ============================================================
# LOGIN
# ============================================================

ADMIN_USER = "admin"
ADMIN_PASS = "somity2026"

DB_FILE = "database.json"


# ============================================================
# DATABASE FUNCTIONS
# ============================================================

def now_string():
    """Current date and time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def load_data():
    """Load database.json safely."""

    if not os.path.exists(DB_FILE):
        return {"members": {}}

    try:
        with open(DB_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        if "members" not in data:
            data["members"] = {}

        return data

    except Exception:
        return {"members": {}}


def save_data(data):
    """Save database.json."""

    with open(DB_FILE, "w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=4
        )


def add_history(member, message):
    """Add timestamped history."""

    if "history" not in member:
        member["history"] = []

    member["history"].append(
        f"{now_string()} - {message}"
    )


def normalize_member(member):
    """
    Existing database.json members may not contain
    the new loan-tracking fields.

    This function adds missing fields automatically.
    """

    defaults = {
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
        "loan_payments": [],
        "history": []
    }

    for key, value in defaults.items():
        if key not in member:
            member[key] = value

    return member


def prepare_database(data):
    """Normalize all members."""

    for member_id in data["members"]:
        data["members"][member_id] = normalize_member(
            data["members"][member_id]
        )

    return data


# ============================================================
# LOAN CALCULATION FUNCTIONS
# ============================================================

def get_periods_per_year(unit):
    """Number of installment periods in one year."""

    if unit == "Days":
        return 365

    if unit == "Weeks":
        return 52

    return 12


def calculate_emi(principal, annual_rate, duration, unit):
    """
    Reducing Balance EMI.

    annual_rate = annual interest percentage.

    Example:
    Principal = 100000
    Annual rate = 10%
    Duration = 10 Months
    """

    if principal <= 0 or duration <= 0:
        return 0.0

    if annual_rate <= 0:
        return principal / duration

    periods_per_year = get_periods_per_year(unit)

    periodic_rate = (annual_rate / 100) / periods_per_year

    if periodic_rate == 0:
        return principal / duration

    emi = (
        principal
        * periodic_rate
        * ((1 + periodic_rate) ** duration)
        / (((1 + periodic_rate) ** duration) - 1)
    )

    return round(emi, 2)


def calculate_loan_schedule(
    principal,
    annual_rate,
    duration,
    unit
):
    """
    Generate complete reducing-balance loan schedule.
    """

    emi = calculate_emi(
        principal,
        annual_rate,
        duration,
        unit
    )

    periods_per_year = get_periods_per_year(unit)

    periodic_rate = (
        annual_rate / 100 / periods_per_year
    )

    balance = float(principal)

    schedule = []

    for period in range(1, duration + 1):

        if balance <= 0:
            break

        if periodic_rate > 0:
            interest = balance * periodic_rate
        else:
            interest = 0

        principal_part = emi - interest

        # Last installment adjustment
        if principal_part > balance:
            principal_part = balance
            payment = principal_part + interest
        else:
            payment = emi

        ending_balance = balance - principal_part

        if ending_balance < 0:
            ending_balance = 0

        schedule.append({
            "period": period,
            "opening_balance": round(balance, 2),
            "interest": round(interest, 2),
            "principal": round(principal_part, 2),
            "payment": round(payment, 2),
            "closing_balance": round(ending_balance, 2)
        })

        balance = ending_balance

    return schedule


def calculate_elapsed_days(start_date_string):
    """Calculate elapsed days from loan start."""

    if not start_date_string:
        return 0

    try:
        start = datetime.strptime(
            start_date_string,
            "%Y-%m-%d %H:%M:%S"
        )

        elapsed = (
            datetime.now() - start
        ).total_seconds() / 86400

        return max(0, int(elapsed))

    except Exception:
        return 0


def calculate_fair_settlement(member):
    """
    Early Settlement Logic.

    We do NOT charge future/unearned interest.

    The settlement interest is based on elapsed days
    and current outstanding principal.

    Therefore the member receives a fair discount because
    future scheduled interest is waived.
    """

    principal = float(
        member.get("loan_remaining_principal", 0)
    )

    annual_rate = float(
        member.get("loan_rate", 0)
    )

    if principal <= 0:
        return {
            "principal": 0.0,
            "interest": 0.0,
            "total": 0.0,
            "future_interest_discount": 0.0
        }

    start_date = member.get(
        "loan_start_date",
        member.get("loan_date", "")
    )

    elapsed_days = calculate_elapsed_days(
        start_date
    )

    # Daily reducing-balance accrued interest.
    accrued_interest = (
        principal
        * (annual_rate / 100)
        * (elapsed_days / 365)
    )

    accrued_interest = round(
        max(0, accrued_interest),
        2
    )

    # Scheduled remaining interest
    scheduled_remaining_interest = float(
        member.get("loan_remaining_interest", 0)
    )

    # Future interest waived.
    discount = max(
        0,
        scheduled_remaining_interest - accrued_interest
    )

    total = principal + accrued_interest

    return {
        "principal": round(principal, 2),
        "interest": round(accrued_interest, 2),
        "total": round(total, 2),
        "future_interest_discount": round(discount, 2),
        "elapsed_days": elapsed_days
    }


def current_loan_status(member):
    """Calculate current loan information."""

    principal = float(
        member.get("loan_remaining_principal", 0)
    )

    interest = float(
        member.get("loan_remaining_interest", 0)
    )

    return {
        "principal": round(principal, 2),
        "interest": round(interest, 2),
        "total": round(principal + interest, 2)
    }


# ============================================================
# LOGIN PAGE
# ============================================================

def login_page():

    st.title("🔐 আমার সমিতি")
    st.subheader("Admin Login")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:

        username = st.text_input(
            "Username"
        )

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
                st.error(
                    "Username অথবা Password ভুল।"
                )


# ============================================================
# DASHBOARD
# ============================================================

def dashboard_page(data):

    st.title("🏠 Dashboard")

    members = data["members"]

    total_members = len(members)

    total_savings = sum(
        float(m.get("savings", 0))
        for m in members.values()
    )

    active_loans = [
        m for m in members.values()
        if m.get("loan_active", False)
    ]

    total_loan = sum(
        float(m.get("loan_remaining_principal", 0))
        for m in active_loans
    )

    total_interest = sum(
        float(m.get("loan_remaining_interest", 0))
        for m in active_loans
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "মোট সদস্য",
        total_members
    )

    col2.metric(
        "মোট সঞ্চয়",
        f"৳ {total_savings:,.2f}"
    )

    col3.metric(
        "চলমান ঋণ",
        f"৳ {total_loan:,.2f}"
    )

    col4.metric(
        "বাকি Interest",
        f"৳ {total_interest:,.2f}"
    )

    st.divider()

    if members:

        rows = []

        for member_id, member in members.items():

            status = (
                "চলমান"
                if member.get("loan_active")
                else "নাই"
            )

            rows.append({
                "Member ID": member_id,
                "নাম": member.get("name", ""),
                "সঞ্চয়": member.get("savings", 0),
                "ঋণের মূলধন": member.get(
                    "loan_remaining_principal",
                    0
                ),
                "বাকি Interest": member.get(
                    "loan_remaining_interest",
                    0
                ),
                "ঋণ Status": status
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
        "নতুন সদস্য",
        "সদস্য তালিকা"
    ])

    with tab1:

        member_id = st.text_input(
            "মোবাইল / সদস্য ID"
        )

        name = st.text_input(
            "সদস্যের নাম"
        )

        initial_savings = st.number_input(
            "প্রাথমিক সঞ্চয়",
            min_value=0.0,
            step=100.0
        )

        if st.button(
            "সদস্য যোগ করুন",
            type="primary"
        ):

            member_id = member_id.strip()

            if not member_id:
                st.error("সদস্য ID দিন।")

            elif not name.strip():
                st.error("সদস্যের নাম দিন।")

            elif member_id in data["members"]:
                st.error(
                    "এই সদস্য ইতিমধ্যে আছে।"
                )

            else:

                timestamp = now_string()

                data["members"][member_id] = {
                    "name": name.strip(),
                    "savings": float(initial_savings),
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
                    "loan_payments": [],
                    "history": [
                        f"{timestamp} - হিসাব খোলা হয়েছে।"
                    ]
                }

                save_data(data)

                st.success(
                    "সদস্য সফলভাবে যোগ হয়েছে।"
                )

    with tab2:

        if not data["members"]:
            st.info("কোনো সদস্য নেই।")
            return

        rows = []

        for member_id, member in data["members"].items():

            rows.append({
                "ID": member_id,
                "নাম": member.get("name", ""),
                "সঞ্চয়": member.get("savings", 0),
                "Loan": member.get(
                    "loan_remaining_principal",
                    0
                ),
                "Status": (
                    "চলমান"
                    if member.get("loan_active")
                    else "নাই"
                )
            })

        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# SAVINGS PAGE
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

    st.info(
        f"বর্তমান সঞ্চয়: "
        f"৳ {float(member.get('savings', 0)):,.2f}"
    )

    transaction_type = st.radio(
        "Transaction Type",
        ["জমা", "উত্তোলন"],
        horizontal=True
    )

    amount = st.number_input(
        "টাকার পরিমাণ",
        min_value=0.0,
        step=100.0
    )

    note = st.text_input(
        "নোট",
        placeholder="যেমন: মাসিক সঞ্চয়"
    )

    if st.button(
        "Transaction সম্পন্ন করুন",
        type="primary"
    ):

        if amount <= 0:
            st.error("টাকার পরিমাণ দিন।")
            return

        if (
            transaction_type == "উত্তোলন"
            and amount > float(member.get("savings", 0))
        ):
            st.error(
                "পর্যাপ্ত সঞ্চয় নেই।"
            )
            return

        if transaction_type == "জমা":

            member["savings"] = (
                float(member.get("savings", 0))
                + amount
            )

            message = (
                f"সঞ্চয় জমা: ৳ {amount:,.2f}"
            )

        else:

            member["savings"] = (
                float(member.get("savings", 0))
                - amount
            )

            message = (
                f"সঞ্চয় উত্তোলন: ৳ {amount:,.2f}"
            )

        if note.strip():
            message += f" | {note.strip()}"

        add_history(member, message)

        save_data(data)

        st.success(
            "Transaction সফল হয়েছে।"
        )

        st.rerun()


# ============================================================
# LOAN DISBURSEMENT PAGE
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
            "এই সদস্যের একটি চলমান ঋণ আছে। "
            "নতুন ঋণ দেওয়ার আগে পুরোনো ঋণ সম্পন্ন করুন।"
        )

        status = current_loan_status(member)

        st.write(
            f"বর্তমান বাকি মূলধন: "
            f"৳ {status['principal']:,.2f}"
        )

        st.write(
            f"বর্তমান বাকি Interest: "
            f"৳ {status['interest']:,.2f}"
        )

        return

    st.subheader(
        f"সদস্য: {member.get('name', '')}"
    )

    col1, col2 = st.columns(2)

    with col1:

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

    with col2:

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

    emi = calculate_emi(
        principal,
        annual_rate,
        duration,
        duration_unit
    )

    schedule = calculate_loan_schedule(
        principal,
        annual_rate,
        duration,
        duration_unit
    )

    total_payable = sum(
        item["payment"]
        for item in schedule
    )

    total_interest = (
        total_payable - principal
    )

    st.divider()

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "প্রতি কিস্তি",
        f"৳ {emi:,.2f}"
    )

    col2.metric(
        "মোট Interest",
        f"৳ {total_interest:,.2f}"
    )

    col3.metric(
        "মোট পরিশোধ",
        f"৳ {total_payable:,.2f}"
    )

    if schedule:

        with st.expander(
            "📊 Reducing Balance Loan Schedule দেখুন"
        ):

            schedule_df = pd.DataFrame(
                schedule
            )

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
            st.error(
                "ঋণের পরিমাণ দিন।"
            )
            return

        if duration <= 0:
            st.error(
                "মেয়াদ সঠিকভাবে দিন।"
            )
            return

        timestamp = now_string()

        member["loan_principal"] = float(
            principal
        )

        member["loan_interest"] = float(
            total_interest
        )

        member["loan_type"] = (
            loan_type.strip()
            if loan_type.strip()
            else "সাধারণ ঋণ"
        )

        member["loan_date"] = timestamp
        member["loan_start_date"] = timestamp
        member["loan_rate"] = float(
            annual_rate
        )

        member["loan_duration"] = int(
            duration
        )

        member["loan_duration_unit"] = (
            duration_unit
        )

        member["loan_installment"] = float(
            emi
        )

        member["loan_total_payable"] = float(
            total_payable
        )

        member["loan_total_paid"] = 0.0
        member["loan_principal_paid"] = 0.0
        member["loan_interest_paid"] = 0.0

        member["loan_remaining_principal"] = (
            float(principal)
        )

        member["loan_remaining_interest"] = (
            float(total_interest)
        )

        member["loan_active"] = True
        member["loan_settled"] = False
        member["loan_payments"] = []

        add_history(
            member,
            (
                f"ঋণ প্রদান: ৳ {principal:,.2f} | "
                f"Rate: {annual_rate}% | "
                f"মেয়াদ: {duration} "
                f"{duration_unit} | "
                f"কিস্তি: ৳ {emi:,.2f}"
            )
        )

        save_data(data)

        st.success(
            "ঋণ সফলভাবে প্রদান করা হয়েছে।"
        )

        st.rerun()


# ============================================================
# LOAN COLLECTION PAGE
# ============================================================

def collection_page(data):

    st.title("💳 ঋণের টাকা বা কিস্তি আদায়")

    active_members = {
        member_id: member
        for member_id, member in data["members"].items()
        if member.get("loan_active", False)
    }

    if not active_members:
        st.info(
            "বর্তমানে কোনো চলমান ঋণ নেই।"
        )
        return

    member_id = st.selectbox(
        "ঋণগ্রহীতা নির্বাচন করুন",
        list(active_members.keys()),
        format_func=lambda x:
            f"{x} - {active_members[x].get('name', '')}"
    )

    member = active_members[member_id]

    status = current_loan_status(member)

    st.subheader(
        f"👤 {member.get('name', '')}"
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "বাকি মূলধন",
        f"৳ {status['principal']:,.2f}"
    )

    col2.metric(
        "বাকি Interest",
        f"৳ {status['interest']:,.2f}"
    )

    col3.metric(
        "মোট বাকি",
        f"৳ {status['total']:,.2f}"
    )

    st.divider()

    st.write(
        f"নির্ধারিত কিস্তি: "
        f"৳ {float(member.get('loan_installment', 0)):,.2f}"
    )

    st.write(
        f"Rate: "
        f"{float(member.get('loan_rate', 0))}%"
    )

    st.write(
        f"মেয়াদ: "
        f"{member.get('loan_duration', 0)} "
        f"{member.get('loan_duration_unit', '')}"
    )

    payment_amount = st.number_input(
        "আদায়ের পরিমাণ",
        min_value=0.0,
        step=100.0
    )

    payment_note = st.text_input(
        "আদায়ের নোট",
        placeholder="যেমন: ১ম কিস্তি"
    )

    if st.button(
        "💰 কিস্তি / টাকা আদায় করুন",
        type="primary",
        use_container_width=True
    ):

        if payment_amount <= 0:
            st.error(
                "আদায়ের পরিমাণ দিন।"
            )
            return

        total_remaining = (
            status["principal"]
            + status["interest"]
        )

        if payment_amount > total_remaining:
            st.error(
                f"সর্বোচ্চ ৳ {total_remaining:,.2f} "
                f"আদায় করা যাবে।"
            )
            return

        # ----------------------------------------------------
        # Payment allocation:
        # First interest, then principal.
        # ----------------------------------------------------

        remaining_payment = float(
            payment_amount
        )

        interest_paid = min(
            remaining_payment,
            status["interest"]
        )

        remaining_payment -= interest_paid

        principal_paid = min(
            remaining_payment,
            status["principal"]
        )

        member["loan_interest_paid"] = (
            float(member.get("loan_interest_paid", 0))
            + interest_paid
        )

        member["loan_principal_paid"] = (
            float(member.get("loan_principal_paid", 0))
            + principal_paid
        )

        member["loan_total_paid"] = (
            float(member.get("loan_total_paid", 0))
            + payment_amount
        )

        member["loan_remaining_interest"] = max(
            0,
            status["interest"] - interest_paid
        )

        member["loan_remaining_principal"] = max(
            0,
            status["principal"] - principal_paid
        )

        timestamp = now_string()

        payment_record = {
            "date": timestamp,
            "amount": round(payment_amount, 2),
            "interest_paid": round(interest_paid, 2),
            "principal_paid": round(principal_paid, 2),
            "type": "কিস্তি / আদায়",
            "note": payment_note.strip()
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
                    f" | {payment_note.strip()}"
                    if payment_note.strip()
                    else ""
                )
            )
        )

        # Loan completed
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

        st.success(
            "কিস্তি/টাকা সফলভাবে আদায় হয়েছে।"
        )

        st.rerun()

    # --------------------------------------------------------
    # EARLY SETTLEMENT
    # --------------------------------------------------------

    st.divider()

    st.subheader(
        "⚡ Early Settlement"
    )

    settlement = calculate_fair_settlement(
        member
    )

    st.write(
        f"Elapsed Days: "
        f"**{settlement['elapsed_days']} দিন**"
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "মূলধন",
        f"৳ {settlement['principal']:,.2f}"
    )

    col2.metric(
        "Fair Interest",
        f"৳ {settlement['interest']:,.2f}"
    )

    col3.metric(
        "Settlement Amount",
        f"৳ {settlement['total']:,.2f}"
    )

    st.info(
        "Early Settlement করলে ভবিষ্যতের অনর্জিত "
        "scheduled interest নেওয়া হবে না। "
        "শুধু outstanding principal এবং elapsed-days "
        "অনুযায়ী fair interest নেওয়া হবে।"
    )

    st.success(
        f"Future Interest Discount: "
        f"৳ {settlement['future_interest_discount']:,.2f}"
    )

    confirm = st.checkbox(
        "আমি Early Settlement-এর হিসাব বুঝেছি এবং ঋণটি সম্পূর্ণ বন্ধ করতে চাই।"
    )

    if confirm:

        if st.button(
            "⚡ Early Settlement করুন",
            type="secondary",
            use_container_width=True
        ):

            settlement_amount = settlement["total"]

            principal = settlement["principal"]
            fair_interest = settlement["interest"]

            timestamp = now_string()

            member["loan_total_paid"] = (
                float(member.get("loan_total_paid", 0))
                + settlement_amount
            )

            member["loan_principal_paid"] = (
                float(member.get("loan_principal_paid", 0))
                + principal
            )

            member["loan_interest_paid"] = (
                float(member.get("loan_interest_paid", 0))
                + fair_interest
            )

            member["loan_remaining_principal"] = 0.0
            member["loan_remaining_interest"] = 0.0
            member["loan_active"] = False
            member["loan_settled"] = True

            if "loan_payments" not in member:
                member["loan_payments"] = []

            member["loan_payments"].append({
                "date": timestamp,
                "amount": settlement_amount,
                "interest_paid": fair_interest,
                "principal_paid": principal,
                "type": "Early Settlement",
                "note": (
                    f"Future interest discount: "
                    f"৳ {settlement['future_interest_discount']:,.2f}"
                )
            })

            add_history(
                member,
                (
                    f"Early Settlement: "
                    f"৳ {settlement_amount:,.2f} | "
                    f"মূলধন: ৳ {principal:,.2f} | "
                    f"Fair Interest: ৳ {fair_interest:,.2f} | "
                    f"Interest Discount: "
                    f"৳ {settlement['future_interest_discount']:,.2f}"
                )
            )

            add_history(
                member,
                "Early Settlement-এর মাধ্যমে ঋণ সম্পূর্ণ বন্ধ হয়েছে।"
            )

            save_data(data)

            st.success(
                "Early Settlement সফল হয়েছে। "
                "ঋণ সম্পূর্ণ বন্ধ করা হয়েছে।"
            )

            st.rerun()

    # --------------------------------------------------------
    # PAYMENT HISTORY
    # --------------------------------------------------------

    if member.get("loan_payments"):

        st.divider()

        st.subheader(
            "📋 Loan Payment History"
        )

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
                "note": "নোট"
            }

            payment_df = payment_df.rename(
                columns=rename_map
            )

            st.dataframe(
                payment_df,
                use_container_width=True,
                hide_index=True
            )


# ============================================================
# MEMBER STATEMENT PAGE
# ============================================================

def statement_page(data):

    st.title("📄 সদস্য স্টেটমেন্ট (Statement)")

    if not data["members"]:
        st.info(
            "কোনো সদস্য নেই।"
        )
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

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "সঞ্চয়",
        f"৳ {float(member.get('savings', 0)):,.2f}"
    )

    col2.metric(
        "Loan Principal",
        f"৳ {float(member.get('loan_remaining_principal', 0)):,.2f}"
    )

    col3.metric(
        "Loan Interest",
        f"৳ {float(member.get('loan_remaining_interest', 0)):,.2f}"
    )

    st.divider()

    st.subheader(
        "📜 সম্পূর্ণ Transaction History"
    )

    history = member.get(
        "history",
        []
    )

    if history:

        statement_rows = []

        for item in history:

            if " - " in item:

                timestamp, description = item.split(
                    " - ",
                    1
                )

            else:

                timestamp = ""
                description = item

            statement_rows.append({
                "তারিখ ও সময়": timestamp,
                "বিবরণ": description
            })

        statement_df = pd.DataFrame(
            statement_rows
        )

        st.dataframe(
            statement_df,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "এই সদস্যের কোনো history নেই।"
        )

    # --------------------------------------------------------
    # LOAN INFORMATION
    # --------------------------------------------------------

    if member.get("loan_principal", 0) > 0:

        st.divider()

        st.subheader(
            "🏦 Loan Details"
        )

        loan_info = {
            "ঋণের ধরন": member.get(
                "loan_type", "নাই"
            ),
            "ঋণ প্রদানের তারিখ": member.get(
                "loan_date", ""
            ),
            "বার্ষিক Rate": f"{member.get('loan_rate', 0)}%",
            "মেয়াদ": (
                f"{member.get('loan_duration', 0)} "
                f"{member.get('loan_duration_unit', '')}"
            ),
            "প্রতি কিস্তি": (
                f"৳ {float(member.get('loan_installment', 0)):,.2f}"
            ),
            "মূল ঋণ": (
                f"৳ {float(member.get('loan_principal', 0)):,.2f}"
            ),
            "Original Interest": (
                f"৳ {float(member.get('loan_interest', 0)):,.2f}"
            ),
            "মোট পরিশোধ": (
                f"৳ {float(member.get('loan_total_paid', 0)):,.2f}"
            ),
            "বাকি মূলধন": (
                f"৳ {float(member.get('loan_remaining_principal', 0)):,.2f}"
            ),
            "বাকি Interest": (
                f"৳ {float(member.get('loan_remaining_interest', 0)):,.2f}"
            ),
            "Loan Status": (
                "চলমান"
                if member.get("loan_active")
                else (
                    "সম্পূর্ণ পরিশোধ"
                    if member.get("loan_settled")
                    else "নাই"
                )
            )
        }

        loan_df = pd.DataFrame(
            list(loan_info.items()),
            columns=["বিষয়", "তথ্য"]
        )

        st.dataframe(
            loan_df,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# MAIN APPLICATION
# ============================================================

def main():

    # --------------------------------------------------------
    # LOGIN
    # --------------------------------------------------------

    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:

        login_page()
        return

    # --------------------------------------------------------
    # LOAD DATABASE
    # --------------------------------------------------------

    data = load_data()
    data = prepare_database(data)

    # --------------------------------------------------------
    # SIDEBAR
    # --------------------------------------------------------

    st.sidebar.title("💰 আমার সমিতি")

    st.sidebar.success(
        "Admin Logged In"
    )

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

    # ========================================================
    # IMPORTANT:
    # Sidebar names and conditions are EXACTLY the same.
    # ========================================================

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
# RUN
# ============================================================

if __name__ == "__main__":
    main()
```
