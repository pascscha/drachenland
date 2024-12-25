import json
import time
import sys
import cv2
import threading
import mediapipe as mp
from marionette.io import ServoKitIoController
from enum import Enum, auto
import RPi.GPIO as GPIO
import random
import os


class Animation:
    def __init__(self, priority=5, strength=1, strength_speed=1):
        self.priority = priority
        self.strength = strength
        self.target_strength = strength
        self.strength_speed = strength_speed

    def animate_strength(self, target_strength):
        self.target_strength = target_strength

    def tick(self, delta):
        step = self.strength_speed * delta

        # print("step", step, self.speed, delta_time)
        if self.strength < self.target_strength:
            self.strength = min(self.strength + step, self.target_strength)
        elif self.strength > self.target_strength:
            self.strength = max(self.strength - step, self.target_strength)


class KeyFrameAnimation(Animation):
    def __init__(self, animation, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.current_time = 0

        self.duration = (
            animation["config"]["totalFrames"] * 1 / animation["config"]["fps"]
        )

        self.keyframes = animation["keyframes"]

        last_frame = self.keyframes[-1]
        new_first = {
            "frameIndex": last_frame["frameIndex"] - animation["config"]["totalFrames"],
            "values": last_frame["values"],
        }
        first_frame = self.keyframes[0]
        new_last = {
            "frameIndex": first_frame["frameIndex"]
            + animation["config"]["totalFrames"],
            "values": last_frame["values"],
        }

        self.keyframes = [new_first] + self.keyframes + [new_last]

        for keyframe in self.keyframes:
            keyframe["time"] = keyframe["frameIndex"] / animation["config"]["fps"]

        self.repetitions = None
        self.fps = animation["config"]["fps"]

    def tick(self, delta):
        super().tick(delta)
        self.current_time += delta

        while self.current_time >= self.duration:
            self.current_time -= self.duration
            if self.repetitions is not None:
                self.repetitions -= 1

        if self.repetitions is not None and self.repetitions <= 0:
            self.animate_strength(0)

        frame_before = None
        frame_after = None

        for keyframe in self.keyframes:
            if keyframe["time"] <= self.current_time:
                frame_before = keyframe
            if keyframe["time"] > self.current_time:
                frame_after = keyframe
                break

        assert frame_before is not None and frame_after is not None

        interpolation_time = frame_after["time"] - frame_before["time"]
        progressed_time = self.current_time - frame_before["time"]
        progress = progressed_time / interpolation_time

        return {
            name: frame_before["values"][name] * (1 - progress)
            + frame_after["values"][name] * progress
            for name in frame_before["values"].keys()
        }


class HeadAnimation(Animation):
    def __init__(self, pose_estimator, left, neutral, right, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.left = left
        self.neutral = neutral
        self.right = right
        self.pose_estimator = pose_estimator
        self.last_pose = neutral

    def interpolate_values(self, x):
        interpolated = {}
        for key in self.left:
            interpolated[key] = x * self.right[key] + (1 - x) * self.left[key]
        return interpolated

    def tick(self, delta):
        super().tick(delta)

        target = self.last_pose

        if self.pose_estimator.pose_x is not None:
            self.animate_strength(1)
            target = self.interpolate_values(self.pose_estimator.pose_x)
        else:
            self.animate_strength(0)

        self.last_pose = target
        return target


class IdleAnimation(Animation):
    def __init__(self, keyframe_animations, *args, expected_start=15, **kwargs):
        super().__init__(*args, **kwargs)
        self.keyframe_animations = keyframe_animations
        self.expected_start = expected_start
        self.active = {animation: False for animation in self.keyframe_animations}

    def tick(self, delta):
        super().tick(delta)
        inactive = [
            animation for animation, is_active in self.active.items() if not is_active
        ]

        self.expected_start / delta
        # print(delta / self.expected_start)

        if len(inactive) > 0 and random.random() < delta / self.expected_start:
            activated_animation = random.choice(inactive)
            self.active[activated_animation] = True

            activated_animation.current_time = 0
            activated_animation.repetitions = 1

        active = [
            animation for animation, is_active in self.active.items() if is_active
        ]
        out = {}
        for animation in active:
            values = animation.tick(delta)
            for key, value in values.items():
                out[key] = value
            if animation.repetitions <= 0:
                self.active[animation] = False

        return out


class WebUIAnimation(Animation):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.slider_values = {}
        self.animation = None

    def start_animation(self, animation_data):
        self.animation = KeyFrameAnimation(animation_data)
        self.animation.current_time = (
            animation_data["config"]["currentFrameIndex"]
            / animation_data["config"]["fps"]
        )

    def get_current_frame(self):
        if self.animation is None:
            raise ValueError("Not Playing")
        else:
            return int(self.animation.current_time * self.animation.fps)

    def stop_animation(self):
        self.animation = None

    def tick(self, delta):
        super().tick(delta)
        if self.animation is not None:
            return self.animation.tick(delta)
        else:
            return self.slider_values
