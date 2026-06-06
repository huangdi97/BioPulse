# Opportunity repositories.py 彻底迁移

## 目标

删除 `opportunity/app/repositories.py`（329 行），将其中的 5 个在用类迁移到 `repositories/` 独立文件中，清理所有死类和 importlib 黑科技。

## 背景

`repositories.py` 有 10 个类，其中 5 个有实际引用，5 个零引用（死代码）。`repositories/` 目录下有 4 个独立文件，但全部零引用——是一次半途而废的迁移。

`repositories/__init__.py` 使用 importlib 动态加载 `repositories.py` 再 `from old_module import *`，是黑科技，需要换成标准 import。

## 修改步骤

### 步骤 1：清理 `repositories/` 独立文件中的死类

文件：`opportunity/app/repositories/bidding_repository.py`
- 删除：`BiddingRepository` 类（零引用）
- 删除：`BiddingAgentRepository` 类（零引用）
- 删除：`BookmarkRepository` 类（零引用）
- 添加：从以下代码迁移 `BiddingInfoRepository` 类的完整代码
  - 来源：`opportunity/app/repositories.py` 第 83-112 行
- 添加：`UserBookmarkRepository` 类的完整代码
  - 来源：`opportunity/app/repositories.py` 第 141-172 行

文件：`opportunity/app/repositories/contact_repository.py`
- 删除：`ContactRepository` 类（零引用）
- 删除：`ResearchRepository` 类（零引用）
- 保留：`OpportunityRepository` 类（已在独立文件中，且与 repositories.py 中内容相同）
- 添加：`ContactRecordRepository` 类的完整代码
  - 来源：`opportunity/app/repositories.py` 第 48-83 行
- 添加：`ResearchTrailRepository` 类的完整代码
  - 来源：`opportunity/app/repositories.py` 第 112-141 行

文件：`opportunity/app/repositories/scoring_repository.py`
- 删除：`ScoringRepository` 类（零引用）
- 删除：`TrendRepository` 类（零引用）
- 删除：`PubPeerRepository` 类（零引用）
- 保留：`StatsRepository` 类（和 repositories.py 中的内容相同，保留独立文件中的版本）

### 步骤 2：清理 `repositories.py` 中的死类

文件：`opportunity/app/repositories.py`
- 删除以下 5 个零引用类：
  - `PaperIntegrityRepository`（第 172-206 行）
  - `TrendAnalysisRepository`（第 207-230 行）
  - `BiddingAgentConfigRepository`（第 231-259 行）
  - `BiddingAgentLogRepository`（第 260-283 行）
  - `StatsRepository`（第 284-329 行，已在独立文件中保留）
- 保留以下 5 个在用类：
  - `OpportunityRepository`（第 19-48 行）
  - `ContactRecordRepository`（第 48-83 行）
  - `BiddingInfoRepository`（第 83-112 行）
  - `ResearchTrailRepository`（第 112-141 行）
  - `UserBookmarkRepository`（第 141-172 行）

### 步骤 3：修改 `__init__.py`

文件：`opportunity/app/repositories/__init__.py`

删除 importlib 动态加载代码（第 1-13 行），只保留从独立文件的标准 import。

从独立文件 import 的类改为：
```python
from .bidding_repository import BiddingInfoRepository, UserBookmarkRepository
from .contact_repository import ContactRecordRepository, OpportunityRepository, ResearchTrailRepository
from .scoring_repository import StatsRepository
```

### 步骤 4：删除 `repositories.py`

文件：`opportunity/app/repositories.py`

**删除整个文件。** 所有在用类已迁移到独立文件中，不再需要。

## 为什么不修改调用端？

`from opportunity.app.repositories import Xxx` 的调用路径不变，因为 `repositories/__init__.py` 已经导出了全部需要的类。调用端零改动。

## 验收标准

- [ ] `python -c "from opportunity.app.repositories import OpportunityRepository, ContactRecordRepository, BiddingInfoRepository, ResearchTrailRepository, UserBookmarkRepository, StatsRepository"` 无报错
- [ ] `python -m pytest opportunity/app/tests/ -q --tb=line` 输出 `7 passed`
- [ ] `ruff check opportunity/` 无新增错误
- [ ] `repositories.py` 文件已被删除
- [ ] `repositories/__init__.py` 中无 `importlib` 引用
