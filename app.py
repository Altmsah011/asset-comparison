import streamlit as st
import pandas as pd
from io import BytesIO
import os

# إعداد الصفحة القياسي المستقر لـ Streamlit
st.set_page_config(page_title="نظام المطابقة المطور", layout="wide")

# --- إدارة قاعدة بيانات المستخدمين باستخدام ملف نصي لحفظ البيانات ---
DB_FILE = "users_db.txt"

def load_users():
    """تحميل المستخدمين من الملف، وإذا لم يكن موجوداً يتم إنشاء حساب الـ admin الافتراضي"""
    users = {"admin": "admin123"}  # الحساب الافتراضي الأساسي
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and ":" in line:
                    u, p = line.split(":", 1)
                    users[u] = p
    else:
        save_users(users)  # إنشاء الملف لأول مرة
    return users

def save_users(users_dict):
    """حفظ قائمة المستخدمين الحالية داخل الملف"""
    with open(DB_FILE, "w", encoding="utf-8") as f:
        for u, p in users_dict.items():
            f.write(f"{u}:{p}\n")

# تحميل المستخدمين عند بدء التطبيق
USERS_DATABASE = load_users()

# إدارة حالة الجلسة في Streamlit
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "current_user" not in st.session_state:
    st.session_state["current_user"] = ""

# ==========================================
# 1. شاشة تسجيل الدخول للمتصفح
# ==========================================
if not st.session_state["logged_in"]:
    st.title("🔐 تسجيل الدخول إلى النظام")
    
    col1, col2, col3 = st.columns(3)
    with col2:
        st.write("الرجاء إدخال بيانات حسابك للوصول إلى نظام المطابقة:")
        username = st.text_input("👤 اسم المستخدم").strip().lower()
        password = st.text_input("🔑 كلمة المرور", type="password")
        
        if st.button("تسجيل الدخول 🚀", use_container_width=True):
            if username in USERS_DATABASE and USERS_DATABASE[username] == password:
                st.session_state["logged_in"] = True
                st.session_state["current_user"] = username
                st.success(f"مرحباً {username}! تم تسجيل الدخول بنجاح...")
                st.rerun()
            else:
                st.error("❌ اسم المستخدم أو كلمة المرور غير صحيحة!")
                
