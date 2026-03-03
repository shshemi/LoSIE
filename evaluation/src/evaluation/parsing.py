"""Parse structured target strings into key-value dicts."""

from __future__ import annotations


def parse_target(text: str) -> dict[str, str]:
    """Parse a structured target string into key-value pairs.

    Format:
        key1 value1
        key2 value2

    Key is the first whitespace-delimited token; value is the rest of the line.

    Returns:
        {"key1": "value1", ...}
    """
    keys: dict[str, str] = {}

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        parts = line.split(None, 1)
        key = parts[0]
        value = parts[1] if len(parts) > 1 else ""
        keys[key] = value

    return keys
