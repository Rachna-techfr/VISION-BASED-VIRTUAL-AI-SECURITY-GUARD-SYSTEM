"""
Adaptive Learning Module
------------------------
Adjusts detection thresholds based on operator feedback:
  - CONFIRM  = true positive  -> tighten thresholds (detect sooner / more aggressively)
  - DISMISS  = false positive -> relax thresholds  (reduce false alarms)

Thresholds adjusted:
  - loiter_time_threshold   : seconds before loitering is declared
  - loiter_move_threshold   : pixel movement to reset loitering timer
  - stationary_vel_threshold: avg px/frame below which person is stationary

Saved to: logs/adaptive_params.json  (persists across restarts)
"""

import json, os, time

PARAMS_FILE = "logs/adaptive_params.json"

# Hard limits — never go beyond these
LIMITS = {
    "loiter_time_threshold":    {"min": 10,  "max": 60,  "default": 30},
    "loiter_move_threshold":    {"min": 20,  "max": 100, "default": 50},
    "stationary_vel_threshold": {"min": 4,   "max": 20,  "default": 10},
}

# How much each confirm/dismiss nudges the value (as % of range)
STEP_PCT = 0.04   # 4% of the allowed range per feedback event


class AdaptiveLearner:
    def __init__(self):
        self.params   = self._load()
        self.history  = []   # list of {action, pid, level, timestamp, changes}

    # ------------------------------------------------------------------ load/save
    def _defaults(self):
        return {k: v["default"] for k, v in LIMITS.items()}

    def _load(self):
        os.makedirs("logs", exist_ok=True)
        if os.path.exists(PARAMS_FILE):
            try:
                with open(PARAMS_FILE) as f:
                    data = json.load(f)
                # Fill in any missing keys with defaults
                defaults = self._defaults()
                for k, v in defaults.items():
                    if k not in data:
                        data[k] = v
                return data
            except Exception:
                pass
        return self._defaults()

    def _save(self):
        os.makedirs("logs", exist_ok=True)
        for _ in range(5):
            try:
                with open(PARAMS_FILE, "w") as f:
                    json.dump(self.params, f, indent=2)
                return
            except PermissionError:
                time.sleep(0.1)

    # ------------------------------------------------------------------ feedback
    def feedback(self, action, pid, level):
        """
        action: 'confirm' or 'dismiss'
        level:  'STATIONARY' or 'LOITERING'
        Returns dict of {param: (old_val, new_val)} for logging.
        """
        changes = {}

        if action == "confirm":
            # True positive — tighten: catch people sooner / at lower movement
            changes.update(self._adjust("loiter_time_threshold",    direction=-1))
            changes.update(self._adjust("loiter_move_threshold",    direction=-1))
            changes.update(self._adjust("stationary_vel_threshold", direction=+1))

        elif action == "dismiss":
            # False positive — relax: require longer / more movement before alerting
            changes.update(self._adjust("loiter_time_threshold",    direction=+1))
            changes.update(self._adjust("loiter_move_threshold",    direction=+1))
            changes.update(self._adjust("stationary_vel_threshold", direction=-1))

        self._save()
        entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "action":    action,
            "pid":       pid,
            "level":     level,
            "changes":   {k: {"from": round(v[0],2), "to": round(v[1],2)}
                          for k, v in changes.items()},
            "params_after": {k: round(v,2) for k,v in self.params.items()}
        }
        self.history.append(entry)
        return entry

    def _adjust(self, key, direction):
        """direction: +1 = increase, -1 = decrease"""
        lo   = LIMITS[key]["min"]
        hi   = LIMITS[key]["max"]
        step = (hi - lo) * STEP_PCT
        old  = self.params[key]
        new  = max(lo, min(hi, old + direction * step))
        self.params[key] = round(new, 2)
        return {key: (old, new)} if abs(new - old) > 0.001 else {}

    # ------------------------------------------------------------------ getters
    def get(self, key):
        return self.params.get(key, LIMITS[key]["default"])

    def get_all(self):
        return dict(self.params)

    def get_history(self, n=20):
        return self.history[-n:]

    def reset_to_defaults(self):
        self.params = self._defaults()
        self._save()
        return self.params