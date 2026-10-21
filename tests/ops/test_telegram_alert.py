import io
import json
import urllib.error
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


class _FakeResp:
    status = 200

    def __init__(self, body: bytes) -> None:
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _capture_urlopen(monkeypatch, responses):
    sent: list[dict] = []

    def fake_urlopen(req, timeout=None):
        sent.append(json.loads(req.data.decode("utf-8")))
        result = responses[len(sent) - 1]
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    return sent


def _http_400(description: str) -> urllib.error.HTTPError:
    body = json.dumps({"ok": False, "error_code": 400, "description": description}).encode("utf-8")
    return urllib.error.HTTPError("https://api.telegram.org", 400, "Bad Request", {}, io.BytesIO(body))


def test_send_telegram_message_includes_parse_mode_when_set(monkeypatch) -> None:
    sent = _capture_urlopen(monkeypatch, [_FakeResp(b'{"ok": true}')])

    result = send_telegram_message(bot_token="t", chat_id="c", text="<b>hi</b>", parse_mode="HTML")

    assert result["sent"] is True
    assert sent == [{"chat_id": "c", "text": "<b>hi</b>", "parse_mode": "HTML"}]


def test_send_telegram_message_omits_parse_mode_by_default(monkeypatch) -> None:
    sent = _capture_urlopen(monkeypatch, [_FakeResp(b'{"ok": true}')])

    send_telegram_message(bot_token="t", chat_id="c", text="hi")

    assert sent == [{"chat_id": "c", "text": "hi"}]


def test_send_telegram_message_resends_plain_text_on_entity_parse_error(monkeypatch) -> None:
    sent = _capture_urlopen(
        monkeypatch,
        [_http_400("Bad Request: can't parse entities: Unsupported start tag"), _FakeResp(b'{"ok": true}')],
    )

    result = send_telegram_message(
        bot_token="t",
        chat_id="c",
        text="<b>a &lt; b</b>\n<blockquote expandable>x &amp; y</blockquote>",
        parse_mode="HTML",
    )

    assert result["sent"] is True
    assert len(sent) == 2
    assert sent[0]["parse_mode"] == "HTML"
    assert "parse_mode" not in sent[1]
    assert sent[1]["text"] == "a < b\nx & y"


def test_send_telegram_message_does_not_resend_on_other_400(monkeypatch) -> None:
    sent = _capture_urlopen(monkeypatch, [_http_400("Bad Request: chat not found")])

    result = send_telegram_message(bot_token="t", chat_id="c", text="hi", parse_mode="HTML")

    assert result["sent"] is False
    assert result["status_code"] == 400
    assert len(sent) == 1
