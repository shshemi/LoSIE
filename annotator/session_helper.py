from __future__ import annotations

import streamlit as st

SELECTED_FILE_KEY = "selected_file"


def get_selected_file() -> str | None:
    return st.session_state.get(SELECTED_FILE_KEY, None)


def set_selected_file(file: str | None) -> None:
    st.session_state[SELECTED_FILE_KEY] = file
