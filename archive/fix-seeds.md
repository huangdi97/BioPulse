# 修复 seeds.py（1,291行） — 执行文档

## 目标
将 seeds.py 拆分为 seeds/ 包，每个种子函数一个独立文件，所有文件 ≤300行。

## 方案
### 结构变化
```
cloud/app/seeds.py              →  删除
cloud/app/seeds/                →  新建目录
  ├── __init__.py               →  导入并重新导出全部25个种子函数
  ├── seed_market_intel.py
  ├── seed_agent_data.py
  ├── seed_decision_intel.py
  ├── seed_compliance_v2.py
  ├── seed_mdt_engine.py
  ├── seed_memory_gates.py
  ├── seed_world_tree.py
  ├── seed_route_rules.py
  ├── seed_hcp_sandbox.py
  ├── seed_training_coach.py
  ├── seed_soap_decision.py
  ├── seed_memory_utility.py
  ├── seed_brain_memory.py
  ├── seed_identity.py
  ├── seed_privacy.py
  ├── seed_kg.py
  ├── seed_recommend.py
  ├── seed_collaboration.py
  ├── seed_event_bus.py
  ├── seed_memory_s1.py
  ├── seed_s2.py
  ├── seed_s3.py
  ├── seed_s4.py
  ├── seed_s5.py
  └── seed_s6.py
```

### 改动范围
**database.py — 完全不用改**
- `from cloud.app.seeds import seed_market_intel, ...` — 路径不变，seeds/__init__.py 自动重导出

**删除文件**
- `cloud/app/seeds.py`（原文件）

## 验证清单
- [ ] `python3 -c "from cloud.app.seeds import seed_market_intel"` — 导入正常
- [ ] `python3 -c "from cloud.app.database import init_db"` — database.py 导入正常
- [ ] 每个种子文件 ≤100行（实际平均~51行）
- [ ] 无重复代码，每个函数只在一个文件中
