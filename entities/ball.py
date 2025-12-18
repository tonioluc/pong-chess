# entities/ball.py
import math
import random

class Ball:
    def __init__(self, x=400, y=300, radius=10, color="#ff79c6", speed=300):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        # velocity in pixels per second
        ang = random.uniform(-math.pi/4, math.pi/4)
        # start mostly vertical: dy positive = down
        self.dx = speed * math.sin(ang)
        self.dy = speed * (1 if random.choice((True, False)) else -1) * math.cos(ang)
        self.speed = speed
        # special power flags provided by game logic (renderer consumes them)
        self.special_ready = False
        self.special_active = False

    def reset(self, x, y, speed=None, direction_down=True):
        import math, random
        if speed is not None:
            self.speed = speed
        self.x = x
        self.y = y
        ang = random.uniform(-math.pi/4, math.pi/4)
        self.dx = self.speed * math.sin(ang)
        self.dy = self.speed * (1 if direction_down else -1) * math.cos(ang)
        # reset special flags when ball respawns
        self.special_ready = False
        self.special_active = False

    def update(self, dt):
        self.x += self.dx * dt
        self.y += self.dy * dt

    def to_dict(self):
        return {
            "x": self.x,
            "y": self.y,
            "dx": self.dx,
            "dy": self.dy,
            "radius": self.radius,
            "color": self.color,
            "speed": self.speed,
            "special_ready": self.special_ready,
            "special_active": self.special_active
        }

