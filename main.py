#!/usr/bin/env python3
"""
Main module for the Marionette control system.
Handles GPIO setup, pose estimation, and web UI integration.
"""

import json
import time
import threading
from typing import Dict, Any

import RPi.GPIO

from webui import webui
from marionette.pose import PoseEstimator
from marionette.io import ServoKitIoController
from marionette.animation import WebUIAnimation
from marionette.orchestrator import Orchestrator


def setup_inputs(pin_config: Dict[str, Any]) -> None:
    """
    Configure GPIO input pins with pull-down resistors.

    Args:
        pin_config: Dictionary containing GPIO pin configurations
    """
    for pin in pin_config:
        RPi.GPIO.setup(
            int(pin),
            RPi.GPIO.IN,
            pull_up_down=RPi.GPIO.PUD_DOWN,
        )


def start_webserver(host: str, port: int) -> None:
    """
    Start the web UI server in a non-blocking manner.

    Args:
        host: Host address to bind the server to
        port: Port number for the server
    """
    webui.run(host=host, port=port)


def main() -> None:
    """Main program loop handling marionette control and animations."""
    # Load configuration
    with open("config/main.json") as f:
        config = json.load(f)

    # Initialize GPIO inputs
    setup_inputs(config["gpio"]["inputs"])

    # Initialize pose estimation and I/O controller
    with (
        PoseEstimator() as pose_estimator,
        ServoKitIoController.from_config(config["gpio"]) as io_controller,
    ):

        orchestrator = Orchestrator(io_controller, 20)

        # Configure web UI animation
        webui.marionette_animator = WebUIAnimation(priority=10, strength=1)
        orchestrator.add(webui.marionette_animator)

        # Set up pose estimator for web UI
        webui.pose_estimator = pose_estimator

        # Start web server in a separate thread
        server_thread = threading.Thread(
            target=start_webserver, args=("0.0.0.0", 5001), daemon=True
        )
        server_thread.start()

        # Main animation loop
        previous_time = time.time()
        while True:
            current_time = time.time()
            delta_time = current_time - previous_time
            previous_time = current_time

            orchestrator.tick(delta_time)


if __name__ == "__main__":
    main()
