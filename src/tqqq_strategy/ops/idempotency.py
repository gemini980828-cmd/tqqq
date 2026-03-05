"""Idempotency helpers for daily ops."""


def build_alert_key(date_str, prev_code, new_code):
    return f"{date_str}:{prev_code}->{new_code}"
