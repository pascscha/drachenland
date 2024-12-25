from adafruit_servokit import ServoKit
import RPi.GPIO as GPIO


class Servo:
    def __init__(self, name, gpio_pin, speed, position=0, binary=False):
        self.name = name
        self.gpio_pin = gpio_pin
        self.speed = speed
        self.position = position
        self.target_position = position
        self.binary = binary

    def set_target(self, target_position):
        self.target_position = target_position

    def tick(self, delta_time):
        step = self.speed * delta_time
        # print("step", step, self.speed, delta_time)
        if self.position < self.target_position:
            self.position = min(self.position + step, self.target_position)
        elif self.position > self.target_position:
            self.position = max(self.position - step, self.target_position)
        return self.position


class Constraint:
    def is_allowed(self, servo):
        raise NotImplementedError("This method should be implemented by subclasses")


class RangeConstraint(Constraint):
    def __init__(self, servo, min_position, max_position):
        self.servo = servo
        self.min_position = min_position
        self.max_position = max_position

    def is_allowed(self, servo):
        if servo != self.servo:
            return True
        return self.min_position <= self.servo.position <= self.max_position


class OverlapConstraint(Constraint):
    def __init__(self, servo1, servo2, range1, range2):
        self.servo1 = servo1
        self.servo2 = servo2
        self.range1 = range1
        self.range2 = range2

    def is_allowed(self, servo):
        if servo != self.servo1 and servo != self.servo2:
            return True

        in_range1 = self.range1[0] <= self.servo1.position <= self.range1[1]
        in_range2 = self.range2[0] <= self.servo2.position <= self.range2[1]
        return not (in_range1 and in_range2)


class IoController:
    def __init__(self, servos, constraints):
        self.servos = {servo.name: servo for servo in servos}
        self.constraints = constraints

    def get_servo(self, name):
        return self.servos.get(name)

    def tick(self, delta_time):
        for servo in self.servos.values():
            old_position = servo.position
            before = [constraint.is_allowed(servo) for constraint in self.constraints]
            servo.tick(delta_time)
            after = [constraint.is_allowed(servo) for constraint in self.constraints]

            # Used to be allowed, now not allowed anymore
            if any(bef and not aft for bef, aft in zip(before, after)):
                servo.position = old_position

    @classmethod
    def from_config(cls, config):
        servos = {
            cfg["name"]: Servo(
                cfg["name"],
                int(idx),
                cfg["speed"],
                position=(cfg["min"] + cfg["max"]) / 2,
            )
            for idx, cfg in config["servos"].items()
        }

        for gpio_pin, cfg in config["gpios"].items():
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


class ServoKitIoController(IoController):
    def __init__(self, servos, constraints, channels=16):
        super().__init__(servos, constraints)
        self.kit = ServoKit(channels=channels)

        for servo in self.servos.values():
            if servo.binary:
                GPIO.setup(servo.gpio_pin, GPIO.OUT)
            else:
                servo.position = self.kit.servo[servo.gpio_pin].angle
                if servo.position is None:
                    servo.position = 90

                if servo.name in ["SR", "ALiR", "ARaR", "BRR"]:
                    servo.position = 180 - servo.position

    def tick(self, delta_time):
        super().tick(delta_time)
        for servo in self.servos.values():
            try:
                # print(servo.name, servo.gpio_pin, servo.position)
                angle = servo.position

                if servo.binary:
                    GPIO.output(servo.gpio_pin, angle > 90)
                else:
                    if servo.name in ["SR", "ALiR", "ARaR", "BRR"]:
                        angle = 180 - angle

                    angle = max(0, min(180, angle))

                    self.kit.servo[servo.gpio_pin].angle = angle
            except Exception as e:
                print("Error setting servo position:", e)
