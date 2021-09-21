import asyncio
import base64
import threading
import time
import cv2
import uvicorn

from fastapi import FastAPI, WebSocket
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
                    _, img_bgr = camera.read()
                    if img_bgr is None:
                        print('丢失帧')
                    else:
                        fast_app.state.frame = image_to_send_data(img_bgr)
            except Exception as e:
                print(e)
                time.sleep(5)
            finally:
                camera.release()
        print('关闭摄像头')


@app.get("/")
async def get(request: Request):
    return templates.TemplateResponse("live.html", {"request": request})


@app.get("/live")
async def get(request: Request):
    return templates.TemplateResponse("live.html", {"request": request})


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


def image_to_send_data(frame):
    try:
        # frame = draw_face_site(frame)
        image = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])[1]
        base64_data = base64.b64encode(image)
        s = 'data:image/jpeg;base64,'.encode() + base64_data
        return gzip_compress(s)
    except Exception as e:
        return None


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

# url = 'rtmp://148676.livepush.myqcloud.com/live/ymc?txSecret=4913fbcff287c2895bc3cf7c65c7122c&txTime=6113823F'
# ffmpeg -f avfoundation -video_size 1280x720 -framerate 30 -i 0 -vf scale=400:-2 -vcodec libx264 -preset ultrafast -f flv 'rtmp://148676.livepush.myqcloud.com/live/ymc?txSecret=4913fbcff287c2895bc3cf7c65c7122c&txTime=6113823F'


if __name__ == "__main__":
    uvicorn.run('main:app', host="0.0.0.0", port=4399)
