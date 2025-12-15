# client/entities/ball.py
import math
import random

class Ball:
    def __init__(self, x=400, y=300, radius=8, color="#FFFFFF"):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        self.dx = 0
        self.dy = 0

    def from_dict(self, d):
        self.x = d.get("x", self.x)
        self.y = d.get("y", self.y)
        self.dx = d.get("dx", self.dx)
        self.dy = d.get("dy", self.dy)
        self.radius = d.get("radius", self.radius)
        self.color = d.get("color", self.color)

