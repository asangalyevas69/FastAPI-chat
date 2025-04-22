import json

import aiofiles
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()
chat_history = []


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


@app.get("/")
async def get_page() -> HTMLResponse:
    async with aiofiles.open("templates/index.html", mode="r") as f:
        content = await f.read()
        return HTMLResponse(
            content=content,
            media_type="text/html",
        )


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    global chat_history
    await manager.connect(websocket)

    for message in chat_history:
        await manager.send_personal_message(json.dumps(message), websocket)

    try:
        while True:
            data = await websocket.receive_text()
            chat_history.append({"from": client_id, "message": data})
            # await manager.send_personal_message(f"You wrote: {data}", websocket)
            await manager.broadcast(json.dumps({"from": client_id, "message": data}))
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        if len(manager.active_connections) == 0:
            chat_history.clear()