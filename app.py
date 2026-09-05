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
    try:
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "r", encoding="utf-8") as file:
                data = json.load(file)
                if isinstance(data, dict):
                    return data
        return {"members": {}}
    except Exception as e:
        return {"members": {}}

def save_data(data):
    try:
        with open(DB_FILE, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"ডাটা সেভ করতে সমস্যা হয়েছে: {e}")

# ডাটা লোড করা
data = load_data()
if "members" not in data:
    data["members"] = {}

# সেশন স্টেট চেক
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# লগইন পেজ ডিজাইন
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🏦 আমার কিস্তি</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-style: italic;'>Micro-Finance & Somity Management System v7.5</p>", unsafe_allow_html=True)
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

# লগইন সফল হলে মূল অ্যাপ
else:
    st.sidebar.title("🎛️ কন্ট্রোল প্যানেল")
    
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
    st.write("---")

    # ১. ড্যাশবোর্ড ও সদস্য তালিকা
    if choice == "ড্যাশবোর্ড ও সদস্য তালিকা":
        st.subheader("📊 ড্যাশবোর্ড ও সদস্য তালিকা")
        if not data["members"]:
            st.info("বর্তমানে কোনো সদস্য নিবন্ধিত নেই।")
        else:
            for phone, info in data["members"].items():
                loan_type = info.get("loan_type", "নাই")
                total_loan = round(info.get("loan_principal", 0.0) + info.get("loan_interest", 0.0), 2)
                st.info(f"👤 **নাম:** {info['name']} | 📱 **মোবাইল:** {phone} | 💰 **মোট সঞ্চয়:** {info.get('savings', 0.0)} টাকা | 📉 **অবশিষ্ট ঋণ:** {total_loan} টাকা ({loan_type})")

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
                        "loan_principal": 0.0,
                        "loan_interest": 0.0,
                        "loan_type": "নাই",
                        "loan_date": "",
                        "history": [f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - হিসাব খোলা হয়েছে প্রাথমিক সঞ্চয় {initial_savings} টাকা দিয়ে।"]
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
            current_total_loan = info.get("loan_principal", 0.0) + info.get("loan_interest", 0.0)
            st.info(f"👤 সদস্য: {info['name']} | 📉 বর্তমান বকেয়া লোন: {current_total_loan} টাকা")
            
            if current_total_loan > 0:
                st.error("⚠️ এই সদস্যের পূর্বের লোন বকেয়া আছে। নতুন লোন দেওয়া যাবে না।")
            else:
                loan_amount = st.number_input("💵 ঋণের আসল পরিমাণ (টাকা)", min_value=0.0, step=100.0)
                interest_rate = st.slider("📊 সুদের হার নির্ধারণ করুন (%)", 1, 50, 10)
                loan_type = st.selectbox("📅 কিস্তির ধরন নির্বাচন করুন", ["দিনের হিসাবে", "সাপ্তাহিক হিসাবে", "মাসিক হিসাবে"])
                duration = st.number_input("⏱️ মেয়াদ বা কিস্তির সংখ্যা দিন", min_value=1, step=1, value=10)
                
                # প্রারম্ভিক সরল/ক্রমহ্রাসমান মিশ্র সুদ হিসাব
                factor = duration / 12 if loan_type == "মাসিক হিসাবে" else duration / 52 if loan_type == "সাপ্তাহিক হিসাবে" else duration / 365
                total_interest = loan_amount * (interest_rate / 100) * factor
                
                st.warning(f"📉 আসল: {loan_amount} টাকা | আনুমানিক মোট সুদ: {round(total_interest, 2)} টাকা")
                
                if st.button("🚀 ঋণ বা লোন অনুমোদন করুন"):
                    if loan_amount > 0:
                        data["members"][phone]["loan_principal"] = loan_amount
                        data["members"][phone]["loan_interest"] = total_interest
                        data["members"][phone]["loan_type"] = loan_type
                        data["members"][phone]["loan_duration"] = duration
                        data["members"][phone]["loan_rate"] = interest_rate
                        data["members"][phone]["loan_date"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        
                        data["members"][phone]["history"].append(
                            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - ঋণ গ্রহণ: আসল {loan_amount} টাকা, সুদ {round(total_interest, 2)} টাকা ({loan_type}, মেয়াদ: {duration})"
                        )
                        save_data(data)
                        st.success(f"✅ সফলভাবে লোন অনুমোদন করা হয়েছে!")
                        st.rerun()

    # ৫. ঋণের টাকা বা কিস্তি আদায়
    elif choice == "ঋণের টাকা বা কিস্তি আদায়":
        st.subheader("📉 ঋণের টাকা বা কিস্তি আদায় করুন")
        if not data["members"]:
            st.warning("কোনো সদস্য নেই।")
        else:
            member_list = {f"{info['name']} ({phone})": phone for phone, info in data["members"].items()}
            selected_member = st.selectbox("📞 সদস্যের ফোন নম্বর নির্বাচন করুন", list(member_list.keys()))
            phone = member_list[selected_member]
            
            info = data["members"][phone]
            principal = info.get("loan_principal", 0.0)
            interest = info.get("loan_interest", 0.0)
            total_due = principal + interest
            
            if total_due <= 0:
                st.info("ℹ️ এই সদস্যের কোনো বকেয়া লোন নেই।")
            else:
                st.info(f"👤 সদস্য: {info['name']} | 💵 বকেয়া আসল: {round(principal, 2)} টাকা | 📊 বকেয়া সুদ: {round(interest, 2)} টাকা")
                st.error(f"💰 মোট প্রদেয় বকেয়া: {round(total_due, 2)} টাকা")
                
                st.markdown("---")
                repay_amount = st.number_input("💵 কিস্তি পরিশোধের পরিমাণ (টাকা)", min_value=0.0, max_value=float(total_due), step=10.0)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("✔️ সাধারণ কিস্তি জমা"):
                        if repay_amount > 0:
                            # সাধারণ ক্রমহ্রাসমান পেমেন্ট প্রসেস
                            if repay_amount >= interest:
