import math
import time
from typing import List, Union

import ntcore
from config.config import ConfigStore
from output.Packet import Packet
from vision_types import CameraPoseObservation, FiducialPoseObservation


class OutputPublisher:
    def send(self, config_store: ConfigStore, timestamp: float, fiducial_pose_observations: List[FiducialPoseObservation], observation: Union[CameraPoseObservation, None], demo_observation: Union[FiducialPoseObservation, None], fps: Union[int, None], latency: float) -> None:
        raise NotImplementedError


class NTPacketPublisher():
    _init_complete: bool = False
    _observations_pub: ntcore.RawPublisher
    _demo_observations_pub: ntcore.RawPublisher
    _fps_pub: ntcore.IntegerPublisher
    _heartbeat_pub: ntcore.IntegerPublisher
    _temp_pub: ntcore.IntegerPublisher
    _latency_pub: ntcore.IntegerPublisher

    def set_heartbeat(self, start_time):
        if self._init_complete:
            self._heartbeat_pub.set(time.time_ns() // 1_000_000 - start_time)

    def send(self, config_store: ConfigStore, timestamp: float, fiducial_pose_observations: List[FiducialPoseObservation], observation: Union[CameraPoseObservation, None], demo_observation: Union[FiducialPoseObservation, None], fps: Union[int, None], latency: float, temp: int) -> None:
        # Initialize publishers on first call
        if not self._init_complete:
            nt_table = ntcore.NetworkTableInstance.getDefault().getTable(
                "CubVision/" + config_store.local_config.device_id + "/output")
            self._observations_pub = nt_table.getRawTopic("observations").publish("ObservationsPacket",
                ntcore.PubSubOptions(periodic=0, sendAll=True, keepDuplicates=True))
            self._demo_observations_pub = nt_table.getRawTopic("demo_observations").publish("FiducialPoseObservation",
                ntcore.PubSubOptions(periodic=0, sendAll=True, keepDuplicates=True))
            self._fps_pub = nt_table.getIntegerTopic("fps").publish()
            self._heartbeat_pub = nt_table.getIntegerTopic("heartbeat").publish(ntcore.PubSubOptions(keepDuplicates=False))
            self._temp_pub = nt_table.getIntegerTopic("temp").publish()
            self._latency_pub = nt_table.getIntegerTopic("latency").publish()
            self._init_complete = True

        self._latency_pub.set(int(latency))

        # Build the observation
        observation_packet = Packet()

        observation_packet.encodeDouble(latency)

        observation_packet.encode8(len(fiducial_pose_observations))
        for fiducial_observation in fiducial_pose_observations:
            observation_packet.encode8(fiducial_observation.tag_id)
            if fiducial_observation.error_0 < fiducial_observation.error_1:
                observation_packet.encodeDouble(fiducial_observation.error_0)
                observation_packet.encodeTransform(fiducial_observation.pose_0)
                observation_packet.encodeDouble(fiducial_observation.error_1)
                observation_packet.encodeTransform(fiducial_observation.pose_1)
            else:
                observation_packet.encodeDouble(fiducial_observation.error_1)
                observation_packet.encodeTransform(fiducial_observation.pose_1)
                observation_packet.encodeDouble(fiducial_observation.error_0)
                observation_packet.encodeTransform(fiducial_observation.pose_0)

        if observation == None:
            observation_packet.encode8(0)
        else:
            observation_packet.encode8(len(observation.tag_ids))
            for tag_id in observation.tag_ids:
                observation_packet.encode8(tag_id)
            observation_packet.encodeDouble(observation.error_0)
            observation_packet.encodeTransform(observation.pose_0)
            if observation.error_1 != None and observation.pose_1 != None:
                observation_packet.encodeDouble(observation.error_1)
                observation_packet.encodeTransform(observation.pose_1)

        # Build demo observation
        demo_observation_packet = Packet()
        if demo_observation != None:
            demo_observation_packet.encode8(demo_observation.tag_id)
            demo_observation_packet.encodeDouble(demo_observation.error_0)
            demo_observation_packet.encodeTransform(demo_observation.pose_0)
            demo_observation_packet.encodeDouble(demo_observation.error_1)
            demo_observation_packet.encodeTransform(demo_observation.pose_1)

        # Send data
        self._observations_pub.set(bytes(observation_packet.getData()))
        self._demo_observations_pub.set(bytes(demo_observation_packet.getData()), math.floor(timestamp * 1000000))
        if fps != None:
            self._fps_pub.set(fps)

        self._temp_pub.set(temp)

#Deprecated, we use the publisher above
class NTOutputPublisher(OutputPublisher):
    _init_complete: bool = False
    _observations_pub: ntcore.DoubleArrayPublisher
    _demo_observations_pub: ntcore.DoubleArrayPublisher
    _fps_pub: ntcore.IntegerPublisher

    def send(self, config_store: ConfigStore, timestamp: float, fiducial_pose_observations: Union[FiducialPoseObservation, None], observation: Union[CameraPoseObservation, None], demo_observation: Union[FiducialPoseObservation, None], fps: Union[int, None], latency: float) -> None:
        # Initialize publishers on first call
        if not self._init_complete:
            nt_table = ntcore.NetworkTableInstance.getDefault().getTable(
                "CubVision/" + config_store.local_config.device_id + "/output")
            self._observations_pub = nt_table.getDoubleArrayTopic("observations").publish(
                ntcore.PubSubOptions(periodic=0, sendAll=True, keepDuplicates=True))
            self._demo_observations_pub = nt_table.getDoubleArrayTopic("demo_observations").publish(
                ntcore.PubSubOptions(periodic=0, sendAll=True, keepDuplicates=True))
            self._fps_pub = nt_table.getIntegerTopic("fps").publish()
            self._init_complete = True

        # Send data
        if fps != None:
            self._fps_pub.set(fps)
        observation_data: List[float] = [0, latency]
        demo_observation_data: List[float] = []
        if observation != None:
            observation_data[0] = 1
            observation_data.append(observation.error_0)
            observation_data.append(observation.pose_0.translation().X())
            observation_data.append(observation.pose_0.translation().Y())
            observation_data.append(observation.pose_0.translation().Z())
            observation_data.append(observation.pose_0.rotation().getQuaternion().W())
            observation_data.append(observation.pose_0.rotation().getQuaternion().X())
            observation_data.append(observation.pose_0.rotation().getQuaternion().Y())
            observation_data.append(observation.pose_0.rotation().getQuaternion().Z())
            if observation.error_1 != None and observation.pose_1 != None:
                observation_data[0] = 2
                observation_data.append(observation.error_1)
                observation_data.append(observation.pose_1.translation().X())
                observation_data.append(observation.pose_1.translation().Y())
                observation_data.append(observation.pose_1.translation().Z())
                observation_data.append(observation.pose_1.rotation().getQuaternion().W())
                observation_data.append(observation.pose_1.rotation().getQuaternion().X())
                observation_data.append(observation.pose_1.rotation().getQuaternion().Y())
                observation_data.append(observation.pose_1.rotation().getQuaternion().Z())
            for tag_id in observation.tag_ids:
                observation_data.append(tag_id)
        if demo_observation != None:
            demo_observation_data.append(demo_observation.error_0)
            demo_observation_data.append(demo_observation.pose_0.translation().X())
            demo_observation_data.append(demo_observation.pose_0.translation().Y())
            demo_observation_data.append(demo_observation.pose_0.translation().Z())
            demo_observation_data.append(demo_observation.pose_0.rotation().getQuaternion().W())
            demo_observation_data.append(demo_observation.pose_0.rotation().getQuaternion().X())
            demo_observation_data.append(demo_observation.pose_0.rotation().getQuaternion().Y())
            demo_observation_data.append(demo_observation.pose_0.rotation().getQuaternion().Z())
            demo_observation_data.append(demo_observation.error_1)
            demo_observation_data.append(demo_observation.pose_1.translation().X())
            demo_observation_data.append(demo_observation.pose_1.translation().Y())
            demo_observation_data.append(demo_observation.pose_1.translation().Z())
            demo_observation_data.append(demo_observation.pose_1.rotation().getQuaternion().W())
            demo_observation_data.append(demo_observation.pose_1.rotation().getQuaternion().X())
            demo_observation_data.append(demo_observation.pose_1.rotation().getQuaternion().Y())
            demo_observation_data.append(demo_observation.pose_1.rotation().getQuaternion().Z())
        self._observations_pub.set(observation_data, math.floor(timestamp * 1000000))
        self._demo_observations_pub.set(demo_observation_data, math.floor(timestamp * 1000000))
