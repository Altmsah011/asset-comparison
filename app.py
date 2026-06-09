import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="نظام المطابقة", layout="wide")

st.markdown("""
<style>
html, body, [class*="css"] {
    direction: rtl;
    text-align: right;
}
</style>
""", unsafe_allow_html=True)

st.title("📦 نظام المطابقة")

# Upload files
old_file = st.file_uploader("📁 ارفع الملف القديم", type=["xlsx"])
new_file = st.file_uploader("📁 ارفع الملف الجديد", type=["xlsx"])

if old_file and new_file:

    old_df = pd.read_excel(old_file)
    new_df = pd.read_excel(new_file)

    st.success("تم تحميل الملفات بنجاح ✅")

    # اختيار مفتاح المطابقة
    st.subheader("🔗 اختيار عمود المطابقة")

    old_key = st.selectbox("عمود المطابقة في القديم", old_df.columns)
    new_key = st.selectbox("عمود المطابقة في الجديد", new_df.columns)

    # Mapping
    st.subheader("🔗 ربط الأعمدة")

    mapping = {}

    for col_old in old_df.columns:
        if col_old == old_key:
            continue

        mapping[col_old] = st.selectbox(
            f"{col_old} ↔",
            [""] + list(new_df.columns),
            key=col_old
        )

    if st.button("🚀 بدء المطابقة"):

        # توحيد المفاتيح
        old_df = old_df.rename(columns={old_key: "key"})
        new_df = new_df.rename(columns={new_key: "key"})

        merged = old_df.merge(
            new_df,
            on="key",
            how="outer",
            suffixes=("_old", "_new"),
            indicator=True
        )

        # 🟢 الجديدة
        new_items = merged[merged["_merge"] == "right_only"]

        # 🔴 المفقودة
        missing_items = merged[merged["_merge"] == "left_only"]

        # 🟡 المشتركة
        matched = merged[merged["_merge"] == "both"]

        # ⚠️ التغييرات
        changes_list = []

        for old_col, new_col in mapping.items():

            if new_col == "":
                continue

            old_c = old_col + "_old"
            new_c = new_col + "_new"

            if old_c in matched.columns and new_c in matched.columns:

                diff = matched[
                    matched[old_c].fillna("") != matched[new_c].fillna("")
                ].copy()

                if not diff.empty:
                    diff["Field"] = old_col
                    changes_list.append(diff)

        changes_df = pd.concat(changes_list) if changes_list else pd.DataFrame()

        # =========================
        # عرض النتائج منفصل
        # =========================

        st.subheader("🟢 الأجهزة الجديدة")
        st.dataframe(new_items)

        st.subheader("🔴 الأجهزة المفقودة")
        st.dataframe(missing_items)

        st.subheader("🟡 الأجهزة المتغيرة")
        st.dataframe(changes_df)

        # =========================
        # تحديث + تحميل Excel
        # =========================

        if st.button("✔ تحديث البيانات وإنشاء التقرير"):

            final_df = new_df.copy()

            output = BytesIO()

            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                final_df.to_excel(writer, sheet_name="البيانات النهائية", index=False)
                new_items.to_excel(writer, sheet_name="الجديدة", index=False)
                missing_items.to_excel(writer, sheet_name="المفقودة", index=False)
                changes_df.to_excel(writer, sheet_name="التغييرات", index=False)

            st.success("تم إنشاء التقرير بنجاح ✅")

            st.download_button(
                "📥 تحميل التقرير",
                data=output.getvalue(),
                file_name="System_Report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
