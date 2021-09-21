FROM python:3.7.6

WORKDIR /code/

RUN apt-get update -y
RUN apt install libgl1-mesa-glx -y

ADD requirements.txt /code/
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple
RUN pip install -r requirements.txt
ADD . /code



CMD ["python3", "-u", "main.py"]

