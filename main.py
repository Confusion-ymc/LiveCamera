import asyncio

import uvicorn

from fastapi import FastAPI, WebSocket, Form
from starlette.requests import Request
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from starlette.websockets import WebSocketDisconnect
from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError

from core import Camera

camera = Camera()
camera.start()
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/")
async def get(request: Request, password: str = Form(...)):
    if password == 'ymc4399':
        return templates.TemplateResponse("live.html", {"request": request})
    else:
        return templates.TemplateResponse("login.html", {"request": request})


@app.websocket("/live")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    camera.global_users.append(websocket)
    try:
        while True:
            if camera.frame is None:
                await asyncio.sleep(0.1)
                continue
            await websocket.send_text(camera.frame)
            await asyncio.sleep(1 / camera.FPS)
    except ConnectionClosedOK:
        pass
    except WebSocketDisconnect:
        pass
    except ConnectionClosedError:
        pass
    finally:
        print('停止发送')
        camera.global_users.remove(websocket)


if __name__ == "__main__":
    uvicorn.run('main:app', host="0.0.0.0", port=4399)
