#!/bin/sh

# SHOULD BE RUN ON HOST MACHINE

echo "Enter OrangePi IP Address: "

read IP
scp -r ./docker/lib/* root@$IP:/usr/local/lib
scp -r ./docker/cv2 root@$IP:/usr/local/lib/python3.10/dist-packages/
scp -r ./* root@$IP:/home/orangepi/CubVision/