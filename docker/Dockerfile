FROM ubuntu:22.04

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app 

# No interaction when installing packages
ARG DEBIAN_FRONTEND=noninteractive

# Note: looks like the OPi's are running 3.10.6, but the subversion for default python in ubuntu 22.04 is 3.10.12
# python3.11 isn't needed here, but I'm scared to change stuff
# Install minimal prerequisites
RUN apt-get update && apt-get install -y cmake g++ wget unzip build-essential apt-utils git python3.11 python3-dev python3-numpy openssh-server
RUN apt-get install -y libavcodec-dev libavformat-dev libswscale-dev libgstreamer-plugins-base1.0-dev libgstreamer1.0-dev libgtk-3-dev

# Kick off SSH server if stuff breaks
RUN sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN useradd -m -s /bin/bash user
RUN echo "user:1701robocubs" | chpasswd
EXPOSE 22
ENTRYPOINT service ssh start && bash

# Download and unpack sources
RUN wget -O opencv.zip https://github.com/opencv/opencv/archive/4.x.zip
RUN wget -O opencv_contrib.zip https://github.com/opencv/opencv_contrib/archive/4.x.zip
RUN unzip opencv.zip
RUN unzip opencv_contrib.zip

# Make CMAKE build dir
RUN mkdir -p build
WORKDIR /usr/src/app/build

# Configure
RUN cmake -DBUILD_EXAMPLES=OFF -DBUILD_TESTS=OFF -DBUILD_PERF_TESTS=OFF -DWITH_GSTREAMER=ON -DOPENCV_EXTRA_MODULES_PATH=../opencv_contrib-4.x/modules ../opencv-4.x

# Build
RUN cmake --build .

# Do standard build and install so it's easier to grab the necessary python module
RUN make 
RUN make install