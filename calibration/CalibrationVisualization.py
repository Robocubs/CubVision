import cv2
import numpy as np
import pathlib

REFERENCE_FILENAME = str(pathlib.Path(__file__).parent.resolve()) + "/base1.jpg"

def get_distorted_reference_image(camera_matrix: np.ndarray, distortion_coefficients: np.ndarray) -> np.ndarray:
    reference_img = cv2.imread(REFERENCE_FILENAME, 0)
    if reference_img.size == 0:
        return None
    distorted_img = cv2.undistort(reference_img, camera_matrix, distortion_coefficients)
    return distorted_img

