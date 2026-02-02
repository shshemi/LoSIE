#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
import http.cookiejar
import re
import urllib.request
from pathlib import Path

CHUNK_SIZE = 1024 * 1024  # 1 MiB
BASE_URL = "https://drive.google.com/uc?export=download&id="
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"


def _build_url(object_id: str, confirm: str | None = None) -> str:
    url = f"{BASE_URL}{object_id}"
    if confirm:
        url = f"{url}&confirm={confirm}"
    return url


def _get_confirm_token_from_cookies(cookie_jar: http.cookiejar.CookieJar) -> str | None:
    for cookie in cookie_jar:
        if cookie.name.startswith("download_warning"):
            return cookie.value
    return None


def _get_confirm_token_from_html(html: str) -> str | None:
    match = re.search(r"confirm=([0-9A-Za-z_-]+)", html)
    return match.group(1) if match else None


def _is_file_response(response: urllib.request.addinfourl) -> bool:
    content_disposition = response.headers.get("Content-Disposition", "")
    content_type = response.headers.get("Content-Type", "")
    if "attachment" in content_disposition.lower():
        return True
    return "text/html" not in content_type.lower()


def download_google_drive(object_id: str, dest_path: Path) -> None:
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = dest_path.with_suffix(dest_path.suffix + ".part")

    try:
        cookie_jar = http.cookiejar.CookieJar()
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))
        request = urllib.request.Request(_build_url(object_id), headers={"User-Agent": USER_AGENT})

        with opener.open(request) as response:
            if _is_file_response(response):
                with tmp_path.open("wb") as out:
                    while True:
                        chunk = response.read(CHUNK_SIZE)
                        if not chunk:
                            break
                        out.write(chunk)
            else:
                html = response.read(2 * 1024 * 1024).decode("utf-8", errors="ignore")
                token = _get_confirm_token_from_cookies(cookie_jar) or _get_confirm_token_from_html(html)
                if not token:
                    raise RuntimeError("Unable to retrieve Google Drive confirmation token.")

                confirm_request = urllib.request.Request(
                    _build_url(object_id, token), headers={"User-Agent": USER_AGENT}
                )
                with opener.open(confirm_request) as confirm_response, tmp_path.open("wb") as out:
                    while True:
                        chunk = confirm_response.read(CHUNK_SIZE)
                        if not chunk:
                            break
                        out.write(chunk)
        tmp_path.replace(dest_path)
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink()
        raise


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    dest_dir = repo_root / "output" / "splits"

    object_ids = {
        "train.jsonl": "1wrzmIx3mPcpYZR9yHzF8jzyJHksC1MX0",
        "valid.jsonl": "1QuzkNw93tHxz4b1dDMsja_lo6CAe1ESM",
        "test.jsonl": "1ZBbcxGBgA0rxW9JaR_KFw1n4gZPhl5Fn",
    }

    for name, object_id in object_ids.items():
        dest_path = dest_dir / name
        print(f"Downloading {name} -> {dest_path}")
        download_google_drive(object_id, dest_path)

    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
