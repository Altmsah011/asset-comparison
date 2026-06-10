
import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="نظام المطابقة V2", layout="wide")

st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] {
    direction: rtl;
}
div.stButton > button {
    width:100%;
}
</style>
""", unsafe_allow_html=True)

st.title("📦 نظام المطابقة V2")

old_file = st.file_uploader("الملف القديم", type=["xlsx"])
new_file = st.file_uploader("الملف الجديد", type=["xlsx"])

if old_file and new_file:

    old_df = pd.read_excel(old_file)
    new_df = pd.read_excel(new_file)

    c1, c2 = st.columns(2)
    with c1:
        old_key = st.selectbox("مفتاح الملف القديم", old_df.columns)
    with c2:
        new_key = st.selectbox("مفتاح الملف الجديد", new_df.columns)

    st.subheader("ربط الأعمدة")

    mapping = {}
    for col in old_df.columns:
        if col == old_key:
            continue

        options = ["-- تجاهل --"] + list(new_df.columns)
        idx = options.index(col) if col in options else 0

        mapping[col] = st.selectbox(
            f"{col} ↔",
            options,
            index=idx,
            key=f"map_{col}"
        )

    st.subheader("خيارات إنشاء البيانات النهائية")

    add_new = st.checkbox("إضافة البيانات الجديدة للملف النهائي", value=True)
    remove_missing = st.checkbox("حذف البيانات المفقودة من الملف النهائي", value=False)
    apply_changes = st.checkbox("تطبيق التعديلات من الملف الجديد", value=True)
    replace_empty = st.checkbox("استبدال القيم القديمة بالقيم الفارغة", value=False)

    if st.button("🚀 تنفيذ المطابقة"):

        old_work = old_df.copy().rename(columns={old_key: "KEY"})
        new_work = new_df.copy().rename(columns={new_key: "KEY"})

        merged = old_work.merge(
            new_work,
            on="KEY",
            how="outer",
            suffixes=("_old", "_new"),
            indicator=True
        )

        new_items = merged[merged["_merge"] == "right_only"].copy()
        missing_items = merged[merged["_merge"] == "left_only"].copy()
        matched = merged[merged["_merge"] == "both"].copy()

        new_items = new_items[[c for c in new_items.columns if c.endswith("_new") or c == "KEY"]]
        new_items.columns = [c.replace("_new", "") for c in new_items.columns]

        missing_items = missing_items[[c for c in missing_items.columns if c.endswith("_old") or c == "KEY"]]
        missing_items.columns = [c.replace("_old", "") for c in missing_items.columns]

        changes = []

        for _, row in matched.iterrows():
            changed = False
            rec = {"KEY": row["KEY"]}

            for old_col, new_col in mapping.items():
                if new_col == "-- تجاهل --":
                    continue

                old_val = row.get(f"{old_col}_old")
                new_val = row.get(f"{new_col}_new")

                if pd.isna(old_val):
                    old_val = ""
                if pd.isna(new_val):
                    new_val = ""

                if old_val != new_val:
                    changed = True
                    rec[f"{old_col} (قديم)"] = old_val
                    rec[f"{old_col} (جديد)"] = new_val

            if changed:
                changes.append(rec)

        changed_df = pd.DataFrame(changes)

        final_df = old_df.copy()

        if apply_changes:
            final_df = final_df.set_index(old_key)
            temp_new = new_df.set_index(new_key)

            for key in final_df.index.intersection(temp_new.index):
                for old_col, new_col in mapping.items():
                    if new_col == "-- تجاهل --":
                        continue

                    value = temp_new.loc[key, new_col]

                    if pd.isna(value) and not replace_empty:
                        continue

                    if old_col in final_df.columns:
                        final_df.loc[key, old_col] = value

            final_df = final_df.reset_index()

        if add_new:
            new_only_keys = set(new_df[new_key]) - set(old_df[old_key])
            additions = new_df[new_df[new_key].isin(new_only_keys)]
            final_df = pd.concat([final_df, additions], ignore_index=True)

        if remove_missing:
            missing_keys = set(old_df[old_key]) - set(new_df[new_key])
            final_df = final_df[~final_df[old_key].isin(missing_keys)]

        st.success("تمت المطابقة بنجاح")

        st.metric("الجديدة", len(new_items))
        st.metric("المفقودة", len(missing_items))
        st.metric("المعدلة", len(changed_df))

        excel_buffer = BytesIO()

        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
            new_items.to_excel(writer, sheet_name="البيانات الجديدة", index=False)
            missing_items.to_excel(writer, sheet_name="البيانات المفقودة", index=False)
            changed_df.to_excel(writer, sheet_name="البيانات المعدلة", index=False)
            final_df.to_excel(writer, sheet_name="البيانات النهائية الشاملة", index=False)

            log_df = pd.DataFrame({
                "البند": [
                    "عدد البيانات الجديدة",
                    "عدد البيانات المفقودة",
                    "عدد البيانات المعدلة"
                ],
                "القيمة": [
                    len(new_items),
                    len(missing_items),
                    len(changed_df)
                ]
            })

            log_df.to_excel(writer, sheet_name="سجل العمليات", index=False)

        st.download_button(
            "📥 تحميل التقرير النهائي",
            excel_buffer.getvalue(),
            file_name="comparison_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
