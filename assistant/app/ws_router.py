import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from assistant.app.ws_manager import connection_manager
from shared.auth import verify_token

logger = logging.getLogger(__name__)
router = APIRouter(tags=["websocket"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket 端点，用于实时双向通信。

    通过 token 验证用户身份，连接后接收 JSON 消息并交由连接管理器处理。

    Args:
        websocket: WebSocket 连接实例

    Returns:
        None
    """
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001)
        return
    try:
        payload = verify_token(token)
        user_id = int(payload["sub"])
    except Exception:
        await websocket.close(code=4001)
        return

    await connection_manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_json()
            logger.info("WS message from user %d: %s", user_id, data)
    except WebSocketDisconnect:
        await connection_manager.disconnect(websocket, user_id)
    except Exception:
        await connection_manager.disconnect(websocket, user_id)
