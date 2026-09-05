import json
import os
import streamlit as st
from datetime import datetime

# আপনার সঠিক ডেটাবেজ ফাইলের নাম
DB_FILE = "database.json"
ADMIN_USER = "admin"
ADMIN_PASS = "somity2026"

def load_data():
    """আপনার মেহেদী হাসান অনিকসহ সকল পুরোনো ডাটা নিরাপদ উপায়ে লোড করার ফাংশন"""
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as file:
                data = json.load(file)
                if isinstance(data, dict) and "members" in data:
                    return data
        except:
            pass
    # ফাইল না থাকলে বা এরর হলে স্বয়ংক্রিয়ভাবে স্ট্রাকচার তৈরি করবে যাতে KeyError না আসে
    return {"members": {}}

def save_data(data):
    try:
        with open(DB_FILE, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
    except:
        st.error("🎰 ডাটা সেভ করতে সমস্যা হয়েছে!")

data = load_data()

# সেশন ট্র্যাকিং
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# লগইন স্ক্রিন প্রসেস
if not st.session_state.logged_in:
    st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>🏦 সমিতি ম্যানেজমেন্ট সিস্টেম</h2>", unsafe_allow_html=True)
    st.write("---")
    with st.form("login_form"):
        username = st.text_input("👤 ইউজারনেম", value="admin")
        password = st.text_input("🔑 পাসওয়ার্ড", type="password")
        if st.form_submit_button("📥 প্রবেশ করুন"):
            if username == ADMIN_USER and password == ADMIN_PASS:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("❌ ভুল পাসওয়ার্ড!")

# মূল অ্যাপ্লিকেশন উইন্ডো (আপনার নতুন সুন্দর ডিজাইনটি অক্ষত রাখা হয়েছে)
else:
    st.sidebar.title("📑 মেনু")
    st.sidebar.write(f"🧑‍💼 স্বাগতম, {ADMIN_USER}")
    st.sidebar.write("---")
    
    # নতুন ডিজাইনের ৬টি বাটন মেনু
    choice = st.sidebar.radio("কোন কাজ করতে চান?", [
        "📊 ড্যাশবোর্ড",
        "👥 সদস্য ব্যবস্থাপনা",
        "💰 সঞ্চয় ব্যবস্থাপনা",
        "💳 ঋণ ব্যবস্থাপনা",
        "📥 ঋণের টাকা বা কিস্তি আদায়",
        "📋 সদস্য স্টেটমেন্ট (Statement)"
    ])
    
    st.sidebar.write("---")
    if st.sidebar.button("■ লগআউট", type="primary"):
        st.session_state.logged_in = False
        st.rerun()

    # পৃষ্ঠা ১: ড্যাশবোর্ড
    if choice == "📊 ড্যাশবোর্ড":
        st.markdown("<h2 style='color: #1E3A8A;'>🏦 সমিতি ম্যানেজমেন্ট সিস্টেম - ড্যাশবোর্ড</h2>", unsafe_allow_html=True)
        st.write("---")
        total_members = len(data["members"])
        st.metric("👥 মোট নিবন্ধিত সদস্য সংখ্যা", total_members)
        
        if total_members == 0:
            st.info("বর্তমানে কোনো সদস্য নিবন্ধিত নেই।")
        else:
            st.write("### 📋 একনজরে সদস্যদের সারসংক্ষেপ:")
            for phone, info in data["members"].items():
                total_loan = round(info.get("loan_principal", 0.0) + info.get("loan_interest", 0.0), 2)
                st.info(f"👤 **নাম:** {info['name']} | 📱 **মোবাইল:** {phone} | 💰 **মোট সঞ্চয়:** {info.get('savings', 0.0)} টাকা | 📉 **চলতি ঋণ:** {total_loan} টাকা")

    # পৃষ্ঠা ২: সদস্য ব্যবস্থাপনা
    elif choice == "👥 সদস্য ব্যবস্থাপনা":
        st.markdown("<h2 style='color: #1E3A8A;'>👥 সদস্য ব্যবস্থাপনা</h2>", unsafe_allow_html=True)
        st.write("---")
        with st.expander("➕ নতুন সদস্য যোগ করুন", expanded=True):
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
                            "loan_rate": 10,
                            "loan_duration": 10,
                            "history": [f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - হিসাব খোলা হয়েছে প্রাথমিক সঞ্চয় {initial_savings} টাকা দিয়ে।"]
                        }
                        save_data(data)
                        st.success(f"🎉 সফলভাবে {name}-এর প্রোফাইল তৈরি হয়েছে!")
                        st.rerun()
                else:
                    st.warning("দয়া করে নাম এবং মোবাইল নম্বর দিন।")

    # পৃষ্ঠা ৩: সঞ্চয় ব্যবস্থাপনা
    elif choice == "💰 সঞ্চয় ব্যবস্থাপনা":
        st.markdown("<h2 style='color: #1E3A8A;'>💰 সঞ্চয় ব্যবস্থাপনা</h2>", unsafe_allow_html=True)
        st.write("---")
        if not data["members"]:
            st.warning("কোনো সদস্য নেই।")
        else:
            member_list = {f"{info['name']} ({phone})": phone for phone, info in data["members"].items()}
            selected_member = st.selectbox("📞 সদস্যের ফোন নম্বর নির্বাচন করুন", list(member_list.keys()))
            phone = member_list[selected_member]
            
            st.info(f"👤 নির্বাচিত সদস্য: {data['members'][phone]['name']} | 💰 বর্তমান সঞ্চয়: {data['members'][phone]['savings']} টাকা")
            amount = st.number_input("💵 সঞ্চয় জমার পরিমাণ (টাকা)", min_value=0.0, step=10.0)
            if st.button("✔️ সফলভাবে সঞ্চয় জমা করুন"):
                if amount > 0:
                    data["members"][phone]["savings"] += amount
                    data["members"][phone]["history"].append(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - সঞ্চয় জমা: +{amount} টাকা।")
                    save_data(data)
                    st.success("💸 সফলভাবে সঞ্চয় জমা করা হয়েছে!")
                    st.rerun()

    # পৃষ্ঠা ৪: ঋণ ব্যবস্থাপনা
    elif choice == "💳 ঋণ ব্যবস্থাপনা":
        st.markdown("<h2 style='color: #1E3A8A;'>💳 ঋণ ব্যবস্থাপনা</h2>", unsafe_allow_html=True)
        st.write("---")
        if not data["members"]:
            st.warning("কোনো সদস্য নেই।")
        else:
            member_list = {f"{info['name']} ({phone})": phone for phone, info in data["members"].items()}
            selected_member = st.selectbox("📞 লোন গ্রহীতার ফোন নম্বর নির্বাচন করুন", list(member_list.keys()))
            phone = member_list[selected_member]
            info = data["members"][phone]
            current_total_loan = info.get("loan_principal", 0.0) + info.get("loan_interest", 0.0)
            
            if current_total_loan > 0:
                st.error("⚠️ এই সদস্যের পূর্বের লোন বকেয়া আছে। নতুন লোন দেওয়া যাবে না।")
            else:
                loan_amount = st.number_input("💵 ঋণের আসল পরিমাণ (টাকা)", min_value=0.0, step=100.0)
                interest_rate = st.slider("📊 সুদের হার নির্ধারণ করুন (%)", 1, 50, 10)
                loan_type = st.selectbox("📅 কিস্তির ধরন নির্বাচন করুন", ["দিনের হিসাবে", "সাপ্তাহিক হিসাবে", "মাসিক হিসাবে"])
                duration = st.number_input("⏱️ মেয়াদ বা কিস্তির সংখ্যা দিন", min_value=1, step=1, value=10)
                
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
                        data["members"][phone]["history"].append(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - ঋণ গ্রহণ: আসল {loan_amount} টাকা, সুদ {round(total_interest, 2)} টাকা ({loan_type})")
                        save_data(data)
                        st.success(f"✅ সফলভাবে লোন অনুমোদন করা হয়েছে!")
                        st.rerun()

    # পৃষ্ঠা ৫: ঋণের টাকা বা কিস্তি আদায়
    elif choice == "📥 ঋণের টাকা বা কিস্তি আদায়":
        st.markdown("<h2 style='color: #1E3A8A;'>📥 ঋণের টাকা বা কিস্তি আদায় করুন</h2>", unsafe_allow_html=True)
        st.write("---")
        if not data["members"]:
            st.warning("কোনো সদস্য নেই।")
        else:
            member_list = {f"{info['name']} ({phone})": phone for phone, info in data["members"].items()}
            selected_member = st.selectbox("📞 সদস্য নির্বাচন করুন", list(member_list.keys()))
            phone = member_list[selected_member]
            info = data["members"][phone]
            principal = info.get("loan_principal", 0.0)
            interest = info.get("loan_interest", 0.0)
            total_due = principal + interest
            
            st.info(f"👤 সদস্য: {info['name']} | 💵 বকেয়া আসল: {round(principal, 2)} টাকা | 📊 বকেয়া সুদ: {round(interest, 2)} টাকা")
            repay_amount = st.number_input("💵 কিস্তি পরিশোধের পরিমাণ (টাকা)", min_value=0.0, max_value=float(total_due) if total_due > 0 else 0.0, step=10.0)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✔️ সাধারণ কিস্তি জমা করুন"):
                    if repay_amount > 0:
                        if repay_amount >= interest:
                            data["members"][phone]["loan_principal"] -= (repay_amount - interest)
                            data["members"][phone]["loan_interest"] = 0.0
