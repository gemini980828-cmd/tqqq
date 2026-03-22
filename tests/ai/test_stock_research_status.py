from tqqq_strategy.ai.stock_research_status import is_candidate_status, normalize_stock_status


def test_normalize_stock_status_maps_legacy_values() -> None:
    assert normalize_stock_status("매수후보") == "후보"
    assert normalize_stock_status("검토") == "후보"
    assert normalize_stock_status("") == "탐색"


def test_is_candidate_status_accepts_normalized_candidates() -> None:
    assert is_candidate_status("후보") is True
    assert is_candidate_status("매수후보") is True
    assert is_candidate_status("검토") is True
    assert is_candidate_status("관찰") is False
