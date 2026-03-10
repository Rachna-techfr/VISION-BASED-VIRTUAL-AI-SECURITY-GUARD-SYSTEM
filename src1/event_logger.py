import csv, os, cv2, time


FIELDS = ["alert_id", "timestamp", "pid", "level",
          "behavior", "duration_sec", "camera_id", "status", "snapshot_path"]


class EventLogger:
    def __init__(self, log_path="logs/events.csv", snap_dir="snapshots"):
        self.log_path = log_path
        self.snap_dir = snap_dir
        self._counter = 0
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        os.makedirs(snap_dir, exist_ok=True)
        if not os.path.exists(log_path):
            self._write_header()

    def _write_header(self):
        self._safe_write("w", lambda f: csv.writer(f).writerow(FIELDS))

    def _safe_write(self, mode, fn):
        """Open/write/close with retry for Windows file lock."""
        for _ in range(10):
            try:
                with open(self.log_path, mode, newline="") as f:
                    fn(f)
                return
            except PermissionError:
                time.sleep(0.2)

    def log(self, alert, frame=None):
        self._counter += 1
        aid  = "EVT-{:05d}".format(self._counter)
        # Snapshots only saved on operator Confirm — not automatically
        row = [aid, alert.timestamp, alert.pid, alert.level,
               alert.behavior, alert.duration_sec, alert.camera_id, alert.status, ""]
        self._safe_write("a", lambda f: csv.writer(f).writerow(row))
        return aid

    def update_confirmed(self, pid, snap_path):
        if not os.path.exists(self.log_path):
            return
        rows = []
        fieldnames = FIELDS
        for _ in range(10):
            try:
                with open(self.log_path, newline="") as f:
                    reader = csv.DictReader(f)
                    fieldnames = reader.fieldnames or FIELDS
                    for row in reader:
                        if int(row["pid"]) == pid:
                            row["status"] = "confirmed"
                            if snap_path:
                                row["snapshot_path"] = snap_path
                        rows.append(row)
                break
            except PermissionError:
                time.sleep(0.2)
        def write_rows(f):
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(rows)
        self._safe_write("w", write_rows)

    def read_recent(self, n=50):
        if not os.path.exists(self.log_path):
            return []
        for _ in range(5):
            try:
                with open(self.log_path, newline="") as f:
                    return list(csv.DictReader(f))[-n:]
            except PermissionError:
                time.sleep(0.1)
        return []