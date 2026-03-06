from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Iterable


def _format_weight(value: float) -> str:
    return f"{value * 100:.2f}%"


def format_s2_change_message(
    date_str: str,
    prev_code: str,
    prev_weight: float,
    new_code: str,
    new_weight: float,
    *,
    title: str = "일일현황보고",
    alert_type: str = "일일 신호 점검 알림",
    action_line: str | None = None,
    position_lines: Iterable[str] | None = None,
    reason: str = "기본 추세/보유 유지",
    reason_lines: Iterable[str] | None = None,
    market_lines: Iterable[str] | None = None,
    ops_lines: Iterable[str] | None = None,
) -> str:
    pos = list(position_lines or [])
    reasons = list(reason_lines or [])
    market = list(market_lines or [])
    ops = list(ops_lines or [])

    if not pos:
        pos = [
            f"현재 포지션: TQQQ({_format_weight(new_weight)})",
            f"교체 포지션: TQQQ({_format_weight(prev_weight)})",
            f"신호코드 전환: {prev_code}->{new_code}",
        ]

    if not market:
        market = ["시장 데이터 요약: N/A"]

    if not ops:
        ops = ["ops log: N/A"]

    if not reasons:
        reasons = [f"사유: {reason}"]

    lines = [f"[ {date_str} ] {title}", f"🚨 {alert_type}", action_line or "📢 [액션 없음] 포지션 유지"]
    if pos:
        lines += ["", *pos]
    if reasons:
        lines += ["", "🧩 체크", *reasons]
    if market:
        lines += ["", "📈 시장 요약", *market]
    if ops:
        lines += ["", "🧾 운영 로그", *ops]
    return "\n".join(lines)


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
