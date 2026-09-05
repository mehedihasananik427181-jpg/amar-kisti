import streamlit as st
import json
import os
from datetime import datetime, timedelta
import pandas as pd
import re

# Page configuration
st.set_page_config(
    page_title="Somity Management System",
    page_icon="🏦",
    layout="wide"
)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'data' not in st.session_state:
    st.session_state.data = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Dashboard"

# File handling
DATA_FILE = "database.json"

def load_data():
    """Load data from JSON file"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"members": {}}

def save_data(data):
    """Save data to JSON file"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# Authentication
def authenticate(username, password):
    return username == "admin" and password == "somity2026"

# Member functions
def add_member(data, phone, name):
    """Add a new member"""
    if phone in data["members"]:
        return False, "সদস্য ইতিমধ্যে বিদ্যমান!"
    
    data["members"][phone] = {
        "name": name,
        "savings": 0.0,
        "loan_principal": 0.0,
        "loan_interest": 0.0,
        "loan_type": "নাই",
        "loan_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "loan_rate": 10,
        "loan_duration": 10,
        "history": [f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - হিসাব খোলা হয়েছে।"]
    }
    save_data(data)
    return True, "সদস্য সফলভাবে যোগ করা হয়েছে!"

def calculate_reducing_balance(principal, rate, duration, duration_type):
    """Calculate EMI using reducing balance method"""
    if duration_type == "Days":
        n = duration
        r = (rate / 100) / 365
    elif duration_type == "Weeks":
        n = duration * 7
        r = (rate / 100) / 365
    else:  # Months
        n = duration * 30
        r = (rate / 100) / 365
    
    if r == 0:
        emi = principal / n if n > 0 else 0
    else:
        emi = principal * r * ((1 + r) ** n) / (((1 + r) ** n) - 1)
    
    return emi, n

def get_early_settlement_amount(principal, rate, loan_date, duration_type):
    """Calculate early settlement amount with fair interest discount"""
    elapsed_days = (datetime.now() - datetime.strptime(loan_date, "%Y-%m-%d %H:%M:%S")).days
    
    if elapsed_days <= 0:
        return principal
    
    if duration_type == "Days":
        total_days = 30  # Default to 30 days for daily loans
    elif duration_type == "Weeks":
        total_days = 30
    else:  # Months
        total_days = 30
    
    daily_rate = (rate / 100) / 365
    remaining_days = max(0, total_days - elapsed_days)
    
    # Calculate interest for actual days used
    interest_used = principal * daily_rate * elapsed_days
    total_amount = principal + interest_used
    
    # Apply discount for early settlement
    if remaining_days > 0:
        discount_factor = min(0.5, (remaining_days / total_days) * 0.5)
        discount = interest_used * discount_factor
        total_amount = principal + (interest_used - discount)
    
    return max(principal, total_amount)

# Page functions
def show_dashboard():
    """Dashboard page"""
    st.title("🏦 সোমিটি ম্যানেজমেন্ট সিস্টেম - ড্যাশবোর্ড")
    
    data = st.session_state.data
    total_members = len(data["members"])
    total_savings = sum(m["savings"] for m in data["members"].values())
    total_loans = sum(m["loan_principal"] for m in data["members"].values())
    active_loans = sum(1 for m in data["members"].values() if m["loan_type"] != "নাই")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("👥 মোট সদস্য", total_members)
    with col2:
        st.metric("💰 মোট সঞ্চয়", f"৳{total_savings:,.2f}")
    with col3:
        st.metric("💳 মোট ঋণ", f"৳{total_loans:,.2f}")
    with col4:
        st.metric("📊 সক্রিয় ঋণ", active_loans)
    
    # Recent activity
    st.subheader("📋 সাম্প্রতিক কার্যক্রম")
    activities = []
    for phone, member in data["members"].items():
        for history in member["history"][-3:]:
            activities.append((history, member["name"], phone))
    
    if activities:
        activities.sort(reverse=True)
        for activity, name, phone in activities[:10]:
            st.write(f"📌 {activity} - {name} ({phone})")
    else:
        st.info("কোনো কার্যক্রম পাওয়া যায়নি।")

def show_members():
    """Manage members page"""
    st.title("👥 সদস্য ব্যবস্থাপনা")
    
    data = st.session_state.data
    
    # Add member
    with st.expander("➕ নতুন সদস্য যোগ করুন"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("সদস্যের নাম")
        with col2:
            phone = st.text_input("মোবাইল নম্বর")
        
        if st.button("সদস্য যোগ করুন", type="primary"):
            if name and phone:
                if re.match(r'^01[3-9]\d{8}$', phone):
                    success, msg = add_member(data, phone, name)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.error("সঠিক মোবাইল নম্বর দিন (01XXXXXXXXX)")
            else:
                st.error("সব তথ্য পূরণ করুন")
    
    # Member list
    st.subheader("📋 সদস্যের তালিকা")
    if data["members"]:
        df = pd.DataFrame([
            {
                "নাম": m["name"],
                "মোবাইল": phone,
                "সঞ্চয়": f"৳{m['savings']:,.2f}",
                "ঋণ": f"৳{m['loan_principal']:,.2f}",
                "ঋণের ধরন": m["loan_type"]
            }
            for phone, m in data["members"].items()
        ])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("কোনো সদস্য নেই। নতুন সদস্য যোগ করুন।")

def show_savings():
    """Savings management page"""
    st.title("💰 সঞ্চয় ব্যবস্থাপনা")
    
    data = st.session_state.data
    
    if not data["members"]:
        st.warning("কোনো সদস্য নেই। প্রথমে সদস্য যোগ করুন।")
        return
    
    selected_phone = st.selectbox(
        "সদস্য নির্বাচন করুন",
        options=list(data["members"].keys()),
        format_func=lambda x: f"{data['members'][x]['name']} ({x})"
    )
    
    if selected_phone:
        member = data["members"][selected_phone]
        st.info(f"**{member['name']}** - বর্তমান সঞ্চয়: ৳{member['savings']:,.2f}")
        
        col1, col2 = st.columns(2)
        with col1:
            amount = st.number_input("সঞ্চয়ের পরিমাণ (টাকা)", min_value=0.0, step=100.0)
        with col2:
            action = st.radio("কার্যক্রম", ["জমা", "উত্তোলন"])
        
        if st.button("সঞ্চয় আপডেট করুন", type="primary"):
            if amount > 0:
                if action == "জমা":
                    member["savings"] += amount
                    member["history"].append(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - সঞ্চয় জমা: ৳{amount:,.2f}")
                else:
                    if member["savings"] >= amount:
                        member["savings"] -= amount
                        member["history"].append(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - সঞ্চয় উত্তোলন: ৳{amount:,.2f}")
                    else:
                        st.error("পর্যাপ্ত সঞ্চয় নেই!")
                        return
                
                save_data(data)
                st.success("সঞ্চয় সফলভাবে আপডেট করা হয়েছে!")
                st.rerun()
            else:
                st.error("সঠিক পরিমাণ দিন")

def show_loan_management():
    """Loan management page"""
    st.title("💳 ঋণ ব্যবস্থাপনা")
    
    data = st.session_state.data
    
    if not data["members"]:
        st.warning("কোনো সদস্য নেই। প্রথমে সদস্য যোগ করুন।")
        return
    
    selected_phone = st.selectbox(
        "সদস্য নির্বাচন করুন",
        options=list(data["members"].keys()),
        format_func=lambda x: f"{data['members'][x]['name']} ({x})",
        key="loan_member"
    )
    
    if selected_phone:
        member = data["members"][selected_phone]
        
        # Loan information
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("ঋণের পরিমাণ", f"৳{member['loan_principal']:,.2f}")
        with col2:
            st.metric("সুদের পরিমাণ", f"৳{member['loan_interest']:,.2f}")
        with col3:
            st.metric("ঋণের ধরন", member["loan_type"])
        
        if member["loan_type"] == "নাই":
            # New loan
            st.subheader("🔴 নতুন ঋণ নিবন্ধন")
            col1, col2 = st.columns(2)
            with col1:
                loan_amount = st.number_input("ঋণের পরিমাণ", min_value=0.0, step=1000.0)
                loan_rate = st.number_input("সুদের হার (%)", min_value=0.0, max_value=100.0, step=0.5, value=10.0)
            with col2:
                duration_value = st.number_input("মেয়াদ", min_value=1, step=1, value=12)
                duration_type = st.selectbox("মেয়াদের ধরণ", ["Days", "Weeks", "Months"])
            
            if st.button("ঋণ দিন", type="primary"):
                if loan_amount > 0:
                    member["loan_principal"] = loan_amount
                    member["loan_rate"] = loan_rate
                    member["loan_duration"] = duration_value
                    member["loan_type"] = duration_type
                    member["loan_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    member["history"].append(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - ঋণ গ্রহণ: ৳{loan_amount:,.2f}")
                    
                    # Calculate EMI
                    emi, total_installments = calculate_reducing_balance(loan_amount, loan_rate, duration_value, duration_type)
                    member["loan_interest"] = (emi * total_installments) - loan_amount
                    
                    save_data(data)
                    st.success(f"ঋণ সফলভাবে দেওয়া হয়েছে! EMI: ৳{emi:,.2f}")
                    st.rerun()
                else:
                    st.error("সঠিক ঋণের পরিমাণ দিন")
        
        else:
            # Existing loan
            st.subheader("📊 ঋণের বিবরণ")
            
            # Calculate EMI
            emi, total_installments = calculate_reducing_balance(
                member["loan_principal"],
                member["loan_rate"],
                member["loan_duration"],
                member["loan_type"]
            )
            
            st.info(f"**EMI (কিস্তি):** ৳{emi:,.2f} | **মোট কিস্তি:** {total_installments}")
            
            col1, col2 = st.columns(2)
            with col1:
                payment_amount = st.number_input("কিস্তির পরিমাণ", min_value=0.0, step=100.0)
            with col2:
                if st.button("কিস্তি আদায় করুন", type="primary"):
                    if payment_amount > 0:
                        # Reduce principal
                        if payment_amount >= member["loan_principal"]:
                            # Loan fully paid
                            member["history"].append(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - ঋণ সম্পূর্ণ পরিশোধ: ৳{member['loan_principal']:,.2f}")
                            member["loan_principal"] = 0
                            member["loan_interest"] = 0
                            member["loan_type"] = "নাই"
                            st.success("ঋণ সম্পূর্ণ পরিশোধ করা হয়েছে!")
                        else:
                            member["loan_principal"] -= payment_amount
                            member["history"].append(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - কিস্তি আদায়: ৳{payment_amount:,.2f}")
                            st.success(f"কিস্তি আদায় করা হয়েছে! বাকি: ৳{member['loan_principal']:,.2f}")
                        
                        save_data(data)
                        st.rerun()
                    else:
                        st.error("সঠিক পরিমাণ দিন")
            
            # Early settlement
            if st.button("🏷️ অনার্লি সেটেলমেন্ট (Early Settlement)", type="warning"):
                early_amount = get_early_settlement_amount(
                    member["loan_principal"] + member["loan_interest"],
                    member["loan_rate"],
                    member["loan_date"],
                    member["loan_type"]
                )
                
                st.info(f"**অনার্লি সেটেলমেন্টের পরিমাণ:** ৳{early_amount:,.2f}")
                
                if st.button("✅ সেটেলমেন্ট নিশ্চিত করুন", type="primary"):
                    member["history"].append(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - অনার্লি সেটেলমেন্ট: ৳{early_amount:,.2f}")
                    member["loan_principal"] = 0
                    member["loan_interest"] = 0
                    member["loan_type"] = "নাই"
                    save_data(data)
                    st.success("ঋণ সফলভাবে সেটেল করা হয়েছে!")
                    st.rerun()

def show_loan_collection():
    """Loan collection page"""
    st.title("💰 ঋণের টাকা বা কিস্তি আদায়")
    
    data = st.session_state.data
    
    # Show all active loans
    active_loans = {
        phone: m for phone, m in data["members"].items() 
        if m["loan_type"] != "নাই" and m["loan_principal"] > 0
    }
    
    if not active_loans:
        st.info("কোনো সক্রিয় ঋণ নেই।")
        return
    
    st.subheader("📋 সক্রিয় ঋণের তালিকা")
    
    for phone, member in active_loans.items():
        with st.expander(f"🧑 {member['name']} - {phone} - বাকি: ৳{member['loan_principal']:,.2f}"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**ঋণের পরিমাণ:** ৳{member['loan_principal']:,.2f}")
                st.write(f"**সুদের হার:** {member['loan_rate']}%")
                st.write(f"**মেয়াদ:** {member['loan_duration']} {member['loan_type']}")
            
            with col2:
                payment = st.number_input(
                    f"কিস্তির পরিমাণ ({member['name']})",
                    min_value=0.0,
                    step=100.0,
                    key=f"payment_{phone}"
                )
                
                if st.button(f"আদায় করুন", key=f"collect_{phone}"):
                    if payment > 0:
                        if payment >= member["loan_principal"]:
                            member["history"].append(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - ঋণ সম্পূর্ণ পরিশোধ: ৳{member['loan_principal']:,.2f}")
                            member["loan_principal"] = 0
                            member["loan_interest"] = 0
                            member["loan_type"] = "নাই"
                            st.success("ঋণ সম্পূর্ণ পরিশোধ করা হয়েছে!")
                        else:
                            member["loan_principal"] -= payment
                            member["history"].append(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - কিস্তি আদায়: ৳{payment:,.2f}")
                            st.success(f"কিস্তি আদায় করা হয়েছে! বাকি: ৳{member['loan_principal']:,.2f}")
                        
                        save_data(data)
                        st.rerun()
                    else:
                        st.error("সঠিক পরিমাণ দিন")

def show_member_statement():
    """Member statement page"""
    st.title("📄 সদস্য স্টেটমেন্ট (Statement)")
    
    data = st.session_state.data
    
    if not data["members"]:
        st.warning("কোনো সদস্য নেই।")
        return
    
    selected_phone = st.selectbox(
        "সদস্য নির্বাচন করুন",
        options=list(data["members"].keys()),
        format_func=lambda x: f"{data['members'][x]['name']} ({x})",
        key="statement_member"
    )
    
    if selected_phone:
        member = data["members"][selected_phone]
        
        # Member info
        st.subheader(f"👤 {member['name']}")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📱 মোবাইল", selected_phone)
        with col2:
            st.metric("💰 সঞ্চয়", f"৳{member['savings']:,.2f}")
        with col3:
            st.metric("💳 ঋণ", f"৳{member['loan_principal']:,.2f}")
        
        # Transaction history
        st.subheader("📜 লেনদেনের ইতিহাস")
        if member["history"]:
            df = pd.DataFrame({
                "তারিখ ও সময়": [h.split(" - ")[0] for h in member["history"]],
                "বিবরণ": [h.split(" - ")[1] if " - " in h else h for h in member["history"]]
            })
            st.dataframe(df, use_container_width=True)
            
            # Download option
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 স্টেটমেন্ট ডাউনলোড করুন (CSV)",
                data=csv,
                file_name=f"statement_{selected_phone}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info("কোনো লেনদেনের ইতিহাস নেই।")

# Main app
def main():
    # Authentication
    if not st.session_state.authenticated:
        st.title("🔐 সোমিটি ম্যানেজমেন্ট সিস্টেম")
        st.subheader("লগইন করুন")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            username = st.text_input("ইউজারনেম")
            password = st.text_input("পাসওয়ার্ড", type="password")
            
            if st.button("লগইন", type="primary", use_container_width=True):
                if authenticate(username, password):
                    st.session_state.authenticated = True
                    st.session_state.data = load_data()
                    st.rerun()
                else:
                    st.error("ভুল ইউজারনেম বা পাসওয়ার্ড!")
        
        return
    
    # Sidebar navigation
    st.sidebar.title("📋 মেনু")
    st.sidebar.write(f"👋 স্বাগতম, admin")
    
    # Navigation buttons
    pages = [
        "🏠 ড্যাশবোর্ড",
        "👥 সদস্য ব্যবস্থাপনা",
        "💰 সঞ্চয় ব্যবস্থাপনা",
        "💳 ঋণ ব্যবস্থাপনা",
        "💰 ঋণের টাকা বা কিস্তি আদায়",
        "📄 সদস্য স্টেটমেন্ট (Statement)"
    ]
    
    for page in pages:
        if st.sidebar.button(page, use_container_width=True):
            st.session_state.current_page = page
            st.rerun()
    
    st.sidebar.divider()
    if st.sidebar.button("🚪 লগআউট", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()
    
    # Page routing
    page = st.session_state.current_page
    
    if page == "🏠 ড্যাশবোর্ড":
        show_dashboard()
    elif page == "👥 সদস্য ব্যবস্থাপনা":
        show_members()
    elif page == "💰 সঞ্চয় ব্যবস্থাপনা":
        show_savings()
    elif page == "💳 ঋণ ব্যবস্থাপনা":
        show_loan_management()
    elif page == "💰 ঋণের টাকা বা কিস্তি আদায়":
        show_loan_collection()
    elif page == "📄 সদস্য স্টেটমেন্ট (Statement)":
        show_member_statement()

if __name__ == "__main__":
    main()
