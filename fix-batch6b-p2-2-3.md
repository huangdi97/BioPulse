## P2-2续：重构剩余5个 database.py

已创建 shared/database.py（149行，通用 SQLiteDatabase 基类）。剩余5个端还未重构：

- assistant/app/database.py
- sales-assistant/app/database.py
- sales-coach/app/database.py
- opportunity/app/database.py
- management/app/database.py

改动：从 shared.database import SQLiteDatabase 继承，只保留本端特有的建表逻辑。保持向后兼容。

验收：各端 from X.app.database import get_connection, init_db 仍正常工作。

## P2-3：base.py 模式统一

文件：cloud/app/services/base.py 和 sales-assistant/app/services/base.py

问题：assistant、opportunity、sales-coach 使用 shared.base_service 重导出模式，但 cloud 和 sales-assistant 自建 FastAPI Depends。

改动：修改 cloud/app/services/base.py 和 sales-assistant/app/services/base.py 为与另外3端一致的方式，从 shared.base_service 导入。

验收：from cloud.app.services.base import BaseService 和 from sales-assistant.app.services.base import BaseService 都能正常工作。
