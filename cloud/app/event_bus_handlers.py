"""事件总线路由的请求模型。"""

from pydantic import BaseModel


class EventDefCreate(BaseModel):
    event_type: str
    display_name: str = ""
    description: str = ""
    source_end: str = "cloud"
    target_ends: list[str] = []
    schema_template: dict = {}
    priority: int = 100


class EventPublish(BaseModel):
    event_type: str
    source_entity_type: str = ""
    source_entity_id: str = ""
    payload: dict = {}
    correlation_id: str = ""


class EventSubscribe(BaseModel):
    event_types: list[str] = []
    target_end: str
    callback_url: str = ""
