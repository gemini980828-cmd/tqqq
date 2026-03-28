from __future__ import annotations

from tqqq_strategy.ai.orchestrator_policy import classify_question, export_orchestrator_policy


def test_classify_question_prioritizes_generic_portfolio_prompts() -> None:
    policy = export_orchestrator_policy()

    result = classify_question("지금 우선순위를 전체적으로 요약해줘", policy=policy)

    assert result["primary_intent"] == "default_priority"
    assert result["brief_keys"][:2] == ["default_priority", "action"]


def test_classify_question_keeps_deterministic_order_for_mixed_prompts() -> None:
    policy = export_orchestrator_policy()

    result = classify_question("전체적으로 현금이랑 리스크 상태를 같이 정리해줘", policy=policy)

    assert result["brief_keys"] == ["default_priority", "action", "risk", "cash"]
    assert result["source_manager_ids"] == ["core_strategy", "cash_debt"]


def test_classify_question_maps_domain_specific_prompts_without_generic_fallback() -> None:
    policy = export_orchestrator_policy()

    result = classify_question("개별주와 부동산 중 어디를 먼저 볼까", policy=policy)

    assert result["brief_keys"] == ["stock_research", "real_estate"]
    assert result["primary_intent"] == "stock_research"


def test_classify_question_maps_recent_change_and_compare_prompts() -> None:
    policy = export_orchestrator_policy()

    changes = classify_question("최근 뭐가 바뀌었어?", policy=policy)
    compare = classify_question("코어전략이랑 현금 상황을 비교해줘", policy=policy)

    assert changes["primary_intent"] == "recent_changes"
    assert changes["brief_keys"] == ["recent_changes"]
    assert compare["primary_intent"] == "comparison"
    assert compare["brief_keys"] == ["comparison", "action", "cash"]
