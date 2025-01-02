"""Real-time offline pose estimation using MediaPipe.

This module provides a threaded pose estimation implementation using OpenCV
and MediaPipe frameworks for real-time human pose detection and tracking.
"""

import logging
from threading import Thread
import time
from typing import Optional

import cv2
import mediapipe as mp
import numpy as np
from numpy.typing import NDArray

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class PoseEstimator:
    """A threaded real-time pose estimation class using MediaPipe.

    This class handles webcam capture and pose detection in a separate thread,
    tracking presence time and wave gestures.

    Attributes:
        fps: Target frames per second for pose detection
        running: Flag indicating if the pose detection thread is active
        detecting: Flag to enable/disable pose detection processing
    """

    def __init__(self, fps: int = 10) -> None:
        """Initialize the PoseEstimator.

        Args:
            fps: Target frames per second for pose detection. Defaults to 10.
        """
        self.fps = fps
        self.running: bool = False
        self.detecting: bool = True

        self._pose_detector = mp.solutions.pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            enable_segmentation=False,
            min_detection_confidence=0.7,
        )

        self.image: Optional[NDArray] = None
        self.pose: Optional[mp.solutions.pose.Pose] = None
        self.pose_x: Optional[float] = None
        self._thread: Optional[Thread] = None

        self.presence_time: float = 0.0
        self.wave_time: float = 0.0

        # Fisheye Lense Correction
        fx = 542.0
        fy = 393.0
        cx = 320.0
        cy = 240.0
        k1 = -0.14
        k2 = -0.36
        p1 = 0.03
        p2 = -0.04

        # Camera matrix and distortion coefficients
        self.K = np.array([[fx, 0, cx], [0, fy, cy], [0, 0, 1]])
        self.D = np.array([k1, k2, p1, p2])

        self.rectify_maps = None

    def _run(self) -> None:
        """Main thread function handling webcam capture and pose detection."""
        while self.running:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                logger.error("Could not open Webcam, will try again in 10 seconds")
                time.sleep(10)
                continue

            try:
                last_time = time.time()
                while self.running and cap.isOpened():
                    current_time = time.time()
                    delta = current_time - last_time
                    last_time = current_time

                    success, frame = cap.read()
                    if not success:
                        logger.error("Could not read frame from Webcam")
                        break

                    if self.detecting:
                        self._process_frame(frame, delta)
            finally:
                cap.release()

    def _process_frame(self, frame: NDArray, delta: float) -> None:
        """Process a single frame for pose detection.

        Args:
            frame: Input frame from webcam
            delta: Time elapsed since last frame
        """
        if self.rectify_maps is None:
            h, w = frame.shape[:2]
            new_K = cv2.fisheye.estimateNewCameraMatrixForUndistortRectify(
                self.K, self.D, (w, h), np.eye(3)
            )
            self.rectify_maps = cv2.fisheye.initUndistortRectifyMap(
                self.K, self.D, np.eye(3), new_K, (w, h), cv2.CV_32FC1
            )

        self.image = cv2.remap(
            frame,
            self.rectify_maps[0],
            self.rectify_maps[1],
            interpolation=cv2.INTER_LINEAR,
        )[50:440, 108:550]

        self.pose = self._pose_detector.process(self.image)
        self._update_pose_time(delta)
        self._update_wave_time(delta)

    def _update_pose_time(self, delta: float) -> None:
        """Update the time a pose has been detected.

        Args:
            delta: Time elapsed since last update
        """
        pose_x = None
        if self.pose and self.pose.pose_landmarks:
            nose_landmark = self.pose.pose_landmarks.landmark[
                mp.solutions.pose.PoseLandmark.NOSE
            ]
            pose_x = 1 - nose_landmark.x

        self.pose_x = pose_x
        if self.pose_x is not None:
            self.presence_time += delta
        else:
            self.presence_time = 0

    def _update_wave_time(self, delta: float) -> None:
        """Update the time a waving gesture has been detected.

        Args:
            delta: Time elapsed since last update
        """
        if not (self.pose and self.pose.pose_landmarks):
            self.wave_time = 0
            return

        landmarks = self.pose.pose_landmarks.landmark
        shoulder_height = (
            landmarks[mp.solutions.pose.PoseLandmark.LEFT_SHOULDER].y
            + landmarks[mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER].y
        ) / 2

        wrists_above_shoulders = (
            landmarks[mp.solutions.pose.PoseLandmark.LEFT_WRIST].y < shoulder_height
            or landmarks[mp.solutions.pose.PoseLandmark.RIGHT_WRIST].y < shoulder_height
        )

        if wrists_above_shoulders:
            self.wave_time += delta
        else:
            self.wave_time = 0

    def get_image(self, annotate: bool = True) -> Optional[NDArray]:
        """Get the latest processed image.

        Args:
            annotate: Whether to draw pose landmarks on the image

        Returns:
            Annotated image if available, None otherwise
        """
        if self.image is None:
            return None

        out = np.copy(self.image)
        if self.pose is not None and self.pose.pose_landmarks and annotate:
            mp.solutions.drawing_utils.draw_landmarks(
                out,
                self.pose.pose_landmarks,
                mp.solutions.pose.POSE_CONNECTIONS,
                mp.solutions.drawing_styles.get_default_pose_landmarks_style(),
            )
        return out

    def __enter__(self) -> "PoseEstimator":
        """Start the pose estimation thread."""
        logger.info("Starting Pose Estimator")
        self.running = True
        self._thread = Thread(target=self._run, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Stop the pose estimation thread."""
        logger.info("Stopping Pose Estimator")
        self.running = False
        if self._thread is not None:
            self._thread.join()
