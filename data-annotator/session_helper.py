from __future__ import annotations

from typing import Any

import streamlit as st

DATASETS_KEY = "datasets"
DATASET_ORDER_KEY = "dataset_order"
SELECTED_DATASET_KEY = "selected_dataset_id"
LOAD_ERRORS_KEY = "disk_load_errors"
BOOTSTRAPPED_KEY = "_annotator_bootstrapped"


def ensure_datasets_initialized() -> None:
    st.session_state.setdefault(DATASETS_KEY, {})


def ensure_dataset_order_initialized() -> None:
    st.session_state.setdefault(DATASET_ORDER_KEY, [])


def ensure_selected_dataset_id_initialized() -> None:
    st.session_state.setdefault(SELECTED_DATASET_KEY, None)


def ensure_load_errors_initialized() -> None:
    st.session_state.setdefault(LOAD_ERRORS_KEY, [])


def is_bootstrapped() -> bool:
    return bool(st.session_state.get(BOOTSTRAPPED_KEY, False))


def set_bootstrapped(value: bool) -> None:
    st.session_state[BOOTSTRAPPED_KEY] = value


def get_datasets() -> dict[str, dict[str, Any]]:
    return st.session_state[DATASETS_KEY]


def get_dataset_order() -> list[str]:
    return st.session_state[DATASET_ORDER_KEY]


def get_selected_dataset_id() -> str | None:
    return st.session_state[SELECTED_DATASET_KEY]


def set_selected_dataset_id(dataset_id: str | None) -> None:
    st.session_state[SELECTED_DATASET_KEY] = dataset_id


def get_load_errors() -> list[str]:
    return st.session_state[LOAD_ERRORS_KEY]


def set_load_errors(errors: list[str]) -> None:
    st.session_state[LOAD_ERRORS_KEY] = errors


def set_dataset_current_index(dataset_id: str, current_index: int) -> None:
    get_datasets()[dataset_id]["current_index"] = current_index
