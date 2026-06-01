# Assistant 端 Service 层引入

## 模式（Cloud 端已验证通过）

**Service 类模式：**
```python
# assistant/app/services/xxx_service.py
from fastapi import Depends, HTTPException
from starlette import status
from assistant.app.database import get_db
from assistant.app.repositories import XxxRepository
from assistant.app.services.base import BaseService

class XxxService(BaseService):
    def __init__(self, db=Depends(get_db)):
        self.repo = XxxRepository(db)

    def get(self, record_id: int) -> dict:
        row = self.repo.get_by_id(record_id)
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")
        return dict(row)
    
    def create(self, data: dict) -> int:
        return self.repo.create(data)
    
    def update(self, record_id: int, data: dict) -> dict:
        self.repo.update(record_id, data)
        return dict(self.repo.get_by_id(record_id))
    
    def delete(self, record_id: int) -> None:
        self.repo.soft_delete(record_id)
```

**路由器改造后模式：**
```python
from assistant.app.services.xxx_service import XxxService

@router.get("")
def list_x(page=Query(1), page_size=Query(20), service: XxxService = Depends()):
    return success(data=service.list(page=page, page_size=page_size))

@router.post("")
def create_x(body: XxxCreate, service: XxxService = Depends()):
    row_id = service.create(body.model_dump())
    return JSONResponse(content=success(data={"id": row_id}).model_dump(), status_code=201)
```

## 任务

### 已有（已创建无需再动）
- `services/__init__.py`
- `services/base.py` — BaseService(Base)
- `services/hcp_service.py` — HcpService
- `services/visit_service.py` — VisitService

### 需要新建 + 改路由

| Service 文件 | 对应路由 | 关键逻辑 |
|:-------------|:---------|:---------|
| task_service.py | task_router.py | 任务 CRUD |
| qa_service.py | qa_router.py | QA 问答 |
| sync_service.py | sync_router.py | 数据同步 |
| voice_service.py | voice_router.py | 语音相关 |
| media_service.py | media_router.py | 媒体文件 CRUD |
| knowledge_service.py | knowledge_router.py | 知识库 CUD + 搜索 |
| surgery_service.py | surgery_router.py | 手术排期 CRUD |
| health_radar_service.py | health_radar_router.py | 健康雷达 CRUD |
| location_service.py | location_router.py | 位置 CRUD |

### 共9个 Service 类 + 12个路由改造（含已有）

## 验收标准

- [ ] 所有 12 个路由编译通过
- [ ] Assistant 端 8 个测试通过
- [ ] Cloud 端 42 个测试不受影响
