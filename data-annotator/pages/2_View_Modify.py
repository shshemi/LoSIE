import streamlit as st

from annotator_utils import init_state
from session_helper import (
    get_dataset_order,
    get_datasets,
    get_selected_dataset_id,
    set_dataset_current_index,
    set_selected_dataset_id,
)


st.set_page_config(page_title="View / Modify", layout="wide")
init_state()

st.title("View / Modify")

order = get_dataset_order()
datasets = get_datasets()

if not order:
    st.info("No uploaded files found.")
    st.stop()

selected_dataset_id = get_selected_dataset_id()
if selected_dataset_id not in datasets:
    selected_dataset_id = order[0]
    set_selected_dataset_id(selected_dataset_id)
dataset = datasets[selected_dataset_id]

warnings = dataset["warnings"]
if warnings:
    with st.expander(f"Normalization warnings ({len(warnings)})"):
        for warning in warnings:
            st.write(f"- {warning}")

records = dataset["records"]
total_records = len(records)
if total_records == 0:
    st.warning("This file has no records to edit.")
    st.stop()

current_index = dataset.get("current_index", 0)
current_index = max(0, min(current_index, total_records - 1))
set_dataset_current_index(selected_dataset_id, current_index)

st.caption(f"Editing record {current_index + 1} of {total_records}")

record = records[current_index]
target_key = f"target_{selected_dataset_id}_{current_index}"


st.markdown("text")
st.code(
    record["text"],
    language="python",
    wrap_lines=True,
)
target_value = st.text_area(
    "target", value=record["target"], height=400, key=target_key
)

if st.button("Submit", type="primary", use_container_width=True):
    record["target"] = target_value
    record["verified"] = True
    if current_index < total_records - 1:
        set_dataset_current_index(selected_dataset_id, current_index + 1)
    st.rerun()
