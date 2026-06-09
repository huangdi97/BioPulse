"""记忆工具路由。"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from cloud.app.services.memory_utility_service import MemoryUtilityService
from shared.base import success

router = APIRouter(prefix="/memory-utils", tags=["Memory Utilities"])


class MoveRequest(BaseModel):
    new_parent_id: int


@router.post("/tree/subtree-stats/{node_id}", tags=["Memory Utilities"])
def subtree_stats(node_id: int, service: MemoryUtilityService = Depends()):
    """获取指定节点的子树统计信息。

    Args:
        node_id: 节点 ID

    Returns: 子树统计（节点数、深度等）
    """
    return success(data=service.subtree_stats(node_id))


@router.post("/tree/move/{node_id}", tags=["Memory Utilities"])
def move_node(node_id: int, body: MoveRequest, service: MemoryUtilityService = Depends()):
    """将节点移动到新的父节点下。

    Args:
        node_id: 要移动的节点 ID
        body:    请求体（含新的父节点 ID）

    Returns: 操作结果消息
    """
    result = service.move_node(node_id, body.new_parent_id)
    return success(message=result.get("message"))


@router.get("/tree/heatmap", tags=["Memory Utilities"])
def tree_heatmap(service: MemoryUtilityService = Depends()):
    """获取记忆树的热力图数据。

    Args:
        service: 记忆工具服务

    Returns: 热力图数据
    """
    return success(data=service.tree_heatmap())


@router.get("/tree/duplicates/{node_id}", tags=["Memory Utilities"])
def tree_duplicates(node_id: int, service: MemoryUtilityService = Depends()):
    """查找指定节点下的重复记忆条目。

    Args:
        node_id: 节点 ID

    Returns: 重复条目列表
    """
    return success(data=service.tree_duplicates(node_id))


@router.delete("/tree/prune/{node_id}", tags=["Memory Utilities"])
def prune_node(node_id: int, service: MemoryUtilityService = Depends()):
    """剪枝删除节点及其子树。

    Args:
        node_id: 要删除的节点 ID

    Returns: 被删除的条目数量及消息
    """
    result = service.prune_node(node_id)
    return success(data={"deleted_count": result["deleted_count"]}, message=result.get("message"))


@router.post("/utility/score/{memory_id}", tags=["Memory Utilities"])
def score_memory(memory_id: int, service: MemoryUtilityService = Depends()):
    """对单条记忆进行效用评分。

    Args:
        memory_id: 记忆 ID

    Returns: 评分结果
    """
    return success(data=service.score_memory(memory_id))


@router.post("/utility/score-all", tags=["Memory Utilities"])
def score_all(service: MemoryUtilityService = Depends()):
    """对所有记忆进行批量效用评分。

    Args:
        service: 记忆工具服务

    Returns: 批量评分结果
    """
    return success(data=service.score_all())


@router.get("/utility/rankings", tags=["Memory Utilities"])
def utility_rankings(
    min_utility: float = Query(0.0),
    limit: int = Query(20, ge=1, le=200),
    service: MemoryUtilityService = Depends(),
):
    """获取效用评分排名。

    Args:
        min_utility: 最低效用分数筛选
        limit:       返回条目数上限

    Returns: 排名列表
    """
    return success(data=service.utility_rankings(min_utility=min_utility, limit=limit))


@router.post("/sleep/consolidate", tags=["Memory Utilities"])
def sleep_consolidate(service: MemoryUtilityService = Depends()):
    """执行睡眠模式记忆整合——压缩、去重、提升重要记忆。

    Args:
        service: 记忆工具服务

    Returns: 整合结果统计
    """
    return success(data=service.sleep_consolidate())


@router.get("/sleep/history", tags=["Memory Utilities"])
def sleep_history(service: MemoryUtilityService = Depends()):
    """获取睡眠模式整合的历史记录。

    Args:
        service: 记忆工具服务

    Returns: 历史记录列表
    """
    return success(data=service.sleep_history())
