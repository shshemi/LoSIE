import os

import streamlit as st

import storage
from storage import STORAGE_DIR

st.set_page_config(page_title="Upload Datasets", layout="centered")

st.title("Upload")
st.write("Upload JSONL files for verification.")
st.caption(f"Imported files are saved under `{str(STORAGE_DIR)}`.")

uploaded_files = st.file_uploader(
    "Upload dataset file",
    type=["jsonl"],
    accept_multiple_files=True,
)

if st.button("Import Selected File(s)", type="primary", disabled=not uploaded_files):
    for uploaded_file in uploaded_files or []:
        try:
            name = os.path.splitext(uploaded_file.name)[0]
            value = uploaded_file.getvalue()
            (line_count, path) = storage.import_file(value, name)
            st.success(f"File {name}({line_count} lines) imported into {path}")
        except ValueError as exc:
            st.error(f"{uploaded_file.name}: {exc}")
