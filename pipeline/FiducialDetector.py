from typing import List

import cv2
from config.config import ConfigStore
from vision_types import FiducialImageObservation


class FiducialDetector:
    def __init__(self) -> None:
        raise NotImplementedError

    def detect_fiducials(self, image: cv2.Mat, config_store: ConfigStore) -> List[FiducialImageObservation]:
        raise NotImplementedError


class ArucoFiducialDetector(FiducialDetector):
    def __init__(self, dictionary_id) -> None:
        self._params = cv2.aruco.DetectorParameters()
        self._params.useAruco3Detection = True
        self._params.minMarkerLengthRatioOriginalImg = 0.00 #τi
        self._detector = cv2.aruco.ArucoDetector(cv2.aruco.getPredefinedDictionary(dictionary_id), self._params)

    def detect_fiducials(self, image: cv2.Mat, config_store: ConfigStore) -> List[FiducialImageObservation]:
        self._detector.setDetectorParameters(self._params)
        corners, ids, _ = self._detector.detectMarkers(image)
        if len(corners) == 0:
            self._params.minMarkerLengthRatioOriginalImg = 0.00
            return []
        # Equation 6 from "Speeded Up Detection of Squared Fiducial Markers"
        # self._params.minMarkerLengthRatioOriginalImg = (1.0 - 0.1)
        return [FiducialImageObservation(id[0], corner) for id, corner in zip(ids, corners)]
