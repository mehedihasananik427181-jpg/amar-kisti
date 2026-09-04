import json
import os
import streamlit as st
import pandas as pd

# ডাটাবেজ ফাইলের নাম
DB_FILE = "database.json"

# এডমিন ইউজারনেম ও পাসওয়ার্ড
ADMIN_USER = "admin"
ADMIN_PASS = "somity2026"

def load_data():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    return {
        "01711223344": {"name": "মেহেদী হাসান", "savings": 5000.0, "loan": 0.0},
        "01911223344": {"name": "আনিক আহমেদ", "savings": 3500.0, "loan": 1000.0},
    }

def save_data(data):
    with open(DB_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

# ডাটা লোড করা
members = load_data()

# ওয়েবসাইটের মূল সেটিংস ও থিম
st.set_page_config(page_title="Amar Kisti - Premium Dashboard", page_icon="🏦", layout="wide")

# --- প্রিমিয়াম কাস্টম কালার ও বাটন স্টাইলিং (CSS Injection) ---
st.markdown("""
    <style>
    /* মেইন ব্যাকগ্রাউন্ড এবং টেক্সট কালার */
    .stApp {
        background-color: #F8FAFC;
    }
    /* বড় মেট্রিক কার্ডের প্রিমিয়াম ডিজাইন */
    [data-testid="stMetricValue"] {
        font-size: 28px;
        font-weight: bold;
        color: #1E3A8A;
    }
    /* সাইডবার মেনুর কালার */
    .css-17eq0hr {
        background-color: #1E3A8A !important;
    }
    /* জেনারাল বাটন স্টাইলিং */
    div.stButton > button:first-child {
        background-color: #1E3A8A;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 8px 16px;
        font-weight: bold;
    }
    div.stButton > button:first-child:hover {
        background-color: #3B82F6;
        color: white;
    }
    /* ডাউনলোড বাটনের প্রিমিয়াম গোল্ডেন লুক */
    .stDownloadButton > button {
        background-color: #D97706 !important;
        color: white !important;
        border-radius: 8px !important;
        padding: 10px 20px !important;
        font-weight: bold !important;
    }
    .stDownloadButton > button:hover {
        background-color: #B45309 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# লগইন অবস্থা মনে রাখার সেশন
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# --- ১. প্রিমিয়াম লগইন স্ক্রিন ---
if not st.session_state["logged_in"]:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
        <div style='background-color: white; padding: 40px; border-radius: 15px; box-shadow: 0px 10px 25px rgba(0,0,0,0.05); max-width: 500px; margin: 0 auto;'>
            <h1 style='text-align: center; color: #1E3A8A; margin-bottom: 5px;'>🏦 আমার কিস্তি</h1>
            <p style='text-align: center; color: #6B7280; font-size: 14px;'>Micro-Finance & Somity Management System</p>
            <hr style='border-top: 1px solid #E5E7EB; margin-bottom: 25px;'>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("👤 ইউজারনেম (Username)")
            password = st.text_input("🔑 পাসওয়ার্ড (Password)", type="password")
            login_btn = st.form_submit_button("🔓 ড্যাশবোর্ডে প্রবেশ করুন")

            if login_btn:
                if username == ADMIN_USER and password == ADMIN_PASS:
                    st.session_state["logged_in"] = True
                    st.success("✅ লগইন সফল হয়েছে! ড্যাশবোর্ডে প্রবেশ করা হচ্ছে...")
                    st.rerun()
                else:
                    st.error("❌ ভুল ইউজারনেম অথবা পাসওয়ার্ড! আবার চেষ্টা করুন।")
    st.stop()

# --- ২. মূল ড্যাশবোর্ড স্ক্রিন (লগইন সফল হওয়ার পর) ---
# প্রিমিয়াম ব্র্যান্ডেড ব্যানার ও লোগো
st.markdown("""
    <div style='background-color: #1E3A8A; padding: 25px; border-radius: 12px; box-shadow: 0 4px 15px rgba(30,58,138,0.2); text-align: center; margin-bottom: 25px;'>
        <h1 style='color: #FBBF24; margin: 0; font-size: 32px; font-weight: 800;'>🏦 আমার কিস্তি (Amar Kisti)</h1>
        <p style='color: #E2E8F0; margin: 5px 0 0 0; font-size: 15px; letter-spacing: 1px;'>ক্ষুদ্র সঞ্চয় সমিতি ও ডিপিএস ট্র্যাকার ডিজিটাল ড্যাশবোর্ড v5.5</p>
    </div>
""", unsafe_allow_html=True)

# বাম পাশের সাইডবার মেনু
st.sidebar.markdown("<h2 style='color: #1E3A8A; text-align: center;'>🧭 কন্ট্রোল প্যানেল</h2>", unsafe_allow_html=True)
menu = st.sidebar.radio("কোন কাজ করতে চান?", [
    "📊 ড্যাশবোর্ড ও সদস্য তালিকা", 
    "👤 নতুন সদস্য যুক্ত করুন", 
    "💰 কিস্তি বা টাকা জমা নিন",
    "📉 ঋণ বা লোন বিতরণ (Loan)",
    "📈 ঋণের টাকা বা কিস্তি আদায়"
])

# সাইডবারে প্রিমিয়াম লগআউট বাটন
st.sidebar.markdown("<br><hr>", unsafe_allow_html=True)
if st.sidebar.button("🔒 নিরাপদ লগআউট"):
    st.session_state["logged_in"] = False
    st.rerun()

# --- মেনু ১: ড্যাশবোর্ড ও সদস্য তালিকা ---
if menu == "📊 ড্যাশবোর্ড ও সদস্য তালিকা":
    st.markdown("<h3 style='color: #1E3A8A;'>📋 সমিতির বর্তমান অবস্থা ও সদস্য তালিকা</h3>", unsafe_allow_html=True)

    total_members = len(members)
    total_savings = sum(float(m["savings"]) for m in members.values())
    total_loans = sum(float(m["loan"]) for m in members.values())

    # স্টাইলিশ মেট্রিক কার্ড সেকশন
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"<div style='background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.02); border-left: 5px solid #3B82F6;'>👥 <b>মোট সদস্য</b><br><span style='font-size:24px; color:#1E3A8A; font-weight:bold;'>{total_members} জন</span></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div style='background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.02); border-left: 5px solid #10B981;'>💰 <b>মোট সঞ্চয় ফান্ড</b><br><span style='font-size:24px; color:#10B981; font-weight:bold;'>{total_savings:,} টাকা</span></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div style='background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.02); border-left: 5px solid #EF4444;'>📉 <b>মোট বিতরণকৃত ঋণ</b><br><span style='font-size:24px; color:#EF4444; font-weight:bold;'>{total_loans:,} টাকা</span></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    st.write("### 🗂️ সকল সদস্যের বিস্তারিত ডাটা টেবিল")
    table_data = []
    for phone, info in members.items():
        table_data.append({
            "ফোন নম্বর": phone,
            "সদস্যের নাম": info["name"],
            "মোট সঞ্চয় (টাকা)": info["savings"],
            "চলতি ঋণ (টাকা)": info["loan"]
        })
    
    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.write("### 📥 এক্সপোর্ট ও প্রিন্ট সেন্টার")
    csv_data = df.to_csv(index=False).encode('utf-8-sig')
    
    st.download_button(
        label="📥 এক্সেল বা প্রিন্ট ফাইল ডাউনলোড করুন (Excel/CSV Report)",
        data=csv_data,
        file_name="Amar_Kisti_Premium_Report.csv",
        mime="text/csv",
        key='download-csv'
    )

# --- মেনু ২: নতুন সদস্য যুক্ত করুন ---
elif menu == "👤 নতুন সদস্য যুক্ত করুন":
    st.markdown("<h3 style='color: #1E3A8A;'>➕ নতুন সদস্যের প্রোফাইল তৈরি করুন</h3>", unsafe_allow_html=True)
    with st.form("add_member_form"):
        new_phone = st.text_input("📱 সদস্যের মোবাইল নম্বর দিন")
        new_name = st.text_input("✍️ সদস্যের পুরো নাম লিখুন")
        new_savings = st.number_input("💵 প্রাথমিক সঞ্চয় জমা (টাকা)", min_value=0.0, step=100.0)
        submit_btn = st.form_submit_button("💾 ডাটাবেজে স্থায়ীভাবে সেভ করুন")
        
        if submit_btn:
            if not new_phone or not new_name:
                st.error("❌ দয়া করে নাম এবং ফোন নম্বর দুটোই সঠিকভাবে লিখুন!")
            elif new_phone in members:
                st.warning("⚠️ এই নম্বরে অলরেডি একজন সদস্য নিবন্ধিত আছেন!")
            else:
                members[new_phone] = {"name": new_name, "savings": new_savings, "loan": 0.0}
                save_data(members)
                st.success(f"🎉 সদস্য '{new_name}' সফলভাবে যুক্ত এবং ডাটাবেজে সেভ হয়েছেন!")

# --- মেনু ৩: কিস্তি বা টাকা জমা নিন ---
elif menu == "💰 কিস্তি বা টাকা জমা নিন":
    st.markdown("<h3 style='color: #1E3A8A;'>📥 সদস্যের কিস্তি বা সঞ্চয়ের টাকা জমা নিন</h3>", unsafe_allow_html=True)
    search_phone = st.selectbox("📞 সদস্যের ফোন নম্বর নির্বাচন করুন", list(members.keys()))
    
    if search_phone:
        member_info = members[search_phone]
        st.info(f"👤 নির্বাচিত সদস্য: **{member_info['name']}** | 💰 বর্তমান মোট সঞ্চয়: **{member_info['savings']} টাকা**")
        amount_to_add = st.number_input("💵 জমার পরিমাণ (টাকা)", min_value=10.0, step=50.0)
        deposit_btn = st.button("✅ সফলভাবে জমা করুন")
        
        if deposit_btn:
            members[search_phone]["savings"] += amount_to_add
            save_data(members)
            st.success(f"💸 সফলভাবে {amount_to_add} টাকা জমা হয়েছে! বর্তমান মোট সঞ্চয়: {members[search_phone]['savings']} টাকা।")

# --- মেনু ৪: ঋণ বা লোন বিতরণ ---
elif menu == "📉 ঋণ বা লোন বিতরণ (Loan)":
    st.markdown("<h3 style='color: #1E3A8A;'>💸 সদস্যকে নতুন ঋণ বা লোন প্রদান করুন</h3>", unsafe_allow_html=True)
    loan_phone = st.selectbox("📞 লোন গ্রহীতার ফোন নম্বর নির্বাচন করুন", list(members.keys()))
    
    if loan_phone:
        m_info = members[loan_phone]
        st.warning(f"👤 সদস্য: **{m_info['name']}** | 📉 বর্তমান চলতি ঋণ: **{m_info['loan']} টাকা**")
        loan_amount = st.number_input("💵 নতুন ঋণের পরিমাণ (টাকা)", min_value=100.0, step=500.0)
        interest_rate = st.slider("📊 সুদের হার নির্ধারণ করুন (%)", 0, 20, 10)
        
        total_interest = loan_amount * (interest_rate / 100)
        total_payable = loan_amount + total_interest
        
        st.info(f"📈 মোট সুদ আসবে: **{total_interest} টাকা** | 🗓️ সদস্যকে মোট ফেরত দিতে হবে: **{total_payable} টাকা**")
        give_loan_btn = st.button("🚀 লোন অনুমোদন ও প্রদান করুন")
        
        if give_loan_btn:
            members[loan_phone]["loan"] = float(members[loan_phone]["loan"]) + total_payable
            save_data(members)