# ==========================================
# 2. واجهة البرنامج الأساسية (بعد تسجيل الدخول المعتمد)
# ==========================================
else:
    # شريط علوي يحتوي على ترحيب بالمستخدم الحالي وزر تسجيل الخروج
    top_col1, top_col2 = st.columns(2)
    with top_col1:
        st.title("📦 نظام المطابقة المطور")
        st.caption(f"👤 المستخدم الحالي: **{st.session_state['current_user']}**")
    with top_col2:
        st.write("") 
        if st.button("تسجيل الخروج 🚪", use_container_width=True):
            st.session_state["logged_in"] = False
            st.session_state["current_user"] = ""
            st.rerun()

    st.write("---")

    # ==========================================
    # 🌟 لوحة تحكم الأدمن (تظهر فقط إذا كان المستخدم admin)
    # ==========================================
    if st.session_state["current_user"] == "admin":
        with st.expander("🛠️ لوحة تحكم مدير النظام (إدارة المستخدمين)", expanded=False):
            st.subheader("➕ إضافة مستخدم جديد")
            
            new_u_col, new_p_col, btn_col = st.columns(3)
            with new_u_col:
                new_username = st.text_input("👤 اسم المستخدم الجديد").strip().lower()
            with new_p_col:
                new_password = st.text_input("🔑 كلمة المرور للمستخدِم الجديد", type="password")
            with btn_col:
                st.write("") 
                st.write("") 
                if st.button("إضافة الحساب 💾", use_container_width=True):
                    if not new_username or not new_password:
                        st.error("الرجاء ملء جميع الحقول!")
                    elif new_username in USERS_DATABASE:
                        st.error("❌ اسم المستخدم هذا موجود بالفعل!")
                    else:
                        USERS_DATABASE[new_username] = new_password
                        save_users(USERS_DATABASE)
                        st.success(f"تمت إضافة المستخدم ({new_username}) بنجاح! 🎉")
                        st.rerun()
            
            st.write("---")
            st.subheader("📋 المستخدمين الحاليين في النظام")
            current_users_list = [{"اسم المستخدم": u, "نوع الحساب": "مدير" if u == "admin" else "مستخدم"} for u in USERS_DATABASE.keys()]
            st.table(pd.DataFrame(current_users_list))
            
        st.write("---")

    # ==========================================
    # 3. قسم رفع ملفات المطابقة (متاح لجميع الحسابات)
    # ==========================================
    old_file = st.file_uploader("📁 ارفع الملف القديم", type=["xlsx"])
    new_file = st.file_uploader("📁 ارفع الملف الجديد", type=["xlsx"])

    if old_file and new_file:
        if "old_df" not in st.session_state or "new_file_name" not in st.session_state or st.session_state.new_file_name != new_file.name:
            st.session_state["old_df"] = pd.read_excel(old_file)
            st.session_state["new_df"] = pd.read_excel(new_file)
            st.session_state["new_file_name"] = new_file.name
            for key in ["new_items", "missing_items", "changed_items", "final_items"]:
                if key in st.session_state:
                    del st.session_state[key]

        old_df = st.session_state["old_df"]
        new_df = st.session_state["new_df"]

        st.success("تم تحميل الملفات بنجاح ✅")

        # اختيار عمود المطابقة
        st.subheader("🔗 اختيار عمود المطابقة")
        col1, col2 = st.columns(2)
        with col1:
            old_key = st.selectbox("عمود المطابقة في الملف القديم (مثل الرقم التسلسلي/المعرف)", old_df.columns)
        with col2:
            new_key = st.selectbox("عمود المطابقة في الملف الجديد (مثل الرقم التسلسلي/المعرف)", new_df.columns)

        # ربط الأعمدة والمقارنة
        st.subheader("🔗 ربط الأعمدة للمقارنة بين القيم")
        st.info("اختر العمود المقابل من الملف الجديد ليتم فحص التغييرات في قيمه.")
        
        mapping = {}
        for col_old in old_df.columns:
            if col_old == old_key:
                continue
            
            default_index = 0
            if col_old in new_df.columns:
                default_index = list(new_df.columns).index(col_old) + 1

            mapping[col_old] = st.selectbox(
                f"العمود في القديم: ({col_old}) ↔ يقابله في الجديد:",
                ["— تجاهل المقارنة —"] + list(new_df.columns),
                index=default_index,
                key=f"map_{col_old}"
            )

        # =========================
        # زر بدء المطابقة
        # =========================
        if st.button("🚀 بدء المطابقة وفحص التغييرات"):
            df_old_mod = old_df.copy().rename(columns={old_key: "key"})
            df_new_mod = new_df.copy().rename(columns={new_key: "key"})

            merged = df_old_mod.merge(
                df_new_mod,
                on="key",
                how="outer",
                suffixes=("_old", "_new"),
                indicator=True
            )

            missing_items = merged[merged["_merge"] == "left_only"].drop(columns=["_merge"])
            new_items = merged[merged["_merge"] == "right_only"].drop(columns=["_merge"])
            matched_items = merged[merged["_merge"] == "both"].drop(columns=["_merge"])

            missing_items = missing_items[[c for c in missing_items.columns if c.endswith("_old") or c == "key"]]
            missing_items.columns = [c.replace("_old", "") for c in missing_items.columns]
            missing_items = missing_items.rename(columns={"key": old_key})

            new_items = new_items[[c for c in new_items.columns if c.endswith("_new") or c == "key"]]
            new_items.columns = [c.replace("_new", "") for c in new_items.columns]
            new_items = new_items.rename(columns={"key": new_key})

            changed_rows = []
            for idx, row in matched_items.iterrows():
                row_changes = {}
                has_change = False
                
                for col_old, col_new in mapping.items():
                    if col_new != "— تجاهل المقارنة —":
                        val_old = row[f"{col_old}_old"]
                        val_new = row[f"{col_new}_new"]
                        
                        if pd.notna(val_old) or pd.notna(val_new):
                            if val_old != val_new:
                                has_change = True
                                row_changes[f"{col_old} (القديم)"] = val_old
                                row_changes[f"{col_old} (الجديد)"] = val_new
                
                if has_change:
                    row_changes[old_key] = row["key"]
                    changed_rows.append(row_changes)

            if changed_rows:
                changed_items = pd.DataFrame(changed_rows)
                cols = [old_key] + [c for c in changed_items.columns if c != old_key]
                changed_items = changed_items[cols]
            else:
                changed_items = pd.DataFrame(columns=[old_key, "حالة التغيير"])

            final_items = new_df.copy()

            st.session_state["new_items"] = new_items
            st.session_state["missing_items"] = missing_items
            st.session_state["changed_items"] = changed_items
            st.session_state["final_items"] = final_items

            st.success("تمت المطابقة وفحص التغييرات بنجاح ✅")

        # =========================
        # عرض النتائج
        # =========================
        if "new_items" in st.session_state:
            st.write("---")
            st.subheader("📊 استعراض نتائج المطابقة")
            
            view_option = st.selectbox(
                "اختر جدول البيانات الذي ترغب في عرضه:",
                [
                    "🟢 الأجهزة الجديدة (موجودة في الجديد فقط)", 
                    "🔴 الأجهزة المفقودة (موجودة في القديم فقط)", 
