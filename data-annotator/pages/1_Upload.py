import streamlit as st

from annotator_utils import (
    ANNOTATOR_OUTPUT_DIR,
    LOAD_ERRORS_KEY,
    add_uploaded_file,
    format_saved_path,
    init_state,
)

st.set_page_config(page_title="Upload Datasets", layout="wide")
init_state()

st.title("Upload")
st.write("Upload JSONL/JSON files for annotation.")
st.caption(f"Imported files are saved under `{format_saved_path(ANNOTATOR_OUTPUT_DIR)}`.")
st.page_link("pages/2_View_Modify.py", label="Go to View / Modify")

disk_load_errors = st.session_state[LOAD_ERRORS_KEY]
if disk_load_errors:
    with st.expander(f"Could not load {len(disk_load_errors)} file(s) from disk"):
        for error in disk_load_errors:
            st.write(f"- {error}")

uploaded_files = st.file_uploader(
    "Select dataset files",
    type=["jsonl", "json"],
    accept_multiple_files=True,
)

if st.button("Import Selected Files", type="primary", disabled=not uploaded_files):
    for uploaded_file in uploaded_files or []:
        try:
            added, message = add_uploaded_file(uploaded_file)
            if added:
                st.success(message)
            else:
                st.info(message)
        except ValueError as exc:
            st.error(f"{uploaded_file.name}: {exc}")
