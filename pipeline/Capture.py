import dataclasses
import sys
import time
import os
from typing import Tuple

import cv2
import numpy
from config.config import ConfigStore

import subprocess


class Capture:
    """Interface for receiving camera frames."""

    def __init__(self) -> None:
        raise NotImplementedError

    def get_frame(self, config_store: ConfigStore) -> Tuple[bool, cv2.Mat]:
        """Return the next frame from the camera."""
        raise NotImplementedError

    @classmethod
    def _config_changed(cls, config_a: ConfigStore, config_b: ConfigStore) -> bool:
        if config_a == None and config_b == None:
            return False
        if config_a == None or config_b == None:
            return True

        remote_a = config_a.remote_config
        remote_b = config_b.remote_config

        return remote_a.camera_id != remote_b.camera_id or remote_a.camera_resolution_width != remote_b.camera_resolution_width or remote_a.camera_resolution_height != remote_b.camera_resolution_height or remote_a.camera_auto_exposure != remote_b.camera_auto_exposure or remote_a.camera_exposure != remote_b.camera_exposure or remote_a.camera_gain != remote_b.camera_gain

class StaticCapture(Capture):
    """Read from an image directory, and returns the frames (Usually for testing)"""
    _src: list = []
    _last_change: float = 0.0
    _index: int = -1

    def __init__(self, s) -> None:
        self._src = s

    def get_frame(self, config_store: ConfigStore) -> Tuple[bool, cv2.Mat]:
        c = time.time()
        if c - self._last_change > 5.0:
            self._last_change = c
            if self._index == len(self._src) - 1:
                self._index = -1
            self._index += 1

        image = cv2.imread(self._src[self._index])
        retval = 1
        return retval, image


class DefaultCapture(Capture):
    """"Read from camera with default OpenCV config."""

    def __init__(self) -> None:
        pass

    _video = None
    _last_config: ConfigStore

    def get_frame(self, config_store: ConfigStore) -> Tuple[bool, cv2.Mat]:
        if self._video != None and self._config_changed(self._last_config, config_store):
            print("Restarting capture session")
            self._video.release()
            self._video = None

        if self._video == None:
            self._video = cv2.VideoCapture(config_store.remote_config.camera_id)
            self._video.set(cv2.CAP_PROP_FRAME_WIDTH, config_store.remote_config.camera_resolution_width)
            self._video.set(cv2.CAP_PROP_FRAME_HEIGHT, config_store.remote_config.camera_resolution_height)
            self._video.set(cv2.CAP_PROP_AUTO_EXPOSURE, config_store.remote_config.camera_auto_exposure)
            self._video.set(cv2.CAP_PROP_EXPOSURE, config_store.remote_config.camera_exposure)
            self._video.set(cv2.CAP_PROP_GAIN, config_store.remote_config.camera_gain)

        self._last_config = config_store

        retval, image = self._video.read()
        return retval, image


class GStreamerCapture(Capture):
    """"Read from camera with GStreamer."""

    def __init__(self) -> None:
        pass

    _video = None
    _last_config: ConfigStore

    def get_id_for_buskey(self, config_store: ConfigStore) -> int:
        bus_keys = config_store.remote_config.bus_keys
        valid_ids = config_store.remote_config.valid_ids
        if bus_keys == "" or valid_ids == []:
            return config_store.remote_config.camera_id
        prefix = config_store.local_config.device_id.strip("CubVision")
        bus = ""
        for key in bus_keys:
            if prefix in key:
                bus = key.split(":")[1]
        
        if bus == "":
            return -1
        
        print(f"Looking for {bus} in {prefix}")

        for id in valid_ids:
            p = subprocess.run(["v4l2-ctl", f"-d{id}", "-D"], capture_output=True, text=True)
            if bus in p.stdout:
                return id
        return -1


    def get_frame(self, config_store: ConfigStore) -> Tuple[bool, cv2.Mat]:
        if self._video != None and self._config_changed(self._last_config, config_store):
            print("Config changed, stopping capture session")
            self._video.release()
            self._video = None
            time.sleep(2)

        if self._video == None:
            if config_store.remote_config.camera_id == -1:
                print("No camera ID, waiting to start capture session")
            else:
                # If we're running on Darwin it's probably for testing/simulation
                if os.uname().sysname != 'Darwin':
                    """
                    gst-launch-1.0 v4l2src device=/dev/video0 extra_controls="c,exposure_auto=0,exposure_absolute=0,gain=0,sharpness=0,brightness=0" ! image/jpeg,format=MJPG,width=1280,height=720 ! jpegdec ! video/x-raw ! appsink drop=1
                    """
                    camera_id = self.get_id_for_buskey(config_store)
                    if camera_id != -1:
                        print("Starting capture session")
                        self._video = cv2.VideoCapture("gst-launch-1.0 v4l2src device=/dev/video" + str(camera_id) + " extra_controls=\"c,exposure_auto=" + str(config_store.remote_config.camera_auto_exposure) + ",exposure_absolute=" + str(
                            config_store.remote_config.camera_exposure) + ",gain=" + str(config_store.remote_config.camera_gain) + ",sharpness=0,brightness=0\" ! image/jpeg,format=MJPG,width=" + str(config_store.remote_config.camera_resolution_width) + ",height=" + str(config_store.remote_config.camera_resolution_height) + " ! jpegdec ! video/x-raw ! appsink drop=1", cv2.CAP_GSTREAMER)
                    else:
                        print("Could not get camera ID")
                else:
                    print("Detected Darwin, using default OpenCV pipeline")
                    self._video = cv2.VideoCapture(config_store.remote_config.camera_id)
                print("Capture session ready")

        self._last_config = ConfigStore(dataclasses.replace(config_store.local_config),
                                        dataclasses.replace(config_store.remote_config))

        if self._video != None:
            retval, image = self._video.read()
            if not retval:
                print("Capture session failed, restarting")
                self._video.release()
                self._video = None  # Force reconnect
            return retval, image
        else:
            return False, cv2.Mat(numpy.ndarray([]))
