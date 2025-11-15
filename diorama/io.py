"""Servo control module for RPi with error handling and logging capabilities."""
import logging
from typing import Dict, Optional, Sequence
import traceback
from adafruit_servokit import ServoKit
import RPi.GPIO as GPIO
# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
class ServoError(Exception):
    """Base exception class for servo-related errors."""
    pass
class Servo:
    """Class representing a servo motor with position control."""
    def __init__(
        self,
        name: str,
        gpio_pin: int,
        speed: float,
        position: float = 0,
        binary: bool = False,
    ) -> None:
        self.name = name
        self.gpio_pin = gpio_pin
        self.speed = speed
        self.position = position
        self.target_position = position
        self.binary = binary
        logger.debug(f"Initialized servo {name} on pin {gpio_pin}")
    def set_target(self, target_position: float) -> None:
        """Set the target position for the servo."""
        self.target_position = target_position
        logger.debug(f"Servo {self.name}: Target position set to {target_position}")
    def tick(self, delta_time: float) -> float:
        """Update servo position based on time delta."""
        try:
            step = self.speed * delta_time
            if self.position < self.target_position:
                self.position = min(self.position + step, self.target_position)
            elif self.position > self.target_position:
                self.position = max(self.position - step, self.target_position)
            return self.position
        except Exception as e:
            logger.error(f"Error in servo tick for {self.name}: {str(e)}")
            logger.debug(traceback.format_exc())
            return self.position
class Constraint:
    """Base class for servo movement constraints."""
    def is_allowed(self, servo: Servo) -> bool:
        """Check if servo position is allowed."""
        raise NotImplementedError("This method should be implemented by subclasses")
class RangeConstraint(Constraint):
    """Constraint limiting servo movement to a specific range."""
    def __init__(self, servo: Servo, min_position: float, max_position: float) -> None:
        self.servo = servo
        self.min_position = min_position
        self.max_position = max_position
    def is_allowed(self, servo: Servo) -> bool:
        if servo != self.servo:
            return True
        return self.min_position <= self.servo.position <= self.max_position
class OverlapConstraint(Constraint):
    """Constraint preventing servo overlap in specified ranges."""
    def __init__(
        self,
        servo1: Servo,
        servo2: Servo,
        range1: tuple[float, float],
        range2: tuple[float, float],
    ) -> None:
        self.servo1 = servo1
        self.servo2 = servo2
        self.range1 = range1
        self.range2 = range2
    def is_allowed(self, servo: Servo) -> bool:
        if servo not in (self.servo1, self.servo2):
            return True
        in_range1 = self.range1[0] <= self.servo1.position <= self.range1[1]
        in_range2 = self.range2[0] <= self.servo2.position <= self.range2[1]
        return not (in_range1 and in_range2)
class IoController:
    """Base class for IO control operations."""
    def __init__(
        self, servos: Sequence[Servo], constraints: Sequence[Constraint]
    ) -> None:
        self.servos = {servo.name: servo for servo in servos}
        self.constraints = constraints
        logger.info(f"Initialized IoController with {len(servos)} servos")
    def get_servo(self, name: str) -> Optional[Servo]:
        """Get servo by name."""
        return self.servos.get(name)
    def tick(self, delta_time: float) -> None:
        """Update all servos respecting constraints."""
        for servo in self.servos.values():
            try:
                old_position = servo.position
                before = [
                    constraint.is_allowed(servo) for constraint in self.constraints
                ]
                servo.tick(delta_time)
                after = [
                    constraint.is_allowed(servo) for constraint in self.constraints
                ]
                if any(bef and not aft for bef, aft in zip(before, after)):
                    servo.position = old_position
            except Exception as e:
                logger.error(f"Error in tick for servo {servo.name}: {str(e)}")
                logger.debug(traceback.format_exc())
    @classmethod
    def from_config(cls, config: Dict) -> "IoController":
        """Create IoController instance from configuration dictionary."""
        try:
            servos = {}
            for idx, cfg in config["servos"].items():
                print(f"Setting up", cfg["name"], idx)
                servos[cfg["name"]] = Servo(
                    cfg["name"],
                    int(idx),
                    cfg["speed"],
                    position=(cfg["min"] + cfg["max"]) / 2,
                )
            for gpio_pin, cfg in config["gpios"].items():
                print(f"Setting up GPIO", cfg["name"], gpio_pin)
                servos[cfg["name"]] = Servo(
                    cfg["name"], int(gpio_pin), 10000, position=0, binary=True
                )
            constraints = [
                RangeConstraint(
                    servos[cfg["name"]],
                    min(cfg["min"], cfg["max"]),
                    max(cfg["min"], cfg["max"]),
                )
                for cfg in config["servos"].values()
            ]
            return cls(servos.values(), constraints)
        except Exception as e:
            logger.error(f"Error creating IoController from config: {str(e)}")
            logger.debug(traceback.format_exc())
            raise ServoError(f"Failed to create IoController: {str(e)}")
class ServoKitIoController(IoController):
    """IoController implementation for ServoKit hardware."""
    def __init__(
        self,
        servos: Sequence[Servo],
        constraints: Sequence[Constraint],
        channels: int = 16,
    ) -> None:
        super().__init__(servos, constraints)
        try:
            self.kit = ServoKit(channels=channels)
            self._initialize_servos()
        except Exception as e:
            raise e
            logger.error(f"Failed to initialize ServoKit: {str(e)}")
            logger.debug(traceback.format_exc())
            raise ServoError(f"ServoKit initialization failed: {str(e)}")
    def _initialize_servos(self) -> None:
        """Initialize all servos with their starting positions."""
        for servo in self.servos.values():
            try:
                if servo.binary:
                    GPIO.setup(servo.gpio_pin, GPIO.OUT)
                else:
                    current_angle = self.kit.servo[servo.gpio_pin].angle
                    servo.position = current_angle if current_angle is not None else 90
            except Exception as e:
                logger.error(f"Error initializing servo {servo.name}: {str(e)}")
                logger.debug(traceback.format_exc())
    def tick(self, delta_time: float) -> None:
        """Update servo positions on hardware."""
        super().tick(delta_time)
        for servo in self.servos.values():
            try:
                angle = servo.position
                if servo.binary:
                    GPIO.output(servo.gpio_pin, angle > 90)
                else:
                    angle = max(0, min(180, angle))
                    self.kit.servo[servo.gpio_pin].angle = angle
            except Exception as e:
                logger.error(f"Error setting position for servo {servo.name}: {str(e)}")
                logger.debug(traceback.format_exc())
    def __enter__(self) -> "ServoKitIoController":
        return self
    def __exit__(self, exc_type, exc_value, traceback) -> None:
        try:
            for servo in self.servos.values():
                if servo.binary:
                    servo.set_target(0)
                    servo.position = 0
                self.tick(0.01)
        except Exception as e:
            logger.error(f"Error in cleanup: {str(e)}")
            logger.debug(traceback.format_exc())
