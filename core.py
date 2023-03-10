from io import BytesIO

import cv2
from PIL import ImageGrab, Image
import gzip
import numpy as np
import base64
import datetime
import time

import threading


class Camera(threading.Thread):
    def __init__(self):
        super(Camera, self).__init__()
        self.daemon = True
        self.frame = None
        self.FPS = 30
        self.frame_generate = self.camera_frame
        self.global_users = []
        self.face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

    @staticmethod
    def desktop_frame():
        while True:
            img = ImageGrab.grab()
            frame = cv2.cvtColor(np.array(img), cv2.COLOR_BGR2RGB)
            # frame = cv2.resize(frame, (int(im.width / 2), int(im.height / 2)))
            yield frame

    @staticmethod
    def camera_frame():
        camera = cv2.VideoCapture(0)
        camera.set(3, 1920)
        camera.set(4, 1080)
        for i in range(10):
            if camera.isOpened():
                print('打开摄像头成功')
                while True:
                    _, frame = camera.read()
                    yield frame
            else:
                time.sleep(3)
        else:
            # 摄像头打开失败
            print('摄像头打开失败')
            return None

    @staticmethod
    def file_frame():
        file_path = '1.mp4'
        camera = cv2.VideoCapture(file_path)
        while True:
            ret, frame = camera.read()
            if not ret:
                break
            yield frame

    def run(self):
        while True:
            try:
                while self.global_users:
                    for frame in self.frame_generate():
                        self.frame = self.to_base64data(frame)
                        time.sleep(1 / self.FPS)
                        if not self.global_users:
                            break
            except Exception as e:
                print(e)
            time.sleep(2)

    @staticmethod
    def gzip_compress(buf):
        return gzip.compress(buf)

    def draw_face_site(self, img):
        # 转灰度图
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # 进行人脸检测
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
        # 绘制人脸矩形框
        for (x, y, w, h) in faces:
            img = cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
        return img

    @staticmethod
    def cv2_base64(image):
        base64_str = cv2.imencode('.jpg', image)[1].tostring()
        base64_str = base64.b64encode(base64_str)
        return base64_str

    @staticmethod
    def pil_base64(image):
        img_buffer = BytesIO()
        image.save(img_buffer, format='JPEG')
        byte_data = img_buffer.getvalue()
        base64_str = base64.b64encode(byte_data)
        img_buffer.close()
        return base64_str

    def to_base64data(self, frame):
        frame = self.draw_face_site(frame)
        x = 10
        y = 35
        font = cv2.FONT_HERSHEY_SIMPLEX
        red = (220, 74, 52)
        date_str = str(datetime.datetime.utcnow() + datetime.timedelta(hours=8)).split('.')[0]
        frame = cv2.putText(frame, date_str, (x, y), font, 1, red, 2, cv2.LINE_AA)

        text = 'Online: {}'.format(len(self.global_users))
        frame = cv2.putText(frame, text, (x, y + 40), font, 1, red, 2, cv2.LINE_AA)

        # image = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])[1]
        pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        s = 'data:image/jpeg;base64,' + self.pil_base64(pil_image).decode()  # base64_data.decode()
        return s
        # return self.gzip_compress(s)
