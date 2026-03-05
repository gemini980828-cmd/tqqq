def passes_oos_gate(is_score: float, oos_score: float, min_ratio: float = 0.70) -> bool:
    if is_score <= 0:
        return False
    return (oos_score / is_score) >= min_ratio
