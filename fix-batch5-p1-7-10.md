## P1-7：sentiment_analyzer.py 子串匹配改为分词匹配

文件：cloud/app/crawler/analysis/sentiment_analyzer.py

问题：word.lower() in text 是子串匹配而非分词匹配。

改动：改用正则 re.search(r'\b' + re.escape(word) + r'\b', text) 或分词后精确匹配。

验收：边界词（如"疗法"不匹配"疗效"）测试通过。

## P1-8：trend_detector.py 魔法数字文档化

文件：cloud/app/crawler/analysis/trend_detector.py

问题：斜率阈值 0.08 和回归检查数量 1 无文档说明。

改动：提取为命名常量并加注释。

验收：常量命名清晰，有注释说明。

## P1-9：threshold_alerter.py 参数硬编码

文件：cloud/app/crawler/analysis/threshold_alerter.py

问题：days=14 硬编码在 check_threshold 中。

改动：将 days 改为函数参数，默认值保持 14。

验收：check_threshold(product_id, threshold_pct=10, days=30) 可自定义参数。

## P1-10：sentiment_analyzer.py track_mentions 低效循环

文件：cloud/app/crawler/analysis/sentiment_analyzer.py 第100-113行

问题：track_mentions 循环中反复调用 analyze() 重新加载数据。

改动：批量加载一次数据，在内存中遍历筛选。

验收：track_mentions 只调用一次数据加载。
