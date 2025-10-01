import logging
from uuid import UUID
from fastapi import WebSocket


logger = logging.getLogger(__name__)

class WebSocketService:
    def __init__(self):
        self.ws_connections: dict[UUID, WebSocket] = {}

        ## WebSocket stuff

    def record_ws_connection(
        self,
        user_id: UUID,
        websocket: WebSocket
    ) -> None:
        self.ws_connections[user_id] = websocket
        return

    def check_ws_connection(
        self,
        user_id: UUID
    ) -> bool:
        logger.info(f"Current websocket connections: {self.ws_connections}")
        return user_id in self.ws_connections

    async def close_ws_connection(
        self,
        user_id: UUID
    ) -> None:
        logger.info(f"Closing websocket of {user_id}")
        if user_id not in self.ws_connections:
            raise Exception()
        await self.ws_connections[user_id].close()
        return
