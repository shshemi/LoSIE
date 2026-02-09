import json
import os
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
STORAGE_DIR = PROJECT_ROOT / "output" / "annotator"
# STORAGE_DIR = "../output/annotator/"


def import_file(raw: bytes, name: str) -> tuple[int, str]:
    lines = raw.decode("utf-8")
    lines = (line.strip() for line in lines.splitlines())
    lines = [json.loads(s) for s in lines if s]
    for line in lines:
        line["verified"] = False

    lines = [json.dumps(obj) for obj in lines]
    content = "\n".join(lines)
    file = os.path.join(STORAGE_DIR, f"{name}.jsonl")
    with open(file, "w") as fp:
        fp.write(content)

    return len(lines), file


def list_files() -> list[str]:
    files = [
        os.path.splitext(file)[0]
        for file in os.listdir(STORAGE_DIR)
        if os.path.splitext(file)[1] == ".jsonl"
    ]
    return files


def load_file(name: str) -> list[dict[str, Any]]:
    with open(os.path.join(STORAGE_DIR, f"{name}.jsonl")) as fp:
        lines = (line.strip() for line in fp)
        lines = [json.loads(s) for s in lines if s]
    return lines


def update_file(
    file: str, index: int, target: str | None = None, verified: bool | None = None
):
    lines = load_file(file)
    if index < 0 or index >= len(lines):
        raise IndexError(f"Index {index} out of range")

    if target is not None:
        lines[index]["target"] = target

    if verified is not None:
        lines[index]["verified"] = verified

    lines = [json.dumps(obj) for obj in lines]
    content = "\n".join(lines)
    with open(os.path.join(STORAGE_DIR, f"{file}.jsonl"), "w") as fp:
        fp.write(content)


def get_next_unverified(
    file: str, index: int = 0
) -> tuple[int, int, dict[str, Any]] | None:
    lines = load_file(file)

    if index < 0 or index >= len(lines):
        raise IndexError(f"Index {index} out of range")

    for index in range(index, len(lines)):
        obj = lines[index]
        if not obj["verified"]:
            return index, len(lines), obj

    return None
