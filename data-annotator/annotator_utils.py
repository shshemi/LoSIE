from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import streamlit as st

REQUIRED_FIELDS = ("text", "target")
DATASETS_KEY = "datasets"
DATASET_ORDER_KEY = "dataset_order"
SELECTED_DATASET_KEY = "selected_dataset_id"
LOAD_ERRORS_KEY = "disk_load_errors"
BOOTSTRAPPED_KEY = "_annotator_bootstrapped"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
ANNOTATOR_OUTPUT_DIR = PROJECT_ROOT / "output" / "annotator"


def stringify_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def normalize_records(raw_records: list[Any]) -> tuple[list[dict[str, Any]], list[str]]:
    if not raw_records:
        raise ValueError("No records found in uploaded file.")

    normalized: list[dict[str, Any]] = []
    warnings: list[str] = []

    for index, item in enumerate(raw_records, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Record {index} is not a JSON object.")

        record = dict(item)
        for field in REQUIRED_FIELDS:
            if field not in record:
                record[field] = ""
                warnings.append(f"Record {index} is missing '{field}'. Added an empty string.")
            elif not isinstance(record[field], str):
                record[field] = stringify_value(record[field])
                warnings.append(
                    f"Record {index} field '{field}' was converted to a string."
                )

        normalized.append(record)

    return normalized, warnings


def parse_json_file(content: str) -> tuple[list[dict[str, Any]], list[str]]:
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON: {exc}") from exc

    if isinstance(parsed, list):
        raw_records = parsed
    elif isinstance(parsed, dict):
        if all(field in parsed for field in REQUIRED_FIELDS):
            raw_records = [parsed]
        else:
            raise ValueError(
                "JSON must be a list of objects, or one object containing 'text' and 'target'."
            )
    else:
        raise ValueError("JSON must be an object or an array of objects.")

    return normalize_records(raw_records)


def parse_jsonl_file(content: str) -> tuple[list[dict[str, Any]], list[str]]:
    raw_records: list[Any] = []
    for line_number, line in enumerate(content.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            raw_records.append(json.loads(stripped))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON on line {line_number}: {exc}") from exc

    if not raw_records:
        raise ValueError("No JSON records were found in the uploaded JSONL file.")

    return normalize_records(raw_records)


def parse_uploaded_dataset(
    file_name: str, raw_bytes: bytes
) -> tuple[list[dict[str, Any]], list[str]]:
    try:
        content = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("File must be UTF-8 encoded.") from exc

    suffix = Path(file_name).suffix.lower()
    if suffix == ".json":
        try:
            return parse_json_file(content)
        except ValueError:
            return parse_jsonl_file(content)
    if suffix == ".jsonl":
        return parse_jsonl_file(content)

    try:
        return parse_jsonl_file(content)
    except ValueError:
        return parse_json_file(content)


def output_file_name(input_name: str, extension: str) -> str:
    stem = Path(input_name).stem or "dataset"
    return f"{stem}.edited.{extension}"


def init_state() -> None:
    st.session_state.setdefault(DATASETS_KEY, {})
    st.session_state.setdefault(DATASET_ORDER_KEY, [])
    st.session_state.setdefault(SELECTED_DATASET_KEY, None)
    st.session_state.setdefault(LOAD_ERRORS_KEY, [])

    if not st.session_state.get(BOOTSTRAPPED_KEY, False):
        ANNOTATOR_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        load_saved_datasets_from_disk()
        st.session_state[BOOTSTRAPPED_KEY] = True


def format_saved_path(saved_path: str | Path) -> str:
    path = Path(saved_path)
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def save_uploaded_file(file_name: str, raw_bytes: bytes, dataset_id: str) -> Path:
    ANNOTATOR_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    base_name = Path(file_name).name or f"{dataset_id}.jsonl"
    stem = Path(base_name).stem or "dataset"
    suffix = Path(base_name).suffix or ".jsonl"
    candidate = ANNOTATOR_OUTPUT_DIR / base_name

    if candidate.exists():
        try:
            existing_hash = hashlib.sha256(candidate.read_bytes()).hexdigest()
            if existing_hash == dataset_id:
                return candidate
        except OSError:
            pass

        candidate = ANNOTATOR_OUTPUT_DIR / f"{stem}-{dataset_id[:8]}{suffix}"
        counter = 1
        while candidate.exists():
            try:
                existing_hash = hashlib.sha256(candidate.read_bytes()).hexdigest()
                if existing_hash == dataset_id:
                    return candidate
            except OSError:
                pass
            candidate = ANNOTATOR_OUTPUT_DIR / f"{stem}-{dataset_id[:8]}-{counter}{suffix}"
            counter += 1

    candidate.write_bytes(raw_bytes)
    return candidate


def add_dataset_to_session(
    dataset_id: str,
    name: str,
    records: list[dict[str, Any]],
    warnings: list[str],
    saved_path: Path | None,
) -> None:
    datasets: dict[str, dict[str, Any]] = st.session_state[DATASETS_KEY]
    order: list[str] = st.session_state[DATASET_ORDER_KEY]

    if dataset_id in datasets:
        if saved_path is not None:
            datasets[dataset_id]["saved_path"] = str(saved_path)
        return

    datasets[dataset_id] = {
        "id": dataset_id,
        "name": name,
        "records": records,
        "warnings": warnings,
        "current_index": 0,
        "saved_path": str(saved_path) if saved_path is not None else None,
    }
    order.append(dataset_id)

    if st.session_state[SELECTED_DATASET_KEY] is None:
        st.session_state[SELECTED_DATASET_KEY] = dataset_id


def load_saved_datasets_from_disk() -> None:
    datasets: dict[str, dict[str, Any]] = st.session_state[DATASETS_KEY]
    errors: list[str] = []

    ANNOTATOR_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for file_path in sorted(ANNOTATOR_OUTPUT_DIR.iterdir()):
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in {".json", ".jsonl"}:
            continue

        try:
            raw_bytes = file_path.read_bytes()
        except OSError as exc:
            errors.append(f"{file_path.name}: {exc}")
            continue

        dataset_id = hashlib.sha256(raw_bytes).hexdigest()
        if dataset_id in datasets:
            if not datasets[dataset_id].get("saved_path"):
                datasets[dataset_id]["saved_path"] = str(file_path)
            continue

        try:
            records, warnings = parse_uploaded_dataset(file_path.name, raw_bytes)
        except ValueError as exc:
            errors.append(f"{file_path.name}: {exc}")
            continue

        add_dataset_to_session(dataset_id, file_path.name, records, warnings, file_path)

    st.session_state[LOAD_ERRORS_KEY] = errors


def add_uploaded_file(uploaded_file: Any) -> tuple[bool, str]:
    raw_bytes = uploaded_file.getvalue()
    dataset_id = hashlib.sha256(raw_bytes).hexdigest()

    datasets: dict[str, dict[str, Any]] = st.session_state[DATASETS_KEY]
    if dataset_id in datasets:
        if not datasets[dataset_id].get("saved_path"):
            saved_path = save_uploaded_file(uploaded_file.name, raw_bytes, dataset_id)
            datasets[dataset_id]["saved_path"] = str(saved_path)
            return (
                False,
                f"{uploaded_file.name} is already uploaded and was saved to {format_saved_path(saved_path)}.",
            )
        return False, f"{uploaded_file.name} is already uploaded."

    records, warnings = parse_uploaded_dataset(uploaded_file.name, raw_bytes)
    saved_path = save_uploaded_file(uploaded_file.name, raw_bytes, dataset_id)
    add_dataset_to_session(dataset_id, uploaded_file.name, records, warnings, saved_path)
    return (
        True,
        "Imported "
        f"{uploaded_file.name} ({len(records)} records), saved to {format_saved_path(saved_path)}.",
    )


def remove_dataset(dataset_id: str, delete_file: bool = True) -> None:
    datasets: dict[str, dict[str, Any]] = st.session_state[DATASETS_KEY]
    order: list[str] = st.session_state[DATASET_ORDER_KEY]
    dataset = datasets.get(dataset_id)
    saved_path_value = dataset.get("saved_path") if dataset else None

    if dataset_id in datasets:
        del datasets[dataset_id]
    if dataset_id in order:
        order.remove(dataset_id)

    if delete_file and saved_path_value:
        saved_path = Path(saved_path_value)
        if saved_path.exists():
            try:
                saved_path.unlink()
            except OSError:
                pass

    if st.session_state[SELECTED_DATASET_KEY] == dataset_id:
        st.session_state[SELECTED_DATASET_KEY] = order[0] if order else None


def dataset_label(dataset_id: str) -> str:
    dataset = st.session_state[DATASETS_KEY][dataset_id]
    return f"{dataset['name']} ({len(dataset['records'])} records)"
