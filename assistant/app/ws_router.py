import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from assistant.app.ws_manager import connection_manager
from shared.auth import verify_token

logger = logging.getLogger(__name__)
router = APIRouter(tags=["websocket"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
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
