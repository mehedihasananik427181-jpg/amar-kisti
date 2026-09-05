import json
import os
import streamlit as st
import pandas as pd
from datetime import datetime

# ডেটাবেজ ফাইলের নাম
DB_FILE = "database.json"

# এডমিন ইউজারনেম ও পাসওয়ার্ড
ADMIN_USER = "admin"
ADMIN_PASS = "somity2026"

def load_data():
    """ডেটাবেজ ফাইল থেকে নিরাপদ উপায়ে ডাটা লোড করার চূড়ান্ত ফাংশন"""
    try:
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "r", encoding="utf-8") as file:
                data = json.load(file)
                # ডাটা যদি ডিকশনারি টাইপ হয়, তবেই কেবল হিস্ট্রি লুপ চলবে
                if isinstance(data, dict):
                    return data
        return {"members": {}}
    except Exception as e:
        return {"members": {}}

def save_data(data):
    """ডাটাবেজে তথ্য সেভ করার ফাংশন"""
    try:
        with open(DB_FILE, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"ডাটা সেভ করতে সমস্যা হয়েছে: {e}")

# ডাটা লোড করা
data = load_data()
if "members" not in data:
    data["members"] = {}

# সেশন স্টেট চেক (লগইন ট্র্যাকিং)
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# লগইন পেজ ডিজাইন
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🏦 আমার কিস্তি</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-style: italic;'>Micro-Finance & Somity Management System</p>", unsafe_allow_html=True)
    st.write("---")
    
    with st.form("login_form"):
        username = st.text_input("👤 ইউজারনেম (Username)", value="admin")
        password = st.text_input("🔑 পাসওয়ার্ড (Password)", type="password")
        submit_button = st.form_submit_button("📥 ড্যাশবোর্ডে প্রবেশ করুন")
        
        if submit_button:
            if username == ADMIN_USER and password == ADMIN_PASS:
                st.session_state.logged_in = True
                st.success("🎉 লগইন সফল হয়েছে!")
                st.rerun()
            else:
                st.error("❌ ভুল ইউজারনেম অথবা পাসওয়ার্ড!")

