"""
State machine implementation for the Marionette control system.
Handles different states and transitions between them.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict

from diorama.pose import PoseEstimator
from diorama.animation import KeyFrameAnimation
import time

from datetime import datetime

def log_animation():
    # Get the current date and time in ISO format
    current_datetime = datetime.now().isoformat()
    
    # Open the log file in append mode and write the current datetime
    with open('./animation-log.log', 'a') as log_file:
        log_file.write(current_datetime + '\n')


class State(Enum):
    NO_OBSERVERS = "no_observers"
    OBSERVER = "observer"
    WAVE = "wave"
    WAVE_BACK = "wave_back"
    START_ANIMATION = "start_animation"
    TEST = "test"


@dataclass
class StateContext:
    pose_estimator: PoseEstimator
    animations: Dict[str, KeyFrameAnimation]
    gpio_state: Dict[str, bool]


class StateMachine:
    def __init__(self, context: StateContext):
        self.context = context
        self.state = State.NO_OBSERVERS
        self.state_start_time = time.time()

    def transition(self, new_state: State) -> None:
        self.state = new_state
        self.state_start_time = time.time()

    def time_in_state(self) -> float:
        return time.time() - self.state_start_time

    def update(self) -> None:
        # Handle LED states based on freigabe switch
        if not self.context.gpio_state["freigabe"]:
            self.context.animations["off"].animate_strength(0)
            self.context.animations["led_red"].animate_strength(0)
            self.context.animations["led_green"].animate_strength(1)
        else:
            self.context.animations["off"].animate_strength(1)
            self.context.animations["led_red"].animate_strength(1)
            self.context.animations["led_green"].animate_strength(0)

        # Check for test state transition
        if self.context.gpio_state["test"] and self.state != State.TEST:
            self.transition(State.TEST)
            self.context.animations["test"].current_time = 0

        handlers = {
            State.NO_OBSERVERS: self._handle_no_observers,
            State.OBSERVER: self._handle_observer,
            State.WAVE: self._handle_wave,
            State.WAVE_BACK: self._handle_wave_back,
            State.START_ANIMATION: self._handle_start_animation,
            State.TEST: self._handle_test,
        }

        handlers[self.state]()

    def _handle_no_observers(self) -> None:
        anims = self.context.animations
        anims["head"].animate_strength(0)
        anims["wave"].animate_strength(0)
        anims["dances"].animate_strength(0)

        if (
            self.context.pose_estimator.presence_time > 1
            or self.context.gpio_state["start"]
        ):
            self.transition(State.OBSERVER)

    def _handle_observer(self) -> None:
        anims = self.context.animations
        anims["head"].animate_strength(1)
        anims["wave"].animate_strength(0)
        anims["dances"].animate_strength(0)
        anims["test"].animate_strength(0)

        if (
            self.context.pose_estimator.wave_time > 0
            or self.context.pose_estimator.presence_time > 12
            or self.context.gpio_state["start"]
        ):
            self.transition(State.WAVE_BACK)
        elif self.time_in_state() > 2:
            self.transition(State.WAVE)
        elif self.context.pose_estimator.presence_time == 0:
            self.transition(State.NO_OBSERVERS)

    def _handle_wave(self) -> None:
        self.context.animations["wave"].animate_strength(1)
        if self.time_in_state() > 2:
            self.transition(State.OBSERVER)
        if (
            self.context.pose_estimator.wave_time > 0
            or self.context.gpio_state["start"]
        ):
            self.transition(State.WAVE_BACK)

    def _handle_wave_back(self) -> None:
        self.context.animations["wave"].animate_strength(1)
        if (
            self.context.pose_estimator.wave_time == 0
            and self.context.pose_estimator.presence_time < 12
        ) and not self.context.gpio_state["start"]:
            self.transition(State.OBSERVER)

        if self.time_in_state() > 2:
            self.context.animations["dances"].start()
            self.transition(State.START_ANIMATION)
            log_animation()

    def _handle_start_animation(self) -> None:
        self.context.animations["close_mouth"].animate_strength(0)
        self.context.animations["dances"].animate_strength(1)
        if not self.context.animations["dances"].is_running:
            self.context.animations["close_mouth"].current_time = 0
            self.context.animations["close_mouth"].animate_strength(1)
            if self.context.pose_estimator.presence_time > 0:
                self.context.pose_estimator.presence_time = 0.01
                self.transition(State.OBSERVER)
            else:
                self.transition(State.NO_OBSERVERS)

    def _handle_test(self) -> None:
        self.context.animations["close_mouth"].animate_strength(0)
        self.context.animations["test"].animate_strength(1)
        self.context.animations["led_green_blink"].animate_strength(1)
        if not self.context.gpio_state["test"]:
            self.context.animations["close_mouth"].current_time = 0
            self.context.animations["close_mouth"].animate_strength(1)
            self.context.animations["test"].animate_strength(0)
            self.context.animations["led_green_blink"].animate_strength(0)
            self.transition(State.NO_OBSERVERS)
