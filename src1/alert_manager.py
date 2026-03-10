import time
from dataclasses import dataclass, field


@dataclass
class Alert:
    pid:          int
    level:        str
    behavior:     str
    duration_sec: float
    camera_id:    int
    timestamp:    str = ""
    status:       str = "pending"
    snapshot_path:str = ""


class AlertManager:
    def __init__(self):
        self._fired    = {}   # pid -> set of levels already fired
        self._open     = []
        self.confirmed = set()
        self.dismissed = set()

    def process(self, pid, level, behavior, duration_sec, camera_id):
        if pid in self.dismissed: return None
        fired = self._fired.setdefault(pid, set())
        if level in fired: return None          # already raised this level for this pid
        fired.add(level)
        a = Alert(pid=pid, level=level, behavior=behavior,
                  duration_sec=round(duration_sec, 1),
                  camera_id=camera_id,
                  timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                  status="pending")
        self._open.append(a)
        return a

    def human_override(self, pid, action):
        if action == "confirm":
            self.confirmed.add(pid); self.dismissed.discard(pid)
        else:
            self.dismissed.add(pid); self.confirmed.discard(pid)
        for a in self._open:
            if a.pid == pid:
                a.status = "confirmed" if action == "confirm" else "dismissed"
        return True

    def is_confirmed(self, pid): return pid in self.confirmed
    def is_dismissed(self, pid): return pid in self.dismissed

    def reset(self):
        self._fired    = {}
        self._open     = []
        self.confirmed = set()
        self.dismissed = set()