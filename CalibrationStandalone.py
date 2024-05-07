import sys
import time
from typing import Union

import cv2

from calibration.CalibrationSession import CalibrationSession
from config.config import ConfigStore, LocalConfig, RemoteConfig
from config.ConfigSource import ConfigSource, FileConfigSource
from output.overlay_util import *
from output.StreamServer import MjpegServer
from pipeline.Capture import DefaultCapture
import pathlib

config = ConfigStore(LocalConfig(), RemoteConfig())
capture = DefaultCapture()
local_config_source: ConfigSource = FileConfigSource()
stream_server = MjpegServer()
calibration_session = CalibrationSession()

try:
    config.remote_config.camera_id = int(sys.argv[3])
except IndexError:
    print("python3 CalibrationStandalone.py [config] [calibration] [cameraID]")
    sys.exit(1)

config.remote_config.camera_resolution_width = 1600
config.remote_config.camera_resolution_height = 1200
config.remote_config.camera_auto_exposure = 0
config.remote_config.camera_exposure = 200


local_config_source.update(config)
stream_server.start(config)

captured: int = 0
frame_count = 0
last_print = 0
last_frame_capture_time = time.time()

while captured < 40:
    timestamp = time.time()
    success, image = capture.get_frame(config)
    if not success:
        time.sleep(0.5)
        continue
    fps = None
    frame_count += 1
    frame_capture_time = time.time()
    if frame_capture_time - last_print > 1:
        last_print = frame_capture_time
        fps = frame_count
        print("Running at", frame_count, "fps,", image.shape[0], image.shape[1], "res,", captured, "captured frames")
        frame_count = 0
    save = False
    if timestamp - last_frame_capture_time > 1:
        save = True
        last_frame_capture_time = timestamp
        captured += 1
    calibration_session.process_frame(image, save)
    stream_server.set_frame(image, fps, captured)

image = calibration_session.finish(True)
stream_server.set_frame(image, fps, captured)

cv2.imwrite(str(pathlib.Path(__file__).parent.resolve()) + "/calibration/distorted_reference.jpg", image)
sys.exit(0)
