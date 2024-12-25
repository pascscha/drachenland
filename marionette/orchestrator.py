
class Orchestrator:
    def __init__(self, ioController, fps):
        self.ioController = ioController
        self.fps = fps
        self.animations = []
        pass

    def add(self, animation):
        self.animations.append(animation)

    def remove(self, animation):
        self.animations.remove(animation)

    def tick(self, delta):
        self.animations.sort(key=lambda x: x.priority)

        self.animations.sort(key=lambda x: x.priority)
        out_values = {}
        for animation in self.animations:
            values = animation.tick(delta)
            for name, value in values.items():
                if name not in out_values:
                    out_values[name] = self.ioController.get_servo(name).position
                out_values[name] = (
                    animation.strength * value
                    + (1 - animation.strength) * out_values[name]
                )

        for name, value in out_values.items():
            self.ioController.get_servo(name).set_target(value)
        self.ioController.tick(delta)
