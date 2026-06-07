"""数据仓库模块，定义各实体的 Repository 类，封装数据库操作。"""

from assistant.app.hcp_repository import (  # noqa: F401
    HcpLocationRepository,
    HcpRepository,
    HealthRadarRepository,
    KnowledgeBaseRepository,
    MediaFileRepository,
    SurgeryReminderRepository,
    SyncQueueRepository,
    TaskRepository,
    VisitRecordRepository,
)
