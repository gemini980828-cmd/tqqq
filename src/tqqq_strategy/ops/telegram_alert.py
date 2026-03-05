from __future__ import annotations

import json
import urllib.error
import urllib.request


def _format_weight(value: float) -> str:
    return f"{value * 100:.2f}%"


def format_s2_change_message(
    date_str: str,
    prev_code: str,
    prev_weight: float,
    new_code: str,
    new_weight: float,
) -> str:
    return (
        "[TQQQ Daily Signal Alert]\n"
        f"Date: {date_str}\n"
        f"S2: {prev_code} ({_format_weight(prev_weight)})"
        f" -> {new_code} ({_format_weight(new_weight)})"
    )


def send_telegram_message(
    *,
    bot_token: str | None,
    chat_id: str | None,
    text: str,
    dry_run: bool = False,
    timeout: float = 10.0,
) -> dict:
    if dry_run:
        return {
            "sent": True,
            "dry_run": True,
            "status_code": None,
            "response": {"ok": True, "dry_run": True},
        }

    if not bot_token or not chat_id:
        return {
            "sent": False,
            "dry_run": False,
            "status_code": None,
            "error": "missing bot token or chat id",
        }

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    body = json.dumps({"chat_id": chat_id, "text": text}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url=url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            payload = json.loads(raw) if raw else {}
            return {
                "sent": bool(payload.get("ok")),
                "dry_run": False,
                "status_code": getattr(resp, "status", None),
                "response": payload,
            }
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        return {
            "sent": False,
            "dry_run": False,
            "status_code": exc.code,
            "error": raw or str(exc),
        }
    except urllib.error.URLError as exc:
        return {
            "sent": False,
            "dry_run": False,
            "status_code": None,
            "error": str(exc),
        }
