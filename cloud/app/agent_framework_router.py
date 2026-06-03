from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from cloud.app.services.agent_framework_service import AgentFrameworkService
from shared.auth_scope import require_scope
from shared.base import success


class TemplateCreate(BaseModel):
    """TemplateCreate 服务类。"""

    template_key: str
    name: str = ""
    description: str = ""
    domain: str = "generic"
    capabilities: list[str] = []
    default_config: dict = {}
    triggers: list[str] = []
    endpoints: list[str] = []


class InstanceCreate(BaseModel):
    """InstanceCreate 服务类。"""

    instance_key: str
    template_key: str
    display_name: str = ""
    bind_to_end: str = "cloud"
    config_overrides: dict = {}


router = APIRouter(prefix="/agent/framework", tags=["Agent Framework"])


@router.get("/templates", summary="List all Templates")
def list_templates(
    domain: str = Query(None),
    service: AgentFrameworkService = Depends(),
    _=Depends(require_scope(["pharma", "research"])),
):
    """list_templates 操作。

    Args:
        domain: 描述
        service: 描述
        _: 描述
    """
    return success(data=service.list_templates(domain=domain))


@router.get("/templates/{template_key}", summary="Get Template by ID")
def get_template(
    template_key: str,
    service: AgentFrameworkService = Depends(),
    _=Depends(require_scope(["pharma", "research"])),
):
    """get_template 操作。

    Args:
        template_key: 描述
        service: 描述
        _: 描述
    """
    return success(data=service.get_template(template_key))


@router.post("/templates", summary="Create Template")
def create_template(
    body: TemplateCreate,
    service: AgentFrameworkService = Depends(),
    _=Depends(require_scope(["pharma", "research"])),
):
    """create_template 操作。

    Args:
        service: 描述
        _: 描述
    """
    return success(
        data=service.create_template(
            key=body.template_key,
            name=body.name,
            description=body.description,
            domain=body.domain,
            capabilities=body.capabilities,
            default_config=body.default_config,
            triggers=body.triggers,
            endpoints=body.endpoints,
        )
    )


@router.get("/instances", summary="List all Instances")
def list_instances(
    status: str = Query(None),
    template_key: str = Query(None),
    service: AgentFrameworkService = Depends(),
    _=Depends(require_scope(["pharma", "research"])),
):
    """list_instances 操作。

    Args:
        status: 描述
        template_key: 描述
        service: 描述
        _: 描述
    """
    return success(data=service.list_instances(status=status, template_key=template_key))


@router.get("/instances/{instance_key}", summary="Get Instance by ID")
def get_instance(
    instance_key: str,
    service: AgentFrameworkService = Depends(),
    _=Depends(require_scope(["pharma", "research"])),
):
    """get_instance 操作。

    Args:
        instance_key: 描述
        service: 描述
        _: 描述
    """
    return success(data=service.get_instance(instance_key))


@router.post("/instances", summary="Create Instance")
def create_instance(
    body: InstanceCreate,
    service: AgentFrameworkService = Depends(),
    _=Depends(require_scope(["pharma", "research"])),
):
    """create_instance 操作。

    Args:
        service: 描述
        _: 描述
    """
    return success(
        data=service.create_instance(
            instance_key=body.instance_key,
            template_key=body.template_key,
            display_name=body.display_name,
            bind_to_end=body.bind_to_end,
            config_overrides=body.config_overrides,
        )
    )


@router.post("/instances/{instance_key}/start", summary="Start Instance")
def start_instance(
    instance_key: str,
    service: AgentFrameworkService = Depends(),
    _=Depends(require_scope(["pharma", "research"])),
):
    """start_instance 操作。

    Args:
        instance_key: 描述
        service: 描述
        _: 描述
    """
    return success(data=service.start_instance(instance_key))


@router.post("/instances/{instance_key}/stop", summary="Stop Instance")
def stop_instance(
    instance_key: str,
    service: AgentFrameworkService = Depends(),
    _=Depends(require_scope(["pharma", "research"])),
):
    """stop_instance 操作。

    Args:
        instance_key: 描述
        service: 描述
        _: 描述
    """
    return success(data=service.stop_instance(instance_key))


@router.post("/instances/{instance_key}/heartbeat", summary="Heartbeat Instance")
def heartbeat_instance(
    instance_key: str,
    service: AgentFrameworkService = Depends(),
    _=Depends(require_scope(["pharma", "research"])),
):
    """heartbeat_instance 操作。

    Args:
        instance_key: 描述
        service: 描述
        _: 描述
    """
    return success(data=service.heartbeat_instance(instance_key))
