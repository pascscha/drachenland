"""Animation classes for handling various types of animations with error handling and logging."""

import json
import os
import logging
from typing import Dict, List, Optional, Any
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class AnimationError(Exception):
    """Base exception class for animation-related errors."""

    pass


class Animation:
    """Base animation class implementing common animation functionality."""

    def __init__(
        self, priority: int = 5, strength: float = 1, strength_speed: float = 1
    ):
        self.priority = priority
        self.strength = strength
        self.target_strength = strength
        self.strength_speed = strength_speed

    def animate_strength(self, target_strength: float) -> None:
        """Update the target strength of the animation."""
        self.target_strength = target_strength

    def tick(self, delta: float) -> None:
        """Update animation state based on time delta."""
        try:
            step = self.strength_speed * delta
            if self.strength < self.target_strength:
                self.strength = min(self.strength + step, self.target_strength)
            elif self.strength > self.target_strength:
                self.strength = max(self.strength - step, self.target_strength)
        except Exception as e:
            logger.error(f"Error in Animation.tick: {str(e)}", exc_info=True)


class KeyFrameAnimation(Animation):
    """Handles keyframe-based animations with interpolation."""

    def __init__(
        self, animation: Dict[str, Any], *args, name: Optional[str] = None, **kwargs
    ):
        try:
            super().__init__(*args, **kwargs)
            self.current_time = 0
            self.name = name

            config = animation.get("config", {})
            self.duration = config.get("totalFrames", 0) * (1 / config.get("fps", 1))
            self.fps = config.get("fps", 30)

            self._process_keyframes(animation)
            self.repetitions: Optional[int] = None

        except Exception as e:
            raise AnimationError(f"Failed to initialize KeyFrameAnimation: {str(e)}")

    def _process_keyframes(self, animation: Dict[str, Any]) -> None:
        """Process and validate keyframe data."""
        try:
            total_frames = animation["config"]["totalFrames"]
            self.keyframes = sorted(
                [
                    kf
                    for kf in animation["keyframes"]
                    if 0 <= kf["frameIndex"] <= total_frames
                ],
                key=lambda kf: kf["frameIndex"],
            )

            # Add wraparound keyframes
            last_frame = self.keyframes[-1]
            first_frame = self.keyframes[0]

            self.keyframes = (
                [
                    {
                        "frameIndex": last_frame["frameIndex"] - total_frames,
                        "values": last_frame["values"],
                    }
                ]
                + self.keyframes
                + [
                    {
                        "frameIndex": first_frame["frameIndex"] + total_frames,
                        "values": first_frame["values"],
                    }
                ]
            )

            # Convert frame indices to time
            for keyframe in self.keyframes:
                keyframe["time"] = keyframe["frameIndex"] / animation["config"]["fps"]

        except Exception as e:
            logger.error(f"Error processing keyframes: {str(e)}", exc_info=True)
            raise AnimationError(f"Failed to process keyframes: {str(e)}")

    @classmethod
    def from_path(
        cls, file_path: str, *args, name: Optional[str] = None, **kwargs
    ) -> "KeyFrameAnimation":
        """Create animation from a JSON file."""
        try:
            with open(file_path) as f:
                data = json.load(f)

            if name is None:
                name = os.path.basename(file_path)

            return cls(data, *args, name=name, **kwargs)

        except (json.JSONDecodeError, FileNotFoundError) as e:
            raise AnimationError(f"Failed to load animation from {file_path}: {str(e)}")

    def tick(self, delta: float) -> Dict[str, float]:
        """Update animation state and return interpolated values."""
        try:
            super().tick(delta)
            self.current_time += delta

            while self.current_time >= self.duration:
                self.current_time -= self.duration
                if self.repetitions is not None:
                    self.repetitions -= 1

            if self.repetitions is not None and self.repetitions <= 0:
                self.animate_strength(0)

            return self._interpolate_values()

        except Exception as e:
            logger.error(f"Error in KeyFrameAnimation.tick: {str(e)}", exc_info=True)
            return {}

    def _interpolate_values(self) -> Dict[str, float]:
        """Calculate interpolated values between keyframes."""
        try:
            frame_before = None
            frame_after = None

            for keyframe in self.keyframes:
                if keyframe["time"] <= self.current_time:
                    frame_before = keyframe
                if keyframe["time"] > self.current_time:
                    frame_after = keyframe
                    break

            if not frame_before or not frame_after:
                logger.warning("Could not find valid keyframes for interpolation")
                return {}

            interpolation_time = frame_after["time"] - frame_before["time"]
            progressed_time = self.current_time - frame_before["time"]
            progress = progressed_time / interpolation_time

            return {
                name: frame_before["values"][name] * (1 - progress)
                + frame_after["values"][name] * progress
                for name in frame_before["values"].keys()
                if name in frame_before["values"] and name in frame_after["values"]
            }

        except Exception as e:
            logger.error(f"Error interpolating values: {str(e)}", exc_info=True)
            return {}


