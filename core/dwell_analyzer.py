import time
from collections import defaultdict

class DwellTimeAnalyzer:
    def __init__(self, limit_seconds=8):
        self.limit = limit_seconds
        self.start_times = defaultdict(lambda: None)

    def evaluate(self, pid):
        now = time.time()

        if self.start_times[pid] is None:
            self.start_times[pid] = now
            return False, 0

        duration = now - self.start_times[pid]
        return duration >= self.limit, duration
