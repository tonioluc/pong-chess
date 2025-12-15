# client/entities/paddle.py
class Paddle:
    def __init__(self, x=400, y=300, width=120, height=12, color="#FFFFFF"):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color

    def from_dict(self, d):
        self.x = d.get("x", self.x)
        self.y = d.get("y", self.y)
        self.width = d.get("width", self.width)
        self.height = d.get("height", self.height)
        self.color = d.get("color", self.color)

