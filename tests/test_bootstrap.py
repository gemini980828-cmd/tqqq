import importlib


def test_import_tqqq_strategy_package() -> None:
    module = importlib.import_module("tqqq_strategy")
    assert module.__name__ == "tqqq_strategy"
