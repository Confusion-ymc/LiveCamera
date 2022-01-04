FROM python:3.7.6

WORKDIR /code/

RUN apt-get update -y
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple
RUN python -m pip install --upgrade pip
ARG OPENCV_VERSION=4.3.0
ARG NUMPY_VERSION=1.18.4

RUN apt-get update && apt-get -y install --no-install-recommends \
	build-essential \
	cmake \
	gfortran \
	libjpeg-dev \
	libatlas-base-dev \
	libavcodec-dev \
	libavformat-dev \
	libgtk2.0-dev \
	libgtk-3-dev \
	libswscale-dev \
	libtiff-dev \
	libv4l-dev \
	libx264-dev \
	libxvidcore-dev \
	pkg-config \
	wget
RUN pip wheel numpy==${NUMPY_VERSION}
RUN pip install numpy-*.whl
RUN wget https://github.com/opencv/opencv/archive/${OPENCV_VERSION}.tar.gz && \
	tar xf ${OPENCV_VERSION}.tar.gz
WORKDIR /code/opencv-${OPENCV_VERSION}/build
RUN cmake -D CMAKE_BUILD_TYPE=RELEASE \
	-D CMAKE_INSTALL_PREFIX=_install \
	-D ENABLE_NEON=ON \
	-D ENABLE_VFPV3=ON \
	-D BUILD_TESTS=OFF \
	-D OPENCV_ENABLE_NONFREE=ON \
	-D INSTALL_PYTHON_EXAMPLES=OFF \
	-D BUILD_EXAMPLES=OFF .. && \
	make -j16
RUN make install


ADD requirements.txt /code/

RUN pip install -r requirements.txt
ADD . /code



CMD ["python3", "-u", "main.py"]

