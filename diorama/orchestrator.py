"""Orchestrator which connects State Machine, Pose estimation with Animations"""

import logging
import traceback
from typing import Dict, List
from diorama.animation import Animation
from diorama.io import IoController

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class Orchestrator:
    """Manages and coordinates multiple animations for servo control."""

    def __init__(self, io_controller: IoController, fps: float) -> None:
        """Initialize the Orchestrator.

        Args:
            io_controller: Controller for handling servo I/O operations.
            fps: Frames per second for animation updates.
        """
        self._io_controller = io_controller
        self._fps = fps
        self._animations: List[Animation] = []

    def add(self, animation: Animation) -> None:
        """Add an animation to the orchestrator.

        Args:
            animation: Animation object to be added.
        """
        try:
            self._animations.append(animation)
            logger.info(f"Added animation: {animation.__class__.__name__}")
        except Exception as exc:
            logger.error("Failed to add animation", exc_info=True)
            raise

    def remove(self, animation: Animation) -> None:
        """Remove an animation from the orchestrator.

        Args:
            animation: Animation object to be removed.

        Raises:
            ValueError: If the animation is not found.
        """
        try:
            self._animations.remove(animation)
            logger.info(f"Removed animation: {animation.__class__.__name__}")
        except ValueError:
            logger.error(
                f"Failed to remove animation {animation.__class__.__name__}: not found",
                exc_info=True,
            )
            raise
        except Exception as exc:
            logger.error("Unexpected error while removing animation", exc_info=True)
            raise

    def tick(self, delta: float) -> None:
        """Update all animations and apply their effects to servos.

        Args:
            delta: Time elapsed since last tick in seconds.
        """
        try:
            # Sort animations by priority once
            self._animations.sort(key=lambda x: x.priority)

            out_values: Dict[str, float] = {}

            # Process each animation
            for animation in self._animations:
                try:
                    values = animation.tick(delta)

                    for name, value in values.items():
                        if name not in out_values:
                            servo = self._io_controller.get_servo(name)
                            if servo is None:
                                logger.warning(f"Servo {name} not found")
                                continue
                            out_values[name] = servo.position

                        # Calculate weighted position
                        out_values[name] = (
                            animation.strength * value
                            + (1 - animation.strength) * out_values[name]
                        )

                except Exception:
                    logger.error(
                        f"Error processing animation {animation.__class__.__name__}",
                        exc_info=True,
                    )
                    logger.debug(f"Stack trace: {traceback.format_exc()}")
                    continue

            # Update servo positions
            for name, value in out_values.items():
                try:
                    servo = self._io_controller.get_servo(name)
                    if servo is not None:
                        servo.set_target(value)
                except Exception:
                    logger.error(
                        f"Failed to set target for servo {name}", exc_info=True
                    )

            # Tick the I/O controller
            try:
                self._io_controller.tick(delta)
            except Exception as exc:
                logger.error("Failed to tick I/O controller", exc_info=True)
                raise

        except Exception as exc:
            logger.critical("Critical error in orchestrator tick", exc_info=True)
            raise
