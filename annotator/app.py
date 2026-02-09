import streamlit as st

import session_helper
import storage

st.set_page_config(page_title="Training Data Annotator", layout="centered")

datasets = storage.list_files()

st.subheader("Datasets")
st.caption(f"Imported files are saved under `{str(storage.STORAGE_DIR)}`.")
if len(datasets) == 0:
    st.text("No dataset found")
for idx, dataset in enumerate(datasets):
    name_col, but_col = st.columns([9, 2])
    with name_col:
        st.markdown(f"#### {dataset}")

    with but_col:
        if st.button("Open", use_container_width=True, key=idx):
            session_helper.set_selected_file(dataset)
            st.switch_page("pages/2_View_Modify.py", query_params={"dataset": dataset})
