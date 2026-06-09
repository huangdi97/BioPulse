# 修复·批次5（P1-7～P1-10：分词 + 魔法数字 + 硬编码 + 低效循环）

你是 Codex CLI。请直接执行，不要调用其他编码Agent，你自己干。

## 1. P1-7：sentiment_analyzer.py 子串匹配改为分词匹配

**文件：** `cloud/app/crawler/analysis/sentiment_analyzer.py`

当前：`word.lower() in text` 子串匹配

改为正则精确匹配：
```python
import re
pattern = re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE)
matches = pattern.findall(text)
```

在 `_classify_sentiment` 函数中修改所有 `word.lower() in text.lower()` 的匹配方式。

## 2. P1-8：trend_detector.py 魔法数字命名化

**文件：** `cloud/app/crawler/analysis/trend_detector.py`

提取 `0.08` 为 `UPWARD_TREND_THRESHOLD = 0.08`，`1` 为 `MIN_REGRESSION_POINTS = 1`
加注释说明阈值的含义（0.08 = 斜率显著上升的阈值）。

## 3. P1-9：threshold_alerter.py 硬编码 days 参数化

**文件：** `cloud/app/crawler/analysis/threshold_alerter.py`

将 `check_threshold` 函数中的 `days=14` 改为函数参数：
```python
def check_threshold(product_id: str, threshold_pct: float = 10.0, days: int = 14) -> list[dict]:
```

## 4. P1-10：sentiment_analyzer.py track_mentions 低效循环

**文件：** `cloud/app/crawler/analysis/sentiment_analyzer.py` 第100-113行

`track_mentions` 循环中反复调用 `analyze()` 重新加载数据。

改为：在循环外加载一次数据，在内存中按平台遍历筛选。