class MultiKeyframeAnimation(Animation):
    """Handles multiple keyframe animations in sequence."""

    def __init__(self, animations: List[KeyFrameAnimation], *args, **kwargs):
        try:
            super().__init__(*args, **kwargs)
            self.animations = animations
            self.index = 0
            self.is_running = False
            self.animation: Optional[KeyFrameAnimation] = None
        except Exception as e:
            logger.error(
                f"Error initializing MultiKeyframeAnimation: {str(e)}", exc_info=True
            )
            raise AnimationError(
                f"Failed to initialize MultiKeyframeAnimation: {str(e)}"
            )

    @classmethod
    def from_path(
        cls, animations_dir: str, *args, **kwargs
    ) -> "MultiKeyframeAnimation":
        """Create animation from a directory of JSON files."""
        try:
            animations = [
                KeyFrameAnimation.from_path(os.path.join(animations_dir, file_path))
                for file_path in sorted(os.listdir(animations_dir))
                if file_path.endswith(".json")
            ]
            return cls(animations, *args, **kwargs)
        except Exception as e:
            logger.error(
                f"Error loading animations from {animations_dir}: {str(e)}",
                exc_info=True,
            )
            raise AnimationError(f"Failed to load animations from directory: {str(e)}")

    def start(self) -> None:
        """Start the animation sequence."""
        try:
            self.is_running = True
            self.animation = self.animations[self.index]
            self.animation.current_time = 0
            self.animation.repetitions = 1
        except Exception as e:
            logger.error(f"Error starting animation: {str(e)}", exc_info=True)
            self.is_running = False

    def tick(self, delta: float) -> Dict[str, float]:
        """Update animation state and return current values."""
        try:
            super().tick(delta)
            if self.animation is None:
                return {}

            values = self.animation.tick(delta)

            if self.animation.repetitions <= 0:
                self.animation = None
                self.is_running = False
                self.index = (self.index + 1) % len(self.animations)

            return values
        except Exception as e:
            logger.error(
                f"Error in MultiKeyframeAnimation.tick: {str(e)}", exc_info=True
            )
            return {}


class BackgroundAnimation(Animation):
    """Manages background animations with random activation."""

    def __init__(
        self,
        keyframe_animations: List[KeyFrameAnimation],
        *args,
        expected_start: float = 15,
        **kwargs,
    ):
        try:
            super().__init__(*args, **kwargs)
            self.keyframe_animations = keyframe_animations
            self.expected_start = expected_start
            self.active = {animation: False for animation in self.keyframe_animations}
        except Exception as e:
            logger.error(
                f"Error initializing BackgroundAnimation: {str(e)}", exc_info=True
            )
            raise AnimationError(f"Failed to initialize BackgroundAnimation: {str(e)}")

    def tick(self, delta: float) -> Dict[str, float]:
        """Update animation states and return combined values."""
        try:
            super().tick(delta)
            inactive = [
                animation
                for animation, is_active in self.active.items()
                if not is_active
            ]

            if inactive and random.random() < delta / self.expected_start:
                self._activate_random_animation(inactive)

            return self._process_active_animations(delta)
        except Exception as e:
            logger.error(f"Error in BackgroundAnimation.tick: {str(e)}", exc_info=True)
            return {}

    def _activate_random_animation(self, inactive: List[KeyFrameAnimation]) -> None:
        """Activate a random animation from inactive ones."""
        try:
            activated_animation = random.choice(inactive)
            self.active[activated_animation] = True
            activated_animation.current_time = 0
            activated_animation.repetitions = 1
        except Exception as e:
            logger.error(f"Error activating random animation: {str(e)}", exc_info=True)

    def _process_active_animations(self, delta: float) -> Dict[str, float]:
        """Process all active animations and combine their values."""
        active = [
            animation for animation, is_active in self.active.items() if is_active
        ]
        combined_values = {}

        for animation in active:
            try:
                values = animation.tick(delta)
                combined_values.update(values)

                if animation.repetitions <= 0:
                    self.active[animation] = False
            except Exception as e:
                logger.error(
                    f"Error processing active animation: {str(e)}", exc_info=True
                )

        return combined_values


