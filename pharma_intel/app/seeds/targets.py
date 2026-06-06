"""靶点种子数据。"""

from typing import Any

_months = [
    "2025-04",
    "2025-05",
    "2025-06",
    "2025-07",
    "2025-08",
    "2025-09",
    "2025-10",
    "2025-11",
    "2025-12",
    "2026-01",
    "2026-02",
    "2026-03",
]


def _make_trend(base: float, variance: float) -> list[dict[str, Any]]:
    import math

    return [{"month": m, "count": max(0, round(base + math.sin(i * 0.8) * variance))} for i, m in enumerate(_months)]


targets: list[dict[str, Any]] = [
    {
        "id": 1,
        "name": "PD-1",
        "category": "免疫检查点",
        "paper_count": 18420,
        "trial_count": 3820,
        "growth": 12.5,
        "trend_data": _make_trend(1500, 200),
    },
    {
        "id": 2,
        "name": "HER2",
        "category": "受体酪氨酸激酶",
        "paper_count": 8650,
        "trial_count": 1580,
        "growth": 5.2,
        "trend_data": _make_trend(720, 80),
    },
    {
        "id": 3,
        "name": "EGFR",
        "category": "受体酪氨酸激酶",
        "paper_count": 12350,
        "trial_count": 2450,
        "growth": 3.8,
        "trend_data": _make_trend(1030, 120),
    },
    {
        "id": 4,
        "name": "CTLA-4",
        "category": "免疫检查点",
        "paper_count": 4520,
        "trial_count": 890,
        "growth": 8.1,
        "trend_data": _make_trend(380, 60),
    },
    {
        "id": 5,
        "name": "KRAS G12C",
        "category": "信号转导",
        "paper_count": 2890,
        "trial_count": 520,
        "growth": 35.6,
        "trend_data": _make_trend(240, 70),
    },
    {
        "id": 6,
        "name": "VEGF",
        "category": "血管生成因子",
        "paper_count": 9870,
        "trial_count": 2100,
        "growth": 2.1,
        "trend_data": _make_trend(820, 90),
    },
    {
        "id": 7,
        "name": "CD19",
        "category": "免疫细胞表面抗原",
        "paper_count": 3210,
        "trial_count": 680,
        "growth": 15.4,
        "trend_data": _make_trend(270, 50),
    },
    {
        "id": 8,
        "name": "BCMA",
        "category": "免疫细胞表面抗原",
        "paper_count": 1870,
        "trial_count": 420,
        "growth": 22.8,
        "trend_data": _make_trend(160, 40),
    },
    {
        "id": 9,
        "name": "ALK",
        "category": "受体酪氨酸激酶",
        "paper_count": 3450,
        "trial_count": 750,
        "growth": 6.7,
        "trend_data": _make_trend(290, 45),
    },
    {
        "id": 10,
        "name": "PARP1",
        "category": "DNA修复酶",
        "paper_count": 5670,
        "trial_count": 1120,
        "growth": 18.3,
        "trend_data": _make_trend(470, 85),
    },
]
