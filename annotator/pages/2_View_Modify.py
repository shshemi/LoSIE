import streamlit as st

import session_helper
import storage

st.set_page_config(page_title="View / Modify", layout="wide")

if st.button("← Back", help="Go back to home", type="tertiary"):
    st.switch_page("app.py")
st.title("View / Modify")


dataset = session_helper.get_selected_file() or st.query_params.get("dataset")
if dataset is None:
    st.error("No dataset is selected!")
    st.stop()

sample = storage.get_next_unverified(dataset)
if sample is None:
    st.success("All samples are verified")
    st.stop()

idx, total, record = sample
st.caption(f"Editing record {idx + 1} / {total}")

st.markdown("text")
st.code(
    record["text"],
    language="python",
    wrap_lines=True,
)
target_value = st.text_area("target", value=record["target"], height=400)

if st.button("Submit", type="primary", use_container_width=True):
    storage.update_file(dataset, idx, target_value, True)
    st.rerun()
