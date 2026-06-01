# 任务：拆分 seeds.py 为 seeds/ 包

## 目标
将 1291 行的 cloud/app/seeds.py 拆分为 seeds/ 包（25个独立文件 + __init__.py）

## 步骤

### 步骤1：创建 cloud/app/seeds/ 目录
```bash
mkdir -p cloud/app/seeds
```

### 步骤2：创建每个种子文件
从 seeds.py 按函数切分，每个函数一个文件。文件内容 = 对应函数的完整代码（含 import）。

函数-行映射：
```
seed_market_intel     L5-41    (37行)
seed_agent_data       L42-87   (46行)
seed_decision_intel   L88-154  (67行)
seed_compliance_v2    L155-214 (60行)
seed_mdt_engine       L215-286 (72行)
seed_memory_gates     L287-334 (48行)
seed_world_tree       L335-371 (37行)
seed_route_rules      L372-396 (25行)
seed_hcp_sandbox      L397-455 (59行)
seed_training_coach   L456-504 (49行)
seed_soap_decision    L505-592 (88行)
seed_memory_utility   L593-631 (39行)
seed_brain_memory     L632-694 (63行)
seed_identity         L695-775 (81行)
seed_privacy          L776-820 (45行)
seed_kg               L821-861 (41行)
seed_recommend        L862-911 (50行)
seed_collaboration    L912-992 (81行)
seed_event_bus        L993-1063(71行)
seed_memory_s1        L1064-1077(14行)
seed_s2               L1078-1120(43行)
seed_s4               L1121-1158(38行)
seed_s3               L1159-1200(42行)
seed_s5               L1201-1255(55行)
seed_s6               L1256-1291(36行)
```

每个种子文件 ≈ 原始种子函数代码 + 文件头部的 `import json` 和 `import sqlite3`（仅首次），但实际 seeds.py 只在最顶部有这2个 import，所有函数共享——所以每个种子文件都要加这2个 import。

### 步骤3：创建 __init__.py
导入并重导出全部25个种子函数：
```python
import json
import sqlite3

from .seed_market_intel import seed_market_intel
from .seed_agent_data import seed_agent_data
...（每个函数一行）
from .seed_s6 import seed_s6

__all__ = [
    "seed_market_intel", "seed_agent_data", ...,
    "seed_s6",
]
```

### 步骤4：删除原文件
```bash
rm cloud/app/seeds.py
```

### 步骤5：验证
```bash
python3 -m py_compile cloud/app/seeds/__init__.py && echo "OK"
python3 -c "from cloud.app.seeds import seed_market_intel; print('OK')"
# 递归编译所有种子文件
for f in cloud/app/seeds/seed_*.py; do python3 -m py_compile "$f" && echo "  $f OK"; done
```

⚠️ 不要改动 cloud/app/database.py — 它的 import 路径不变
