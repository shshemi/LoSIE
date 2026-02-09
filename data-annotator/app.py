import streamlit as st

from annotator_utils import (
    format_saved_path,
    init_state,
    remove_dataset,
)
from session_helper import (
    get_dataset_order,
    get_datasets,
    set_selected_dataset_id,
)

st.set_page_config(page_title="Training Data Annotator", layout="wide")
init_state()

order = get_dataset_order()
datasets = get_datasets()

st.subheader("Uploaded Files")
if not order:
    st.info("No dataset uploaded yet.")
else:
    for dataset_id in order.copy():
        dataset = datasets[dataset_id]
        left_col, mid_col, right_col = st.columns([6, 2, 2])
        with left_col:
            st.write(f"**{dataset['name']}**")
            st.caption(f"{len(dataset['records'])} records")
            saved_path = dataset.get("saved_path")
            if saved_path:
                st.caption(f"Saved at `{format_saved_path(saved_path)}`")
        with mid_col:
            if st.button("Select", key=f"main_select_{dataset_id}", use_container_width=True):
                set_selected_dataset_id(dataset_id)
                st.switch_page("pages/2_View_Modify.py")
        with right_col:
            if st.button("Remove", key=f"main_remove_{dataset_id}", use_container_width=True):
                remove_dataset(dataset_id)
                st.rerun()
