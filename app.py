import streamlit as st
import pandas as pd

st.title("Asset Comparison Tool 🔍")

old_file = st.file_uploader("Upload OLD File")
new_file = st.file_uploader("Upload NEW File")

if old_file and new_file:

    old_df = pd.read_excel(old_file)
    new_df = pd.read_excel(new_file)

    st.write("Files uploaded successfully ✅")
    st.dataframe(old_df)
    st.dataframe(new_df)
