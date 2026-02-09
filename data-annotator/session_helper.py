from __future__ import annotations

from typing import Any

import streamlit as st

SELECTED_FILE_KEY = "selected_file"

DATASETS_KEY = "datasets"
DATASET_ORDER_KEY = "dataset_order"
SELECTED_DATASET_KEY = "selected_dataset_id"
LOAD_ERRORS_KEY = "disk_load_errors"
BOOTSTRAPPED_KEY = "_annotator_bootstrapped"


def get_selected_file() -> str | None:
    return st.session_state.get(SELECTED_FILE_KEY, None)


def set_selected_file(file: str | None) -> None:
    st.session_state[SELECTED_FILE_KEY] = file
