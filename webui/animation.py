import os
import json
import time
from adafruit_servokit import ServoKit
import sys
import RPi.GPIO as GPIO
import threading


def interpolate_keyframe(keyframes, index):
    lower = None
    higher = None
    for keyframe in keyframes:
        if keyframe["frameIndex"] < index:
            lower = keyframe
        if keyframe["frameIndex"] == index:
            return keyframe
        if keyframe["frameIndex"] > index:
            higher = keyframe
            break

    if lower is None:
        return {
            "frameIndex": index,
            "values": {key: value for key, value in higher["values"].items()},
        }

    if higher is None:
        return {
            "frameIndex": index,
            "values": {key: value for key, value in lower["values"].items()},
        }

    progress = (index - lower["frameIndex"]) / (
        higher["frameIndex"] - lower["frameIndex"]
    )

    return {
        "frameIndex": index,
        "values": {
            name: lower["values"][name]
            + (higher["values"][name] - lower["values"][name]) * progress
            for name in lower["values"].keys()
        },
    }


def bake(animation):
    # Ensure keyframes are sorted
    keyframes = sorted(
        animation["keyframes"], key=lambda keyframe: keyframe["frameIndex"]
    )

    return [
        interpolate_keyframe(keyframes, index)
        for index in range(animation["config"]["totalFrames"])
    ]


def add_frames(animation, factor):
    animation["config"]["fps"] *= factor
    animation["config"]["totalFrames"] *= factor

    for keyframe in animation["keyframes"]:
        keyframe["frameIndex"] *= factor


class AnimationPlayer:
    def __init__(self):
        self.kit = ServoKit(channels=16)

        self.servos = {
            0: {"min": 0, "max": 120, "step": 10, "name": "ALa"},
            1: {"min": 180, "max": 38, "step": -10, "name": "ALiR"},
            4: {"min": 140, "max": 28, "step": -10, "name": "ARaR"},
            5: {"min": 0, "max": 140, "step": 10, "name": "ARi"},
            3: {"min": 180, "max": 120, "step": -60, "name": "SLR"},
            7: {"min": 0, "max": 60, "step": 60, "name": "SR"},
            2: {"min": 0, "max": 180, "step": 60, "name": "BL"},
            6: {"min": 0, "max": 180, "step": 60, "name": "BRR"},
            8: {"min": 0, "max": 180, "step": 60, "name": "K"},
            14: {"min": 30, "max": 180, "step": 60, "name": "KnopfSchlange"},
            12: {"min": 0, "max": 60, "step": 60, "name": "KopfDrache"},
            11: {"min": 65, "max": 180, "step": 60, "name": "LangDrache"},
            13: {"min": 70, "max": 180, "step": 60, "name": "PflanzenDrache"},
            15: {"min": 0, "max": 180, "step": 60, "name": "FressDrache"},
            10: {"min": 130, "max": 150, "step": 60, "name": "WippDrache"},
            9: {"min": 0, "max": 180, "step": 60, "name": "DreiDrachen"},
        }

        self.gpios = {
            4: {"name": "1FlugDrache"},
            14: {"name": "Schwanzbeisser"},
            15: {"name": "Reiter"},
            17: {"name": "Reserve"},
            18: {"name": "HubAb"},
            27: {"name": "HubAuf"},
            22: {"name": "HubEin"},
            23: {"name": "2Flugdrachen"},
            25: {"name": "LedRot"},
            11: {"name": "LedGruen"},
        }

        self.servo_map = {
            servo["name"]: servo_idx for servo_idx, servo in self.servos.items()
        }
        self.gpio_map = {
            gpio["name"]: gpio_pin for gpio_pin, gpio in self.gpios.items()
        }

        GPIO.setmode(GPIO.BCM)
        for gpio_pin in self.gpios.keys():
            GPIO.setup(gpio_pin, GPIO.OUT)

        self.running = False
        self.current_index = 0
        self.animation_thread = None

    def start_animation(self, animation):
        if self.running:
            raise ValueError("Already Running")
        else:
            self.running = True
            self.animation_thread = threading.Thread(
                target=self.play_animation, args=(animation,)
            )
            self.animation_thread.start()

    def stop_animation(self):
        self.running = False
        if self.animation_thread is not None:
            self.animation_thread.join()

    def play_animation(self, animation):
        total_frames = animation["config"]["totalFrames"]

        fps = animation["config"]["fps"]

        last_frame = animation["keyframes"][-1]
        new_first = {
            "frameIndex": last_frame["frameIndex"] - animation["config"]["totalFrames"],
            "values": last_frame["values"],
        }
        first_frame = animation["keyframes"][0]
        new_last = {
            "frameIndex": first_frame["frameIndex"]
            + animation["config"]["totalFrames"],
            "values": last_frame["values"],
        }

        animation["keyframes"] = [new_first] + animation["keyframes"] + [new_last]

        for keyframe in animation["keyframes"]:
            keyframe["time"] = keyframe["frameIndex"] / animation["config"]["fps"]

        animation_duration = total_frames / fps

        current_time = animation["config"]["currentFrameIndex"] / animation["config"]["fps"]
        last_ts = time.time()
        while self.running:
            current_ts = time.time()
            delta = current_ts - last_ts
            current_time += delta
            last_ts = current_ts

            while current_time > animation_duration:
                current_time -= animation_duration

            self.current_index = int(current_time * fps)

            frame_before = None
            frame_after = None

            for keyframe in animation["keyframes"]:
                if keyframe["time"] <= current_time:
                    frame_before = keyframe
                if keyframe["time"] > current_time:
                    frame_after = keyframe
                    break

            assert frame_before is not None and frame_after is not None

            interpolation_time = frame_after["time"] - frame_before["time"]
            progressed_time = current_time - frame_before["time"]
            progress = progressed_time / interpolation_time

            values = {
                name: frame_before["values"][name] * (1 - progress)
                + frame_after["values"][name] * progress
                for name in frame_before["values"].keys()
            }

            for servo_name, angle in values.items():
                min_angle = 0  # min(servo_info["min"], servo_info["max"])
                max_angle = 180  # max(servo_info["min"], servo_info["max"])

                if servo_name in ["SR", "ALiR", "ARaR", "BRR"]:
                    angle = 180 - angle

                angle = min(max_angle, max(min_angle, angle))

                if servo_name in self.servo_map:
                    self.kit.servo[self.servo_map[servo_name]].angle = angle
                else:
                    GPIO.output(self.gpio_map[servo_name], angle > 90)

    def get_current_frame(self):
        return self.current_index
