import streamlit as st
import pandas as pd

st.title("Asset Management System 🔍 (Pro Version)")

old_file = st.file_uploader("Upload OLD File")
new_file = st.file_uploader("Upload NEW File")

if old_file and new_file:

    old_df = pd.read_excel(old_file)
    new_df = pd.read_excel(new_file)

    st.success("Files Loaded Successfully ✅")

    old_serial = st.selectbox("Old Serial Column", old_df.columns)
    new_serial = st.selectbox("New Serial Column", new_df.columns)

    if st.button("Run Comparison 🔍"):

        # Normalize
        old_df = old_df.rename(columns={old_serial: "serial"})
        new_df = new_df.rename(columns={new_serial: "serial"})

        # Merge full
        merged = old_df.merge(
            new_df,
            on="serial",
            how="outer",
            suffixes=("_old", "_new"),
            indicator=True
        )

        # Categories
        new_items = merged[merged["_merge"] == "right_only"]
        missing_items = merged[merged["_merge"] == "left_only"]
        matched = merged[merged["_merge"] == "both"]

        st.subheader("🟢 New Devices")
        st.dataframe(new_items)

        st.subheader("🔴 Missing Devices")
        st.dataframe(missing_items)

        # Detect changes
        changes = []

        for col in old_df.columns:
            if col != "serial":
                old_col = col + "_old"
                new_col = col + "_new"

                if old_col in matched.columns and new_col in matched.columns:
                    diff = matched[matched[old_col] != matched[new_col]].copy()

                    if not diff.empty:
                        diff["Changed Column"] = col
                        changes.append(diff)

        if changes:
            changes_df = pd.concat(changes)

            st.subheader("⚠️ Changes Detected")
            st.dataframe(changes_df)

        else:
            changes_df = pd.DataFrame()
            st.success("No Changes Found ✅")

        # Approve button
        if st.button("✔ Apply Updates"):

            final = old_df.set_index("serial").combine_first(
                new_df.set_index("serial")
            ).reset_index()

            st.subheader("📦 Final Updated Data")
            st.dataframe(final)

            # Excel export (multi sheets)
            from io import BytesIO
            import xlsxwriter

            output = BytesIO()

            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                final.to_excel(writer, sheet_name='Final Data', index=False)
                changes_df.to_excel(writer, sheet_name='Changes', index=False)
                new_items.to_excel(writer, sheet_name='New Items', index=False)
                missing_items.to_excel(writer, sheet_name='Missing Items', index=False)

            st.download_button(
                "📥 Download Full Report (Excel)",
                data=output.getvalue(),
                file_name="Asset_Report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