class HeadAnimation(Animation):
    """Handles head movement animations based on pose estimation."""

    def __init__(
        self, pose_estimator: Any, animation_data: Dict[str, Any], *args, **kwargs
    ):
        try:
            super().__init__(*args, **kwargs)
            keyframes = animation_data.get("keyframes", [])
            if len(keyframes) < 3:
                raise AnimationError("Insufficient keyframes for head animation")

            self.left = keyframes[0]["values"]
            self.neutral = keyframes[1]["values"]
            self.right = keyframes[2]["values"]
            self.pose_estimator = pose_estimator
            self.last_pose = self.neutral
        except Exception as e:
            logger.error(f"Error initializing HeadAnimation: {str(e)}", exc_info=True)
            raise AnimationError(f"Failed to initialize HeadAnimation: {str(e)}")

    def interpolate_values(self, x: float) -> Dict[str, float]:
        """Interpolate between left and right poses."""
        try:
            return {
                key: x * self.right[key] + (1 - x) * self.left[key]
                for key in self.left
                if key in self.right and key in self.left
            }
        except Exception as e:
            logger.error(f"Error interpolating values: {str(e)}", exc_info=True)
            return self.neutral

    def tick(self, delta: float) -> Dict[str, float]:
        """Update animation state based on pose estimation."""
        try:
            super().tick(delta)
            target = self.last_pose

            if (
                hasattr(self.pose_estimator, "pose_x")
                and self.pose_estimator.pose_x is not None
            ):
                self.animate_strength(1)
                target = self.interpolate_values(self.pose_estimator.pose_x)
            else:
                self.animate_strength(0)

            self.last_pose = target
            return target
        except Exception as e:
            logger.error(f"Error in HeadAnimation.tick: {str(e)}", exc_info=True)
            return self.neutral


class WebUIAnimation(Animation):
    """Handles web UI-based animations with slider controls."""

    def __init__(self, *args, **kwargs):
        try:
            super().__init__(*args, **kwargs)
            self.slider_values: Dict[str, float] = {}
            self.animation: Optional[KeyFrameAnimation] = None
        except Exception as e:
            logger.error(f"Error initializing WebUIAnimation: {str(e)}", exc_info=True)
            raise AnimationError(f"Failed to initialize WebUIAnimation: {str(e)}")

    def start_animation(self, animation_data: Dict[str, Any]) -> None:
        """Start a new animation from provided data."""
        try:
            self.animation = KeyFrameAnimation(animation_data)
            config = animation_data.get("config", {})
            current_frame = config.get("currentFrameIndex", 0)
            fps = config.get("fps", 30)
            self.animation.current_time = current_frame / fps
        except Exception as e:
            logger.error(f"Error starting animation: {str(e)}", exc_info=True)
            self.animation = None

    def get_current_frame(self) -> int:
        """Get the current frame number of the animation."""
        try:
            if self.animation is None:
                raise ValueError("No animation is currently playing")
            return int(self.animation.current_time * self.animation.fps)
        except Exception as e:
            logger.error(f"Error getting current frame: {str(e)}", exc_info=True)
            return 0

    def stop_animation(self) -> None:
        """Stop the current animation."""
        self.animation = None

    def tick(self, delta: float) -> Dict[str, float]:
        """Update animation state and return current values."""
        try:
            super().tick(delta)
            if self.animation is not None:
                return self.animation.tick(delta)
            return self.slider_values
        except Exception as e:
            logger.error(f"Error in WebUIAnimation.tick: {str(e)}", exc_info=True)
            return self.slider_values
