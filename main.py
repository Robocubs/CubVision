import sys
import time
from typing import Union

import cv2
import ntcore

from calibration.CalibrationCommandSource import (CalibrationCommandSource,
                                                  NTCalibrationCommandSource)
from calibration.CalibrationSession import CalibrationSession
from config.config import ConfigStore, LocalConfig, RemoteConfig
from config.ConfigSource import ConfigSource, FileConfigSource, NTConfigSource
from output.OutputPublisher import NTPacketPublisher, OutputPublisher
from output.overlay_util import *
from output.StreamServer import MjpegServer
from pipeline.CameraPoseEstimator import MultiTargetCameraPoseEstimator
from pipeline.Capture import DefaultCapture, GStreamerCapture, StaticCapture
from pipeline.FiducialDetector import ArucoFiducialDetector
from pipeline.PoseEstimator import SquareTargetPoseEstimator
from datetime import date
import pathlib


DEMO_ID = 29

if __name__ == "__main__":
    print(f"--- Launching CubVision @ {date.today()}")
    config = ConfigStore(LocalConfig(), RemoteConfig())
    local_config_source: ConfigSource = FileConfigSource()
    remote_config_source: ConfigSource = NTConfigSource()
    calibration_command_source: CalibrationCommandSource = NTCalibrationCommandSource()

    capture = DefaultCapture()
    fiducial_detector = ArucoFiducialDetector(cv2.aruco.DICT_APRILTAG_36h11)
    camera_pose_estimator = MultiTargetCameraPoseEstimator()
    tag_pose_estimator = SquareTargetPoseEstimator()
    output_publisher: OutputPublisher = NTPacketPublisher()
    stream_server = MjpegServer()
    calibration_session = CalibrationSession()

    local_config_source.update(config)
    ntcore.NetworkTableInstance.getDefault().setServer(config.local_config.server_ip)
    ntcore.NetworkTableInstance.getDefault().startClient4(config.local_config.device_id)

    started_server = False
    temp = 0
    thermal_zone_handle = None
    try: thermal_zone_handle = open("/sys/class/thermal/thermal_zone1/temp", "r")
    except: pass
    frame_count = 0
    latency_sum = 0
    last_print = 0
    was_calibrating = False
    last_frame_capture_time = time.time()
    start_time = time.time_ns() // 1_000_000

    # More benchmarking
    fiducial_detection_time = last_frame_capture_time
    solvepnp_solve_time = last_frame_capture_time

    while True:
        output_publisher.set_heartbeat(start_time)
        if config.remote_config.should_stream and not started_server:
            stream_server.start(config)
            started_server = True
        remote_config_source.update(config)
        timestamp = time.time()
        success, image = capture.get_frame(config)
        if not success:
            time.sleep(0.5)
            continue

        fps = None
        latency = None
        frame_count += 1
        frame_capture_time = time.time()
        if frame_capture_time - last_print > 1:
            # There is no perf impact when we measure temperature. In fact, this is quicker than the previous way of measuring which I'm embarassed of
            if thermal_zone_handle != None:
                thermal_zone_handle.seek(0)
                temp = int(int(thermal_zone_handle.read().strip("\n")) / 1000)
            last_print = frame_capture_time
            fps = frame_count
            # print("Running at", frame_count, "fps, avg latency", int(latency_sum / frame_count), "ms")
            frame_count = 0
            latency_sum = 0

        if calibration_command_source.get_calibrating(config):
            # Calibration mode
            was_calibrating = True
            calibration_session.process_frame(image, calibration_command_source.get_capture_flag(config))

        elif was_calibrating:
            # Finish calibration, and set the final frame before we die
            image = calibration_session.finish(True)
            if started_server:
                stream_server.set_frame(image, fps, latency)
            
            cv2.imwrite(str(pathlib.Path(__file__).parent.resolve()) + "/calibration/distorted_reference.jpg", image)
            sys.exit(0)

        elif config.local_config.has_calibration:
            # Normal mode
            start_detection = time.time()
            image_observations = fiducial_detector.detect_fiducials(image, config)
            fiducial_detection_time = time.time() - start_detection
            [overlay_image_observation(image, x) for x in image_observations]
            fiducial_pose_observations, camera_pose_observation, solvepnp_solve_time = camera_pose_estimator.solve_camera_pose(
                [x for x in image_observations if x.tag_id != DEMO_ID], config)
            demo_image_observations = [x for x in image_observations if x.tag_id == DEMO_ID]
            demo_pose_observation: Union[FiducialPoseObservation, None] = None
            if len(demo_image_observations) > 0:
                demo_pose_observation = tag_pose_estimator.solve_fiducial_pose(demo_image_observations[0], config)
            latency = (time.time() - frame_capture_time) * 1000
            latency_sum += latency
            output_publisher.send(config, timestamp, fiducial_pose_observations, camera_pose_observation, demo_pose_observation, fps, latency, temp)
            output_publisher.send_perf(fiducial_detection_time, solvepnp_solve_time)

        else:
            # No calibration
            print("No calibration found")
            time.sleep(0.5)

        last_frame_capture_time = frame_capture_time
        if started_server:
            stream_server.set_frame(image, fps, latency)
