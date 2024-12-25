import time
import cv2
import threading
import mediapipe as mp
import numpy as np


class PoseEstimator:
    def __init__(self, fps=10):
        self.fps = fps
        self.running = False
        self.detecting = True
        self.pose_detector = mp.solutions.pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            enable_segmentation=False,
            min_detection_confidence=0.7,
        )

        self.image = None
        self.pose = None
        self.pose_x = None
        self._thread = None

        self.presence_time = 0
        self.wave_time = 0

    def _run(self):
        cap = cv2.VideoCapture(0)
        last = time.time()
        while self.running and cap.isOpened():
            now = time.time()
            delta = now - last
            last = now

            ret, frame = cap.read()
            if self.detecting:
                if not ret:
                    break

                self.image = cv2.flip(frame, 1)

                # Convert the BGR image to RGB
                # self.image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # Perform pose detection
                self.pose = self.pose_detector.process(self.image)
                self._update_pose_time(delta)
                self._update_wave_time(delta)

        cap.release()

    def _update_pose_time(self, delta):
        pose_x = None
        if self.pose and self.pose.pose_landmarks:
            for landmark in self.pose.pose_landmarks.landmark:
                if (
                    landmark
                    == self.pose.pose_landmarks.landmark[
                        mp.solutions.pose.PoseLandmark.NOSE
                    ]
                ):
                    pose_x = landmark.x

        self.pose_x = pose_x
        if self.pose_x is not None:
            self.presence_time += delta
        else:
            self.presence_time = 0

    def _update_wave_time(self, delta):
        if self.pose and self.pose.pose_landmarks:
            left_wrist = self.pose.pose_landmarks.landmark[
                mp.solutions.pose.PoseLandmark.LEFT_WRIST
            ]
            right_wrist = self.pose.pose_landmarks.landmark[
                mp.solutions.pose.PoseLandmark.RIGHT_WRIST
            ]
            left_shoulder = self.pose.pose_landmarks.landmark[
                mp.solutions.pose.PoseLandmark.LEFT_SHOULDER
            ]
            right_shoulder = self.pose.pose_landmarks.landmark[
                mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER
            ]
            shoulder_height = (left_shoulder.y + right_shoulder.y) / 2

            if (left_wrist.y < shoulder_height) or (right_wrist.y < shoulder_height):
                self.wave_time += delta
            else:
                self.wave_time = 0
        else:
            self.wave_time = 0

    def __enter__(self):
        self.running = True
        self._thread = threading.Thread(target=self._run)
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.running = False
        if self._thread is not None:
            self._thread.join()

    def get_image(self, annotate=True):
        out = np.copy(self.image)
        if self.pose is not None and annotate:
            mp.solutions.drawing_utils.draw_landmarks(
                out,
                self.pose.pose_landmarks,
                mp.solutions.pose.POSE_CONNECTIONS,
                mp.solutions.drawing_styles.get_default_pose_landmarks_style(),
            )
        return out
