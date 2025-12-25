#!/usr/bin/env python3
"""
Main module for the Marionette control system.
Handles GPIO setup, pose estimation, and web UI integration.
"""
import os
import json
import time
import threading
from typing import Dict, Any
import argparse
import socket
import RPi.GPIO as GPIO
from webui import webui
from diorama.pose import PoseEstimator
from diorama.io import ServoKitIoController
from diorama.animation import (
    WebUIAnimation,
    KeyFrameAnimation,
    MultiKeyframeAnimation,
)
from diorama.orchestrator import Orchestrator
from utils.state import StateMachine, StateContext


def get_local_ip():
    """Get the local IP address of the machine."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
        s.close()
        return ip_address
    except Exception:
        return None


def setup_inputs(pin_config: Dict[str, Any]) -> None:
    """
    Configure GPIO input pins with pull-down resistors.
    Args:
        pin_config: Dictionary containing GPIO pin configurations
    """
    for pin in pin_config.values():
        GPIO.setup(
            int(pin),
            GPIO.IN,
            pull_up_down=GPIO.PUD_DOWN,
        )


def create_animations(
    config: Dict, pose_estimator: PoseEstimator
) -> Dict[str, KeyFrameAnimation]:
    """Create and return all animations used by the system."""
    animations = {}
    # Web UI animation
    animations["webui"] = WebUIAnimation(priority=50, strength=0)
    # Idle animation
    animations["idle"] = KeyFrameAnimation.from_path(
        config["animations"]["idle"], priority=0, strength=1
    )
    # Observer
    animations["observer"] = KeyFrameAnimation.from_path(
        config["animations"]["observer"], priority=1, strength=0
    )

    # Check if we have split config for dances, if not fallback or create default
    dances_open_path = config["animations"].get("dances_open", "animations/dances_open")
    dances_closed_path = config["animations"].get(
        "dances_closed", "animations/dances_closed"
    )

    # Ensure directories exist
    if not os.path.exists(dances_open_path):
        os.makedirs(dances_open_path)
    if not os.path.exists(dances_closed_path):
        os.makedirs(dances_closed_path)

    animations["dances_open"] = MultiKeyframeAnimation.from_path(
        dances_open_path,
        priority=11,
        strength=0,
        animation_duration=45,
    )
    animations["dances_closed"] = MultiKeyframeAnimation.from_path(
        dances_closed_path,
        priority=11,
        strength=0,
        animation_duration=45,
    )
    animations["off"] = KeyFrameAnimation.from_path(
        config["animations"]["off"], priority=100, strength=1, strength_speed=1
    )
    animations["led_red"] = KeyFrameAnimation.from_path(
        config["animations"]["led"]["red"],
        priority=1000,
        strength=0,
        strength_speed=100,
    )
    animations["led_green"] = KeyFrameAnimation.from_path(
        config["animations"]["led"]["green"],
        priority=1000,
        strength=0,
        strength_speed=100,
    )
    animations["led_green_blink"] = KeyFrameAnimation.from_path(
        config["animations"]["led"]["green_blink"],
        priority=1001,
        strength=0,
        strength_speed=100,
    )
    animations["test"] = KeyFrameAnimation.from_path(
        config["animations"]["test"], priority=200, strength=0
    )
    print(config["animations"]["test"])
    return animations


def main() -> None:
    """Main program loop handling marionette control and animations."""
    parser = argparse.ArgumentParser(description="Process some arguments.")
    parser.add_argument(
        "--config",
        type=str,
        default="config/default.json",
        help="Path to the configuration file (default: config/default.json)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Port for the web UI (default: 5001)",
    )
    args = parser.parse_args()
    # Load configuration
    with open(args.config) as f:
        config = json.load(f)
    # Initialize GPIO
    setup_inputs(config["gpio"]["inputs"])
    # Initialize pose estimation and I/O controller
    min_confidence = config.get("gpio", {}).get("min_detection_confidence", 0.8)
    with (
        PoseEstimator(min_detection_confidence=min_confidence) as pose_estimator,
        ServoKitIoController.from_config(config["gpio"]) as io_controller,
    ):
        # Create orchestrator
        orchestrator = Orchestrator(io_controller, 20)
        # Create animations
        animations = create_animations(config, pose_estimator)
        # Add animations to orchestrator
        for animation in animations.values():
            orchestrator.add(animation)
        # Create state machine
        state_context = StateContext(
            pose_estimator=pose_estimator,
            animations=animations,
            gpio_state={},
            config=config,
        )
        state_machine = StateMachine(state_context)
        # Set up web UI
        webui.config_path = args.config
        webui.marionette_animator = animations["webui"]
        webui.pose_estimator = pose_estimator
        webui.state_machine = state_machine

        local_ip = get_local_ip()
        if local_ip:
            webui.config["LOCAL_URL"] = f"http://{local_ip}:{args.port}"
            print(f"* Access the web UI at: {webui.config['LOCAL_URL']}")

        # Start web server in a separate thread
        server_thread = threading.Thread(
            target=webui.run, args=("0.0.0.0", args.port), daemon=True
        )
        server_thread.start()
        # Main animation loop
        previous_time = time.time()
        while True:
            current_time = time.time()
            delta_time = current_time - previous_time
            previous_time = current_time
            # Update GPIO state
            state_context.gpio_state = {
                "freigabe": GPIO.input(config["gpio"]["inputs"]["freigabe"])
                == GPIO.HIGH,
                "test": GPIO.input(config["gpio"]["inputs"]["test"]) == GPIO.HIGH,
                "start": GPIO.input(config["gpio"]["inputs"]["start"]) == GPIO.HIGH,
            }
            # Update state machine and animations
            state_machine.update()
            orchestrator.tick(delta_time)


if __name__ == "__main__":
    main()
