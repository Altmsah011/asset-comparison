import streamlit as st
import pandas as pd
from io import BytesIO
import os

# 1. إعداد الصفحة وتفعيل دعم الواجهة العربية (RTL) بطريقة مستقرة
st.set_page_config(page_title="نظام المطابقة المطور", layout="wide")

st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] {
        direction: rtl !important;
        text-align: right !important;
    }
    div.stButton > button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# 2. إدارة قاعدة البيانات المحلية للمستخدمين
DB_FILE = "users_db.txt"

def load_users():
    users = {"admin": "admin123"}
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and ":" in line:
                    u, p = line.split(":", 1)
                    users[u] = p
    else:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            f.write("admin:admin123\n")
    return users

def save_users(users_dict):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        for u, p in users_dict.items():
            f.write(f"{u}:{p}\n")

USERS_DATABASE = load_users()

# 3. إدارة حالة الجلسة ومنع الـ Rerun العشوائي
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "current_user" not in st.session_state:
    st.session_state["current_user"] = ""

# --- شاشة تسجيل الدخول ---
if not st.session_state["logged_in"]:
    st.title("🔐 تسجيل الدخول إلى النظام")
    col1, col2, col3 = st.columns(3)
    with col2:
        username = st.text_input("👤 اسم المستخدم").strip().lower()
        password = st.text_input("🔑 كلمة المرور", type="password")
        if st.button("تسجيل الدخول 🚀"):
            if username in USERS_DATABASE and USERS_DATABASE[username] == password:
                st.session_state["logged_in"] = True
                st.session_state["current_user"] = username
                st.rerun()
            else:
                st.error("❌ اسم المستخدم أو كلمة المرور غير صحيحة!")

