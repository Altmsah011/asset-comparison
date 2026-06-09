import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="نظام المطابقة", layout="wide")

# RTL Arabic UI
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

    # اختيار عمود المطابقة
    st.subheader("🔗 اختيار عمود المطابقة")

    old_key = st.selectbox("عمود المطابقة في الملف القديم", old_df.columns)
    new_key = st.selectbox("عمود المطابقة في الملف الجديد", new_df.columns)

    # ربط الأعمدة
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

    # =========================
    # زر بدء المطابقة
    # =========================
    if st.button("🚀 بدء المطابقة"):

        old_df = old_df.rename(columns={old_key: "key"})
        new_df = new_df.rename(columns={new_key: "key"})

        merged = old_df.merge(
            new_df,
            on="key",
            how="outer",
            suffixes=("_old", "_new"),
            indicator=True
        )

        # حفظ النتائج
        st.session_state["new_items"] = merged[merged["_merge"] == "right_only"]
        st.session_state["missing_items"] = merged[merged["_merge"] == "left_only"]
        st.session_state["matched"] = merged[merged["_merge"] == "both"]

        st.success("تمت المطابقة بنجاح ✅")

    # =========================
    # عرض النتائج
    # =========================
    if "new_items" in st.session_state:

        st.subheader("🟢 الأجهزة الجديدة")
        st.dataframe(st.session_state["new_items"], use_container_width=True)

        st.subheader("🔴 الأجهزة المفقودة")
        st.dataframe(st.session_state["missing_items"], use_container_width=True)

    # =========================
    # زر التقرير
    # =========================
    if st.button("✔ تحديث البيانات وإنشاء التقرير"):

        if "new_items" not in st.session_state:
            st.error("من فضلك اضغط بدء المطابقة أولاً")
        else:

            output = BytesIO()

            with pd.ExcelWriter(output, engine="openpyxl") as writer:

                pd.DataFrame().to_excel(writer, sheet_name="البيانات النهائية", index=False)

                st.session_state["new_items"].to_excel(writer, sheet_name="الجديدة", index=False)
                st.session_state["missing_items"].to_excel(writer, sheet_name="المفقودة", index=False)

            st.success("تم إنشاء التقرير بنجاح ✅")

            st.download_button(
                "📥 تحميل التقرير",
                data=output.getvalue(),
                file_name="System_Report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
