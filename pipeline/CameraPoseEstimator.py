from typing import List, Tuple, Union

import cv2
import numpy
from config.config import ConfigStore
from vision_types import CameraPoseObservation, FiducialImageObservation, FiducialPoseObservation
from wpimath.geometry import *
import time

from pipeline.coordinate_systems import (openCvPoseToWpilib,
                                         wpilibTranslationToOpenCv)


class CameraPoseEstimator:
    def __init__(self) -> None:
        raise NotImplementedError

    def solve_camera_pose(self, image_observations: List[FiducialImageObservation], config_store: ConfigStore) -> Tuple[List[FiducialPoseObservation], Union[CameraPoseObservation, None]]:
        raise NotImplementedError


class MultiTargetCameraPoseEstimator(CameraPoseEstimator):
    def __init__(self) -> None:
        pass

    def solve_camera_pose(self, image_observations: List[FiducialImageObservation], config_store: ConfigStore) -> Tuple[List[FiducialPoseObservation], Union[CameraPoseObservation, None], float]:
        # Exit if no tag layout available
        if config_store.remote_config.tag_layout == None:
            return [], None, 0.0

        # Exit if no observations available
        if len(image_observations) == 0:
            return [], None, 0.0

        # Create set of object and image points
        fid_size = config_store.remote_config.fiducial_size_m
        all_object_points = []
        all_image_points = []
        tag_ids = []
        tag_poses: List[Pose3d] = []
        fiducial_observations: List[FiducialPoseObservation] = []

        solvepnp_start_time = 0.0

        for observation in image_observations:
            tag_pose = None
            for tag_data in config_store.remote_config.tag_layout["tags"]:
                if tag_data["ID"] == observation.tag_id:
                    tag_pose = Pose3d(
                        Translation3d(
                            tag_data["pose"]["translation"]["x"],
                            tag_data["pose"]["translation"]["y"],
                            tag_data["pose"]["translation"]["z"]
                        ),
                        Rotation3d(Quaternion(
                            tag_data["pose"]["rotation"]["quaternion"]["W"],
                            tag_data["pose"]["rotation"]["quaternion"]["X"],
                            tag_data["pose"]["rotation"]["quaternion"]["Y"],
                            tag_data["pose"]["rotation"]["quaternion"]["Z"]
                        )))
                    break
            if tag_pose == None:
                continue
            
            # Add object points by transforming from the tag center
            half_fid_size = fid_size / 2.0
            corner_0 = tag_pose + Transform3d(Translation3d(0, half_fid_size, -half_fid_size), Rotation3d())
            corner_1 = tag_pose + Transform3d(Translation3d(0, -half_fid_size, -half_fid_size), Rotation3d())
            corner_2 = tag_pose + Transform3d(Translation3d(0, -half_fid_size, half_fid_size), Rotation3d())
            corner_3 = tag_pose + Transform3d(Translation3d(0, half_fid_size, half_fid_size), Rotation3d())
            all_object_points += [
                wpilibTranslationToOpenCv(corner_0.translation()),
                wpilibTranslationToOpenCv(corner_1.translation()),
                wpilibTranslationToOpenCv(corner_2.translation()),
                wpilibTranslationToOpenCv(corner_3.translation())
            ]

            # Add image points from observation
            image_points = [
                [observation.corners[0][0][0], observation.corners[0][0][1]],
                [observation.corners[0][1][0], observation.corners[0][1][1]],
                [observation.corners[0][2][0], observation.corners[0][2][1]],
                [observation.corners[0][3][0], observation.corners[0][3][1]]
            ]
            all_image_points += image_points

            tag_ids.append(observation.tag_id)
            tag_poses.append(tag_pose)

            object_points = numpy.array([[-half_fid_size, half_fid_size, 0.0],
                                         [half_fid_size, half_fid_size, 0.0],
                                         [half_fid_size, -half_fid_size, 0.0],
                                         [-half_fid_size, -half_fid_size, 0.0]])
            try:
                solvepnp_start_time = time.time_ns()
                _, rvecs, tvecs, errors = cv2.solvePnPGeneric(object_points, numpy.array(image_points),
                                                              config_store.local_config.camera_matrix, config_store.local_config.distortion_coefficients, flags=cv2.SOLVEPNP_IPPE_SQUARE)
                solvepnp_solve_time = time.time_ns() - solvepnp_start_time
            except:
                continue

            # Calculate WPILib camera poses
            camera_to_tag_pose_0 = openCvPoseToWpilib(tvecs[0], rvecs[0])
            camera_to_tag_pose_1 = openCvPoseToWpilib(tvecs[1], rvecs[1])
            camera_to_tag_0 = Transform3d(camera_to_tag_pose_0.translation(), camera_to_tag_pose_0.rotation())
            camera_to_tag_1 = Transform3d(camera_to_tag_pose_1.translation(), camera_to_tag_pose_1.rotation())

            fiducial_observations.append(FiducialPoseObservation(observation.tag_id, camera_to_tag_0, errors[0][0], camera_to_tag_1, errors[1][0]))

        # Don't include a camera pose if there are no tags or we failed to resolve a tag pose
        if len(fiducial_observations) == 0:
            return fiducial_observations, None
        
        # Only one target, use result of IPPE Square
        if len(tag_ids) == 1:
            tag_to_camera_pose_0 = fiducial_observations[0].pose_0.inverse()
            camera_pose_0 = tag_poses[0].transformBy(tag_to_camera_pose_0)
            tag_to_camera_pose_1 = fiducial_observations[0].pose_1.inverse()
            camera_pose_1 = tag_poses[0].transformBy(tag_to_camera_pose_1)
            return fiducial_observations, CameraPoseObservation(tag_ids, camera_pose_0, fiducial_observations[0].error_0, camera_pose_1, fiducial_observations[0].error_1), solvepnp_solve_time

        # Run SolvePNP with all tags
        try:
            solvepnp_start_time = time.time_ns()
            _, rvecs, tvecs, errors = cv2.solvePnPGeneric(numpy.array(all_object_points), numpy.array(all_image_points),
                                                            config_store.local_config.camera_matrix, config_store.local_config.distortion_coefficients, flags=cv2.SOLVEPNP_SQPNP)
            solvepnp_solve_time = time.time_ns() - solvepnp_start_time
        except:
            return fiducial_observations, None, solvepnp_solve_time

        # Calculate WPILib camera pose
        camera_to_field_pose = openCvPoseToWpilib(tvecs[0], rvecs[0])
        camera_to_field = Transform3d(camera_to_field_pose.translation(), camera_to_field_pose.rotation())
        field_to_camera = camera_to_field.inverse()
        field_to_camera_pose = Pose3d(field_to_camera.translation(), field_to_camera.rotation())

        # Return result
        return fiducial_observations, CameraPoseObservation(tag_ids, field_to_camera_pose, errors[0][0], None, None), solvepnp_solve_time