# --- واجهة البرنامج الأساسية ---
else:
    top_col1, top_col2 = st.columns(2)
    with top_col1:
        st.title("📦 نظام المطابقة المطور")
        st.caption(f"👤 المستخدم الحالي: **{st.session_state['current_user']}**")
    with top_col2:
        if st.button("تسجيل الخروج 🚪"):
            st.session_state["logged_in"] = False
            st.session_state["current_user"] = ""
            st.rerun()

    st.write("---")

    # لوحة تحكم الأدمن لإضافة المستخدمين
    if st.session_state["current_user"] == "admin":
        with st.expander("🛠️ لوحة تحكم مدير النظام (إدارة المستخدمين)", expanded=False):
            st.subheader("➕ إضافة مستخدم جديد")
            nu_col, np_col, nb_col = st.columns(3)
            with nu_col:
                new_username = st.text_input("👤 اسم المستخدم الجديد").strip().lower()
            with np_col:
                new_password = st.text_input("🔑 كلمة المرور للمستخدِم الجديد", type="password")
            with nb_col:
                st.write("\n\n")
                if st.button("إضافة الحساب 💾"):
                    if new_username and new_password:
                        if new_username in USERS_DATABASE:
                            st.error("❌ اسم المستخدم موجود بالفعل!")
                        else:
                            USERS_DATABASE[new_username] = new_password
                            save_users(USERS_DATABASE)
                            st.success("تم الحفظ بنجاح! 🎉")
                            st.rerun()
                    else:
                        st.error("الرجاء ملء الحقول!")
            
            st.write("---")
            current_users_list = [{"اسم المستخدم": u, "نوع الحساب": "مدير" if u == "admin" else "مستخدم"} for u in USERS_DATABASE.keys()]
            st.table(pd.DataFrame(current_users_list))

    # قسم رفع ومعالجة الملفات
    old_file = st.file_uploader("📁 ارفع الملف القديم", type=["xlsx"])
    new_file = st.file_uploader("📁 ارفع الملف الجديد", type=["xlsx"])

    if old_file and new_file:
        if "loaded_filename" not in st.session_state or st.session_state.get("loaded_filename") != new_file.name:
            st.session_state["old_df"] = pd.read_excel(old_file)
            st.session_state["new_df"] = pd.read_excel(new_file)
            st.session_state["loaded_filename"] = new_file.name

        old_df = st.session_state["old_df"]
        new_df = st.session_state["new_df"]

        st.success("تم تحميل الملفات بنجاح ✅")

        # اختيار أعمدة المطابقة
        st.subheader("🔗 إعدادات المطابقة")
        m_col1, m_col2 = st.columns(2)
        with m_col1:
            old_key = st.selectbox("عمود المطابقة في الملف القديم", old_df.columns)
        with m_col2:
            new_key = st.selectbox("عمود المطابقة في الملف الجديد", new_df.columns)

        # ربط الأعمدة لفحص التغيرات قيمياً
        st.subheader("🔍 فحص تعديل القيم داخل الأعمدة المشتركة")
        mapping = {}
        for col_old in old_df.columns:
            if col_old == old_key: continue
            default_idx = list(new_df.columns).index(col_old) + 1 if col_old in new_df.columns else 0
            mapping[col_old] = st.selectbox(
                f"العمود القديم [{col_old}] ↔ يقابله في الجديد:",
                ["— تجاهل —"] + list(new_df.columns),
                index=default_idx,
                key=f"m_{col_old}"
            )

        # زر تنفيذ العملية الأساسية
        if st.button("🚀 بدء المطابقة وفحص التغييرات الآن"):
            df_o = old_df.copy().rename(columns={old_key: "key"})
            df_n = new_df.copy().rename(columns={new_key: "key"})

            merged = df_o.merge(df_n, on="key", how="outer", suffixes=("_old", "_new"), indicator=True)

            missing = merged[merged["_merge"] == "left_only"].copy()
            new_items = merged[merged["_merge"] == "right_only"].copy()
            matched = merged[merged["_merge"] == "both"].copy()

            missing = missing[[c for c in missing.columns if c.endswith("_old") or c == "key"]]
            missing.columns = [c.replace("_old", "") for c in missing.columns]
            missing = missing.rename(columns={"key": old_key})

            new_items = new_items[[c for c in new_items.columns if c.endswith("_new") or c == "key"]]
            new_items.columns = [c.replace("_new", "") for c in new_items.columns]
            new_items = new_items.rename(columns={"key": new_key})

            changed_rows = []
            for idx, row in matched.iterrows():
                row_changes = {}
                has_change = False
                for col_old, col_new in mapping.items():
                    if col_new != "— تجاهل —":
                        v_old, v_new = row[f"{col_old}_old"], row[f"{col_new}_new"]
                        if pd.notna(v_old) or pd.notna(v_new):
                            if v_old != v_new:
                                has_change = True
                                row_changes[f"{col_old} (القديم)"] = v_old
                                row_changes[f"{col_old} (الجديد)"] = v_new
                if has_change:
                    row_changes[old_key] = row["key"]
                    changed_rows.append(row_changes)

            changed_df = pd.DataFrame(changed_rows) if changed_rows else pd.DataFrame(columns=[old_key])
            if not changed_df.empty and old_key in changed_df.columns:
                cols = [old_key] + [c for c in changed_df.columns if c != old_key]
                changed_df = changed_df[cols]

            # دمج البيانات الجديدة والمفقودة لإنشاء شيت البيانات النهائية الشامل
            missing_aligned = missing.reindex(columns=new_df.columns)
            final_combined_df = pd.concat([new_df, missing_aligned], ignore_index=True)

            # تخزين الحالات في الجلسة لضمان العرض وثبات الشاشة
            st.session_state["new_items"] = new_items
            st.session_state["missing_items"] = missing
            st.session_state["changed_items"] = changed_df
            st.session_state["final_items"] = final_combined_df
            
            # بناء ملف الإكسيل مسبقاً وتخزينه في الجلسة لحمايته وثباته
            excel_buffer = BytesIO()
            with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
                new_items.to_excel(writer, sheet_name="الأجهزة الجديدة", index=False)
                missing.to_excel(writer, sheet_name="الأجهزة المفقودة", index=False)
                changed_df.to_excel(writer, sheet_name="البيانات المعدلة", index=False)
                final_combined_df.to_excel(writer, sheet_name="البيانات النهائية الشاملة", index=False)
            
            st.session_state["excel_file_data"] = excel_buffer.getvalue()
            st.session_state["match_processed"] = True
            st.success("تمت عملية المطابقة وتجميع البيانات بنجاح! 🎯")

        # عرض واستخراج التقرير النهائي (تم التعديل الجذري هنا لمنع أخطاء الشروط والمسافات)
        if st.session_state.get("match_processed", False):
            st.write("---")
            st.subheader("📊 استعراض الجداول والنتائج")
            
            choice = st.radio("اختر الفئة لعرض بياناتها المباشرة:", ["🟢 الأجهزة الجديدة", "🔴 الأجهزة المفقودة", "🟡 البيانات المعدلة قيمياً", "🔵 البيانات النهائية الشاملة"], horizontal=True)
            
            # نظام الـ Mapping المستحيل يغلط في مسافة
            data_map = {
                "🟢 الأجهزة الجديدة": st.session_state["new_items"],
                "🔴 الأجهزة المفقودة": st.session_state["missing_items"],
                "🟡 البيانات المعدلة قيمياً": st.session_state["changed_items"],
                "🔵 البيانات النهائية الشاملة": st.session_state["final_items"]
            }
            
            selected_df = data_map[choice]
            
            if choice == "🟡 البيانات المعدلة قيمياً" and selected_df.empty:
                st.info("لا توجد اختلافات مكتشفة في قيم الحقول المشتركة.")
            else:
