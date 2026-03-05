def within_tolerance(expected: float, actual: float, tol: float = 0.001) -> bool:
    return abs(expected - actual) <= tol
