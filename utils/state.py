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
from utils.time_utils import is_store_open, get_default_schedule


def log_animation():
    # Get the current date and time in ISO format
    current_datetime = datetime.now().isoformat()

    # Open the log file in append mode and write the current datetime
    with open("./animation-log.log", "a") as log_file:
        log_file.write(current_datetime + "\n")


class State(Enum):
    NO_OBSERVERS = "no_observers"
    OBSERVER = "observer"
    START_ANIMATION = "start_animation"
    TEST = "test"


@dataclass
class StateContext:
    pose_estimator: PoseEstimator
    animations: Dict[str, KeyFrameAnimation]
    gpio_state: Dict[str, bool]
    config: Dict


class StateMachine:
    def __init__(self, context: StateContext):
        self.context = context
        self.state = State.NO_OBSERVERS
        self.state_start_time = time.time()
        self.freigabe_off_start_time = None

    def transition(self, new_state: State) -> None:
        self.state = new_state
        self.state_start_time = time.time()

    def time_in_state(self) -> float:
        return time.time() - self.state_start_time

    def update(self) -> None:
        # Handle LED states based on freigabe switch
        freigabe_config_timeout = self.context.config.get("gpio", {}).get(
            "timeout", 1
        )  # Minutes
        freigabe_active = self.context.gpio_state["freigabe"]

        if freigabe_active:
            if self.freigabe_off_start_time is None:
                self.freigabe_off_start_time = time.time()

            # Check if timeout exceeded
            elapsed_minutes = (time.time() - self.freigabe_off_start_time) / 60
            if elapsed_minutes > freigabe_config_timeout:
                freigabe_active = False
        else:
            self.freigabe_off_start_time = None

        if not freigabe_active:
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
            State.START_ANIMATION: self._handle_start_animation,
            State.TEST: self._handle_test,
        }

        handlers[self.state]()

    def _handle_no_observers(self) -> None:
        anims = self.context.animations
        anims["observer"].animate_strength(0)

        anims["dances_open"].animate_strength(0)
        anims["dances_closed"].animate_strength(0)

        presence_notice_time = self.context.config.get("gpio", {}).get(
            "presence_notice_time", 3
        )
        if (
            self.context.pose_estimator.presence_time > presence_notice_time
            or self.context.gpio_state["start"]
        ):
            self.transition(State.OBSERVER)

    def _handle_observer(self) -> None:
        anims = self.context.animations
        anims["observer"].animate_strength(1)

        presence_trigger_time = self.context.config.get("gpio", {}).get(
            "presence_trigger_time", 15
        )
        if (
            self.context.pose_estimator.presence_time > presence_trigger_time
            or self.context.gpio_state["start"]
        ):
            log_animation()

            # Determine which animation set to use
            schedule = self.context.config.get("opening_hours", get_default_schedule())
            is_open = is_store_open(schedule)

            target_anim_key = "dances_open" if is_open else "dances_closed"

            self.context.animations[target_anim_key].start()
            self.transition(State.START_ANIMATION)
        elif self.context.pose_estimator.presence_time == 0:
            self.transition(State.NO_OBSERVERS)

    def _handle_start_animation(self) -> None:
        # Check if any dance animation is running
        dances_running = False
        for key in ["dances_open", "dances_closed"]:
            if key in self.context.animations:
                anim = self.context.animations[key]
                if anim.is_running:
                    anim.animate_strength(1)
                    dances_running = True
                else:
                    pass

        if not dances_running:
            if self.context.pose_estimator.presence_time > 0:
                self.context.pose_estimator.presence_time = 0.01
                self.transition(State.OBSERVER)
            else:
                self.transition(State.NO_OBSERVERS)

    def _handle_test(self) -> None:
        self.context.animations["test"].animate_strength(1)
        self.context.animations["led_green_blink"].animate_strength(1)
        if not self.context.gpio_state["test"]:
            self.context.animations["test"].animate_strength(0)
            self.context.animations["led_green_blink"].animate_strength(0)
            self.transition(State.NO_OBSERVERS)
