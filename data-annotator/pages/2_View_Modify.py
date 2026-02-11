import streamlit as st

from annotator_utils import (
    DATASET_ORDER_KEY,
    DATASETS_KEY,
    SELECTED_DATASET_KEY,
    init_state,
)


def navigation_controls(
    dataset_id: str, total_records: int, current_index: int
) -> None:
    prev_col, next_col = st.columns(2)

    with prev_col:
        if st.button(
            "Previous",
            key=f"prev_{dataset_id}",
            use_container_width=True,
            disabled=current_index == 0,
        ):
            st.session_state[DATASETS_KEY][dataset_id]["current_index"] = (
                current_index - 1
            )
            st.rerun()

    with next_col:
        if st.button(
            "Next",
            key=f"next_{dataset_id}",
            use_container_width=True,
            disabled=current_index >= total_records - 1,
        ):
            st.session_state[DATASETS_KEY][dataset_id]["current_index"] = (
                current_index + 1
            )
            st.rerun()


st.set_page_config(page_title="View / Modify", layout="wide")
init_state()

st.title("View / Modify")

order = st.session_state[DATASET_ORDER_KEY]
datasets = st.session_state[DATASETS_KEY]

if not order:
    st.info("No uploaded files found.")
    st.stop()

selected_dataset_id = st.session_state[SELECTED_DATASET_KEY]
if selected_dataset_id not in datasets:
    selected_dataset_id = order[0]
    st.session_state[SELECTED_DATASET_KEY] = selected_dataset_id
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
dataset["current_index"] = current_index

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

if target_value != record["target"]:
    record["target"] = target_value

st.divider()
navigation_controls(selected_dataset_id, total_records, current_index)
