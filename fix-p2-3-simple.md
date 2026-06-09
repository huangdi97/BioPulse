## P2-3：base.py 模式统一

将 cloud 和 sales-assistant 的 base.py 改为与另外3端一致的重导出模式。

### 1. cloud/app/services/base.py

当前代码（使用 Depends 注入）：
```python
from fastapi import Depends
from cloud.app.database import get_db
from shared.base_service import BaseService as _BaseService

class BaseService(_BaseService):
    def __init__(self, db=Depends(get_db)):
        self.db = db
```

改为：
```python
from shared.base_service import BaseService, BaseCrudService

__all__ = ["BaseService", "BaseCrudService"]
```

保持 from cloud.app.services.base import BaseService 能正常导入。

### 2. sales-assistant/app/services/base.py

当前代码：
```python
from fastapi import Depends
from sales_assistant.app.database import get_db
from shared.base_service import BaseCrudService as _BaseCrudService
from shared.base_service import BaseService as _BaseService

class BaseService(_BaseService):
    def __init__(self, db=Depends(get_db)):
        self.db = db

class BaseCrudService(_BaseCrudService):
    ...
    def __init__(self, repository_class=None, entity_name=None, db=Depends(get_db)):
        ...
    def _close_connection(self, conn):
        pass
```

改为：
```python
from shared.base_service import BaseService, BaseCrudService

__all__ = ["BaseService", "BaseCrudService"]
```

保持 from sales_assistant.app.services.base import BaseService 和 BaseCrudService 能正常导入。

注意：shared.base_service 的 BaseService.__init__(self, db=None) 和 BaseCrudService.__init__(self, repository_class=None, entity_name="entity", db=None) 已经支持外部传 db，所以去掉 Depends 后不会破坏已有功能。