# লগইন সফল হলে মূল অ্যাপ চালু হবে
else:
    st.sidebar.title("🎛️ কন্ট্রোল প্যানেল")
    
    # লগআউট বাটন
    if st.sidebar.button("🔒 নিরাপদ লগআউট", type="primary"):
        st.session_state.logged_in = False
        st.rerun()
        
    choice = st.sidebar.radio("কোন কাজ করতে চান?", [
        "ড্যাশবোর্ড ও সদস্য তালিকা",
        "নতুন সদস্য যুক্ত করুন",
        "কিস্তি বা টাকা জমা নিন",
        "ঋণ বা লোন বিতরণ (Loan)",
        "ঋণের টাকা বা কিস্তি আদায়",
        "সদস্য স্টেটমেন্ট (Statement)"
    ])

    st.markdown(f"<h1 style='text-align: center; color: #1E3A8A;'>🏦 আমার কিস্তি (Amar Kisti)</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; font-style: italic;'>ক্ষুদ্র সঞ্চয় সমিতি ও ডিপিএস ট্র্যাকার ডিজিটাল ড্যাশবোর্ড v6.0</p>", unsafe_allow_html=True)
    st.write("---")

    # ১. ড্যাশবোর্ড ও সদস্য তালিকা
    if choice == "ড্যাশবোর্ড ও সদস্য তালিকা":
        st.subheader("📊 ড্যাশবোর্ড ও সদস্য তালিকা")
        if not data["members"]:
            st.info("বর্তমানে কোনো সদস্য নিবন্ধিত নেই।")
        else:
            for phone, info in data["members"].items():
                st.info(f"👤 **নাম:** {info['name']} | 📱 **মোবাইল:** {phone} | 💰 **মোট সঞ্চয়:** {info.get('savings', 0.0)} টাকা | 📉 **চলতি ঋণ:** {info.get('loan', 0.0)} টাকা")

    # ২. নতুন সদস্য যুক্ত করুন
    elif choice == "নতুন সদস্য যুক্ত করুন":
        st.subheader("➕ নতুন সদস্যের প্রোফাইল তৈরি করুন")
        phone = st.text_input("📱 সদস্যের মোবাইল নম্বর দিন")
        name = st.text_input("✍️ সদস্যের পুরো নাম লিখুন")
        initial_savings = st.number_input("💵 প্রাথমিক সঞ্চয় জমা (টাকা)", min_value=0.0, step=10.0)
        
        if st.button("💾 ডেটাবেজে স্থায়ীভাবে সেভ করুন"):
            if phone and name:
                if phone in data["members"]:
                    st.error("এই মোবাইল নম্বরে ইতিমধ্যে একজন সদস্য আছেন!")
                else:
                    data["members"][phone] = {
                        "name": name,
                        "savings": initial_savings,
                        "loan": 0.0,
                        "history": [f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - হিসাব खोला হয়েছে প্রাথমিক সঞ্চয় {initial_savings} টাকা দিয়ে।"]
                    }
                    save_data(data)
                    st.success(f"🎉 সফলভাবে {name}-এর প্রোফাইল তৈরি হয়েছে!")
            else:
                st.warning("দয়া করে নাম এবং মোবাইল নম্বর দিন।")

    # ৩. কিস্তি বা টাকা জমা নিন
    elif choice == "কিস্তি বা টাকা জমা নিন":
        st.subheader("💰 সদস্যের কিস্তি বা সঞ্চয়ের টাকা জমা নিন")
        if not data["members"]:
            st.warning("কোনো সদস্য নেই। আগে সদস্য যুক্ত করুন।")
        else:
            member_list = {f"{info['name']} ({phone})": phone for phone, info in data["members"].items()}
            selected_member = st.selectbox("📞 সদস্যের ফোন নম্বর নির্বাচন করুন", list(member_list.keys()))
            phone = member_list[selected_member]
            
            info = data["members"][phone]
            st.info(f"👤 নির্বাচিত সদস্য: {info['name']} | 💰 বর্তমান মোট সঞ্চয়: {info['savings']} টাকা")
            
            amount = st.number_input("💵 জমার পরিমাণ (টাকা)", min_value=0.0, step=10.0)
            if st.button("✔️ সফলভাবে জমা করুন"):
                if amount > 0:
                    data["members"][phone]["savings"] += amount
                    data["members"][phone]["history"].append(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - সঞ্চয় জমা: +{amount} টাকা।")
                    save_data(data)
                    st.success(f"💸 সফলভাবে {amount} টাকা সঞ্চয় জমা করা হয়েছে!")
                    st.rerun()

    # ৪. ঋণ বা লোন বিতরণ (Loan)
    elif choice == "ঋণ বা লোন বিতরণ (Loan)":
        st.subheader("💸 সদস্যকে নতুন ঋণ বা লোন প্রদান করুন")
        if not data["members"]:
            st.warning("কোনো সদস্য নেই।")
        else:
            member_list = {f"{info['name']} ({phone})": phone for phone, info in data["members"].items()}
            selected_member = st.selectbox("📞 লোন গ্রহীতার ফোন নম্বর নির্বাচন করুন", list(member_list.keys()))
            phone = member_list[selected_member]
            
            info = data["members"][phone]
            st.info(f"👤 সদস্য: {info['name']} | 📉 বর্তমান চলতি ঋণ: {info.get('loan', 0.0)} টাকা")
            
            loan_amount = st.number_input("💵 নতুন ঋণের পরিমাণ (টাকা)", min_value=0.0, step=10.0)
            interest_rate = st.slider("📊 সুদের হার নির্ধারণ করুন (%)", 0, 50, 10)
            
            total_interest = (loan_amount * interest_rate) / 100
            total_payable = loan_amount + total_interest
            
            st.warning(f"📊 মোট সুদ আসবে: {total_interest} টাকা | 📑 সদস্যকে মোট ফেরত দিতে হবে: {total_payable} টাকা")
            
            if st.button("🚀 ঋণ বা লোন অনুমোদন করুন"):
                if loan_amount > 0:
                    data["members"][phone]["loan"] = data["members"][phone].get("loan", 0.0) + total_payable
                    data["members"][phone]["history"].append(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - ঋণ গ্রহণ (সুদসহ): +{total_payable} টাকা ({interest_rate}% সুদ)।")
                    save_data(data)
                    st.success(f"✅ সফলভাবে {loan_amount} টাকা ঋণ বিতরণ করা হয়েছে (মোট প্রদেয়: {total_payable})")
                    st.rerun()

    # ৫. ঋণের টাকা বা কিস্তি আদায় (এটি আগে ফাঁকা ছিল, এখন যুক্ত করা হয়েছে)
    elif choice == "ঋণের টাকা বা কিস্তি আদায়":
        st.subheader("📉 ঋণের টাকা বা কিস্তি আদায় করুন")
        if not data["members"]:
            st.warning("কোনো সদস্য নেই।")
        else:
            member_list = {f"{info['name']} ({phone})": phone for phone, info in data["members"].items()}
            selected_member = st.selectbox("📞 সদস্যের ফোন নম্বর নির্বাচন করুন", list(member_list.keys()))
            phone = member_list[selected_member]
            
            info = data["members"][phone]
            current_loan = info.get("loan", 0.0)
            st.info(f"👤 সদস্য: {info['name']} | 📉 বর্তমান মোট ঋণ বা দেনা: {current_loan} টাকা")
            
            repay_amount = st.number_input("💵 পরিশোধের পরিমাণ (টাকা)", min_value=0.0, max_value=float(current_loan) if current_loan > 0 else 0.0, step=10.0)
            
            if st.button("✔️ ঋণ/কিস্তি আদায় নিশ্চিত করুন"):
                if repay_amount > 0:
                    data["members"][phone]["loan"] -= repay_amount
                    data["members"][phone]["history"].append(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - ঋণ/কিস্তি পরিশোধ: -{repay_amount} টাকা।")
                    save_data(data)
                    st.success(f"🎉 সফলভাবে {repay_amount} টাকা কিস্তি বা ঋণ আদায় করা হয়েছে!")
                    st.rerun()
                else:
                    st.warning("পরিশোধের পরিমাণ ০ এর বেশি হতে হবে অথবা সদস্যের কোনো বকেয়া লোন নেই।")

    # ৬. সদস্য স্টেটমেন্ট (Statement) (এটিও আগে ফাঁকা ছিল, এখন যুক্ত করা হয়েছে)
    elif choice == "সদস্য স্টেটমেন্ট (Statement)":
        st.subheader("📋 সদস্যের সম্পূর্ণ লেনদেন স্টেটমেন্ট")
        if not data["members"]:
            st.warning("কোনো সদস্য নেই।")
        else:
            member_list = {f"{info['name']} ({phone})": phone for phone, info in data["members"].items()}
            selected_member = st.selectbox("📞 স্টেটমেন্ট দেখতে সদস্য নির্বাচন করুন", list(member_list.keys()))
            phone = member_list[selected_member]
            
            info = data["members"][phone]
            st.markdown(f"### 👤 নাম: {info['name']}")
            st.write(f"📱 **মোবাইল:** {phone}")
            st.write(f"💰 **বর্তমান মোট জমানো সঞ্চয়:** {info.get('savings', 0.0)} টাকা")
            st.write(f"📉 **বর্তমান অবশিষ্ট লোন/দেনা:** {info.get('loan', 0.0)} টাকা")
            st.write("---")
            st.write("📜 **লেনদেনের ইতিহাস (History):**")
            
            history = info.get("history", [])
            if not history:
