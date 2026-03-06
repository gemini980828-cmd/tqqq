import urllib.request

from tqqq_strategy.ops.telegram_alert import format_s2_change_message, send_telegram_message


def test_format_s2_change_message_contains_key_fields() -> None:
    message = format_s2_change_message(
        date_str="2026-03-06",
        prev_code="1",
        prev_weight=1.0,
        new_code="3",
        new_weight=0.25,
        action_line="📢 [매매 필요] 현금 → TQQQ 25%",
        reason_lines=["✅ 조건 A", "⬜ 조건 B"],
    )

    assert "2026-03-06" in message
    assert "1" in message
    assert "3" in message
    assert "100.00%" in message
    assert "25.00%" in message
    assert "->" in message
    assert "현재 포지션" in message
    assert "교체 포지션" in message
    assert "[매매 필요]" in message
    assert "🧩 체크" in message
    assert "✅ 조건 A" in message


def test_send_telegram_message_dry_run_returns_sent_without_network_call(monkeypatch) -> None:
    def fail_if_called(*args, **kwargs):
        raise AssertionError("network call must not happen during dry_run")

    monkeypatch.setattr(urllib.request, "urlopen", fail_if_called)

    result = send_telegram_message(
        bot_token="dummy-token",
        chat_id="dummy-chat",
        text="hello",
        dry_run=True,
    )

    assert result["sent"] is True
    assert result["dry_run"] is True
