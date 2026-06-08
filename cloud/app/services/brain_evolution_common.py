"""脑记忆进化共享工具。"""

from datetime import datetime


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def calc_confidence(memory_type: str, importance: float, valence: float = 0.0) -> float:
    base = importance * 0.6 + abs(valence) * 0.4
    if memory_type == "episodic":
        return round(min(base * 1.1, 1.0), 4)
    return round(min(base, 1.0), 4)
