## P2-3：base.py 模式统一

文件：cloud/app/services/base.py 和 sales-assistant/app/services/base.py

问题：assistant、opportunity、sales-coach 使用 shared.base_service 重导出模式，cloud 和 sales-assistant 自建 FastAPI Depends 模式。

cloud/app/services/base.py 当前内容：
```python
from typing import Any
from shared.base_service import BaseService as SharedBaseService, BaseCrudService as SharedBaseCrudService

__all__ = ["BaseService", "BaseCrudService"]
BaseService = SharedBaseService
BaseCrudService = SharedBaseCrudService
```

sales-assistant/app/services/base.py 当前内容（查看文件确定）。

改动：
1. 修改 cloud/app/services/base.py：保证与另外3端一致，从 shared.base_service 导入 BaseService 和 BaseCrudService。
2. 修改 sales-assistant/app/services/base.py：同样改为从 shared.base_service 导入。

注意：
- cloud/app/services/ 下 73 个文件使用 from cloud.app.services.base import BaseService，这些不能断
- sales-assistant/app/services/ 下文件使用 from sales_assistant.app.services.base import BaseService，这些不能断
- 要检查 cloud 和 sales-assistant 的 BaseService 是否传了 db 参数（与其他3端兼容）

验收：from cloud.app.services.base import BaseService 和 from sales_assistant.app.services.base import BaseService 正常。
