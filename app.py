import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="نظام المطابقة المطور", layout="wide")

# RTL Arabic UI
st.markdown("""
<style>
html, body, [class*="css"] {
    direction: rtl;
    text-align: right;
}
</style>
""", unsafe_allow_html=True)

st.title("📦 نظام المطابقة المطور")

# Upload files
old_file = st.file_uploader("📁 ارفع الملف القديم", type=["xlsx"])
new_file = st.file_uploader("📁 ارفع الملف الجديد", type=["xlsx"])

if old_file and new_file:
    # قراءة الملفات مرة واحدة وتخزينها لتجنب إعادة التحميل المستمر
    if "old_df" not in st.session_state or "new_file_name" not in st.session_state or st.session_state.new_file_name != new_file.name:
        st.session_state["old_df"] = pd.read_excel(old_file)
        st.session_state["new_df"] = pd.read_excel(new_file)
        st.session_state["new_file_name"] = new_file.name
        # تصفير النتائج السابقة عند رفع ملفات جديدة
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
        
        # محاولة مطابقة الأسماء تلقائياً لتسهيل التجربة على المستخدم
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
        # نسخ البيانات لتجنب تعديل الأصل
        df_old_mod = old_df.copy().rename(columns={old_key: "key"})
        df_new_mod = new_df.copy().rename(columns={new_key: "key"})

        # دمج البيانات دمجاً كاملاً (Outer Join)
        merged = df_old_mod.merge(
            df_new_mod,
            on="key",
            how="outer",
            suffixes=("_old", "_new"),
            indicator=True
        )

        # 1. الأجهزة المفقودة والجديدة
        missing_items = merged[merged["_merge"] == "left_only"].drop(columns=["_merge"])
        new_items = merged[merged["_merge"] == "right_only"].drop(columns=["_merge"])
        matched_items = merged[merged["_merge"] == "both"].drop(columns=["_merge"])

        # تنظيف أسماء الأعمدة للمفقود والجديد لتبدو بشكل سليم
        missing_items = missing_items[[c for c in missing_items.columns if c.endswith("_old") or c == "key"]]
        missing_items.columns = [c.replace("_old", "") for c in missing_items.columns]
        missing_items = missing_items.rename(columns={"key": old_key})

        new_items = new_items[[c for c in new_items.columns if c.endswith("_new") or c == "key"]]
        new_items.columns = [c.replace("_new", "") for c in new_items.columns]
        new_items = new_items.rename(columns={"key": new_key})

        # 2. فحص التغييرات في الأعمدة المربوطة (للأجهزة الموجودة في الملفين)
        changed_rows = []
        
        for idx, row in matched_items.iterrows():
            row_changes = {}
            has_change = False
            
            for col_old, col_new in mapping.items():
                if col_new != "— تجاهل المقارنة —":
                    val_old = row[f"{col_old}_old"]
                    val_new = row[f"{col_new}_new"]
                    
                    # مقارنة القيم (مع التعامل مع القيم الفارغة)
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
            # ترتيب الأعمدة ليظهر المعرف أولاً
            cols = [old_key] + [c for c in changed_items.columns if c != old_key]
            changed_items = changed_items[cols]
        else:
            changed_items = pd.DataFrame(columns=[old_key, "حالة التغيير"])

        # 3. بناء البيانات النهائية (تحديث القديم بالجديد + إضافة الجديد بالكامل)
        # نأخذ نسخة من الملف الجديد كقاعدة أساسية للبيانات الحالية والنهائية
        final_items = new_df.copy()

        # تخزين النتائج في الـ session_state لمنع اختفائها عند التحديث
        st.session_state["new_items"] = new_items
        st.session_state["missing_items"] = missing_items
        st.session_state["changed_items"] = changed_items
        st.session_state["final_items"] = final_items

        st.success("تمت المطابقة وفحص التغييرات بنجاح ✅")

    # =========================
    # عرض النتائج
    # =========================
    if "new_items" in st.session_state:
        tab1, tab2, tab3 = st.tabs(["🟢 الأجهزة الجديدة", "🔴 الأجهزة المفقودة", "🟡 بيانات تم تعديلها"])
        
        with tab1:
            st.subheader("🟢 الأجهزة الجديدة (موجودة في الجديد فقط)")
            st.dataframe(st.session_state["new_items"], use_container_width=True)
            
        with tab2:
            st.subheader("🔴 الأجهزة المفقودة (موجودة في القديم فقط)")
            st.dataframe(st.session_state["missing_items"], use_container_width=True)
            
        with tab3:
            st.subheader("🟡 الاختلافات المكتشفة في الأعمدة المربوطة")
            if not st.session_state["changed_items"].empty:
                st.dataframe(st.session_state["changed_items"], use_container_width=True)
            else:
                st.info("لا توجد اختلافات في قيم الأعمدة بين الملفين للأجهزة المتطابقة.")

        # =========================
        # قسم تحميل التقرير
        # =========================
        st.write("---")
        st.subheader("💾 تحميل التقرير النهائي")
        
        # إنشاء ملف الاكسيل مباشرة لتفادي مشاكل الـ Rerun والأزرار المتداخلة
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            st.session_state["final_items"].to_excel(writer, sheet_name="البيانات النهائية", index=False)
            st.session_state["new_items"].to_excel(writer, sheet_name="الجديدة", index=False)
            st.session_state["missing_items"].to_excel(writer, sheet_name="المالمفقودة", index=False)
            st.session_state["changed_items"].to_excel(writer, sheet_name="التعديلات والاختلافات", index=False)
        
        st.download_button(
            "📥 تحميل التقرير كملف Excel المحدث",
            data=output.getvalue(),
            file_name="System_Final_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
