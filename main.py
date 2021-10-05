import asyncio
import base64
import datetime
import threading
import time
import cv2
import uvicorn
from fastapi.responses import JSONResponse
from fastapi import FastAPI, WebSocket, Form
from starlette.requests import Request
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
import gzip

from starlette.websockets import WebSocketDisconnect
from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
global_users = []


def open_camera():
    camera = cv2.VideoCapture(0)
    camera.set(3, 1920)
    camera.set(4, 1080)
    for i in range(5):
        if camera.isOpened():
            print('打开摄像头成功')
            return camera
        else:
            time.sleep(1)
    else:
        # 摄像头打开失败
        print('摄像头打开失败')
        return None


def update_video_frame(fast_app):
    while True:
        if not global_users:
            time.sleep(1)
            continue
        else:
            camera = open_camera()
            if camera is None:
                continue
            try:
                while global_users:
                    fast_app.state.frame = image_to_send_data(camera)
            except Exception as e:
                print(e)
                time.sleep(5)
            finally:
                camera.release()
        print('关闭摄像头')


def gzip_compress(buf):
    return gzip.compress(buf)


def draw_face_site(img):
    # 转灰度图
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # 进行人脸检测
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    # 绘制人脸矩形框
    for (x, y, w, h) in faces:
        img = cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
    return img


def image_to_send_data(camera):
    try:
        for i in range(100):
            _, frame = camera.read()
            if frame is None:
                print('丢失帧')
                continue
            else:
                # frame = draw_face_site(frame)
                # text = 'Width: ' + str(camera.get(3)) + ' Height:' + str(camera.get(4))
                date_str = str(datetime.datetime.utcnow()+datetime.timedelta(hours=8)).split('.')[0]
                font = cv2.FONT_HERSHEY_SIMPLEX

                x = 10
                y = 35
                frame = cv2.putText(frame, date_str, (x, y), font, 1,
                                    (0, 0, 0), 2, cv2.LINE_AA)

                text = 'Online: {}'.format(len(global_users))
                frame = cv2.putText(frame, text, (x, y + 40), font, 1,
                                    (0, 0, 0), 2, cv2.LINE_AA)

                image = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])[1]
                base64_data = base64.b64encode(image)
                s = 'data:image/jpeg;base64,'.encode() + base64_data
                return gzip_compress(s)
    except Exception as e:
        return None


# @app.get('/users/')
# async def users(request: Request):
#     return JSONResponse({'data': len(global_users)})


@app.get("/")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/")
async def get(request: Request, password: str = Form(...)):
    if password == 'ymc4399':
        return templates.TemplateResponse("live.html", {"request": request})
    else:
        return templates.TemplateResponse("login.html", {"request": request})


# @app.get("/live")
# async def get(request: Request):
#     return templates.TemplateResponse("live.html", {"request": request})


@app.websocket("/live")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    global_users.append(websocket)
    try:
        while True:
            if websocket.app.state.frame is None:
                await asyncio.sleep(0.1)
                continue
            await websocket.send_bytes(websocket.app.state.frame)
            await asyncio.sleep(0.01)
    except ConnectionClosedOK:
        pass
    except WebSocketDisconnect:
        pass
    except ConnectionClosedError:
        pass
    finally:
        print('停止发送')
        global_users.remove(websocket)


def register_task(fast_app: FastAPI) -> None:
    @app.on_event('startup')
    async def startup_event():
        fast_app.state.frame = None
        threading.Thread(target=update_video_frame, args=(fast_app,), daemon=True).start()


register_task(app)

if __name__ == "__main__":
    uvicorn.run('main:app', host="0.0.0.0", port=4399)
