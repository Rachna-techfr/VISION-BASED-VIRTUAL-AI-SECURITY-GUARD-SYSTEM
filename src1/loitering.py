import time

class LoiteringDetector:
    def __init__(self, time_threshold=30, movement_threshold=50):
        self.time_threshold     = time_threshold
        self.movement_threshold = movement_threshold
        self.start_time = {}
        self.positions  = {}

    def update(self, pid, center):
        if pid not in self.start_time:
            self.start_time[pid] = time.time()
            self.positions[pid]  = center
            return False
        dx   = abs(center[0] - self.positions[pid][0])
        dy   = abs(center[1] - self.positions[pid][1])
        dist = (dx**2 + dy**2)**0.5
        if dist > self.movement_threshold:
            self.start_time[pid] = time.time()
            self.positions[pid]  = center
            return False
        return (time.time() - self.start_time[pid]) >= self.time_threshold