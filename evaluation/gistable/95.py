#!/bin/env python3
#-*- encoding: utf-8 -*-

import cv2
import numpy as np

# start this:
# ffmpeg -i /dev/video0 -f mpegts udp://localhost:1337
# ffmpeg -i rtsp://... -f mpegts udp://localhost:1337

cameraCapture = cv2.VideoCapture('udp://localhost:1337')
cv2.namedWindow('MyWindow')

print('Showing camera feed. Click window or press any key to stop.')

while True:
    success, frame = cameraCapture.read()
    cv2.imshow('MyWindow', frame)

    if cv2.waitKey(1) & 0xff == ord("q"):
        break

cv2.destroyWindow('MyWindow')
cameraCapture.release()
