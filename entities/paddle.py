# entities/paddle.py

class Paddle:
    def __init__(self, x=400, y=580, width=120, height=12, color="#FFFFFF", speed=350):
        # x is center x
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.speed = speed  # pixels per second when moving
        self.vx = 0  # current horizontal velocity
        # movement command state: 'left'/'right'/'stop'
        self.command = 'stop'

    def apply_command(self, cmd):
        self.command = cmd
        if cmd == 'left':
            self.vx = -self.speed
        elif cmd == 'right':
            self.vx = self.speed
        else:
            self.vx = 0

    def update(self, dt, left_bound, right_bound):
        self.x += self.vx * dt
        half = self.width / 2
        min_x = left_bound + half
        max_x = right_bound - half
        if self.x < min_x:
            self.x = min_x
        if self.x > max_x:
            self.x = max_x

    def get_bounds(self):
        half = self.width / 2
        return (self.x - half, self.y - self.height/2, self.x + half, self.y + self.height/2)

    def to_dict(self):
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "color": self.color,
            "speed": self.speed,
            "command": self.command
        }

