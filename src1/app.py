from flask import Flask, render_template, Response, request, jsonify, send_from_directory
import cv2, os, time, threading, queue, math, csv
from collections import deque

from detection     import detect_and_track
from loitering     import LoiteringDetector
from alert_manager import AlertManager
from event_logger        import EventLogger
from adaptive_learning   import AdaptiveLearner

app = Flask(__name__)

DATASETS = {
    "Avenue":       "datasets/avenue/videos",
    "ShanghaiTech": "datasets/SHANGHAI/SHANGHAI_Test/frames",
}

loiter    = LoiteringDetector(time_threshold=30, movement_threshold=50)
alert_mgr = AlertManager()
event_log = EventLogger()
learner   = AdaptiveLearner()

frame_queue    = queue.Queue(maxsize=120)
detect_queue   = queue.Queue(maxsize=2)
last_persons   = []
last_frame     = None          # always keep latest frame for screenshots
prev_centers   = {}
vel_history    = {}
alerted_pids   = set()         # pids that have triggered loitering alert — box stays RED forever
persons_lock   = threading.Lock()
stop_event     = threading.Event()
live_stats     = {"people": 0, "stationary": 0, "loitering": 0}
session_id     = 0

SLOW           = 2.0
WARMUP         = 20
STATIONARY_VEL = 10
VEL_WINDOW     = 8

GREEN = (0, 200,  80)
RED   = (0,   0, 255)
BLUE  = (200,  80,   0)

os.makedirs("snapshots", exist_ok=True)


def box_color(pid):
    if alert_mgr.is_dismissed(pid):  return None          # don't draw
    if alert_mgr.is_confirmed(pid):  return BLUE
    if pid in alerted_pids:          return RED           # stays red forever once alerted
    return GREEN


def draw_boxes(frame, persons):
    out = frame.copy()
    count = 0
    for pid, (x1, y1, x2, y2), _ in persons:
        col = box_color(pid)
        if col is None:
            continue
        count += 1
        cv2.rectangle(out, (x1, y1), (x2, y2), col, 2)
        lbl = "ID {}".format(pid)
        font, fs, ft = cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2
        (tw, th), _  = cv2.getTextSize(lbl, font, fs, ft)
        pad   = 4
        tag_x = x1 + ((x2 - x1) // 2) - (tw // 2)
        tag_y = y1 - 6
        tag_x = max(pad, min(tag_x, out.shape[1] - tw - pad))
        if tag_y - th - pad < 0:
            tag_y = y2 + th + pad + 2
        rx1, ry1 = tag_x - pad, tag_y - th - pad
        rx2, ry2 = tag_x + tw + pad, tag_y + pad
        cv2.rectangle(out, (rx1, ry1), (rx2, ry2), col, cv2.FILLED)
        cv2.rectangle(out, (rx1, ry1), (rx2, ry2), (0, 0, 0), 1)
        cv2.putText(out, lbl, (tag_x, tag_y), font, fs, (0, 0, 0), ft, cv2.LINE_AA)
    cv2.putText(out, "People: {}".format(count),
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2, cv2.LINE_AA)
    return out


def video_reader(dataset, video):
    global last_frame
    base = DATASETS[dataset]
    if dataset == "Avenue":
        cap = cv2.VideoCapture(os.path.join(base, video))
        fps = cap.get(cv2.CAP_PROP_FPS) or 25
        spf = (1.0 / fps) * SLOW
        while not stop_event.is_set():
            t0 = time.perf_counter()
            ret, frame = cap.read()
            if not ret: break
            last_frame = frame.copy()
            try: frame_queue.put_nowait(frame)
            except: pass
            try: detect_queue.put_nowait(frame)
            except: pass
            wait = spf - (time.perf_counter() - t0)
            if wait > 0: time.sleep(wait)
        cap.release()
    elif dataset == "ShanghaiTech":
        seq_dir = os.path.join(base, video)
        spf = (1.0 / 25) * SLOW
        for fname in sorted(os.listdir(seq_dir)):
            if stop_event.is_set(): break
            t0    = time.perf_counter()
            frame = cv2.imread(os.path.join(seq_dir, fname))
            if frame is None: continue
            last_frame = frame.copy()
            try: frame_queue.put_nowait(frame)
            except: pass
            try: detect_queue.put_nowait(frame)
            except: pass
            wait = spf - (time.perf_counter() - t0)
            if wait > 0: time.sleep(wait)
    stop_event.set()


def detector():
    global last_persons, live_stats, STATIONARY_VEL
    fc = 0
    # Apply latest learned thresholds every time detector starts
    loiter.time_threshold     = learner.get("loiter_time_threshold")
    loiter.movement_threshold = learner.get("loiter_move_threshold")
    STATIONARY_VEL            = learner.get("stationary_vel_threshold")
    while not stop_event.is_set():
        try:    frame = detect_queue.get(timeout=0.5)
        except: continue
        fc += 1
        try:    persons = detect_and_track(frame)
        except: continue

        crowd  = len(persons)
        n_stat = 0
        n_loit = 0

        for pid, (x1, y1, x2, y2), center in persons:
            prev = prev_centers.get(pid, center)
            vel  = math.dist(center, prev)
            prev_centers[pid] = center

            if pid not in vel_history:
                vel_history[pid] = deque(maxlen=VEL_WINDOW)
            vel_history[pid].append(vel)
            avg_vel = sum(vel_history[pid]) / len(vel_history[pid])

            is_l = loiter.update(pid, center)
            dur  = time.time() - loiter.start_time.get(pid, time.time())

            is_stat = (avg_vel < STATIONARY_VEL) and not is_l

            if is_stat: n_stat += 1
            if is_l:
                n_loit += 1
                alerted_pids.add(pid)   # mark permanently

            if fc > WARMUP and not alert_mgr.is_dismissed(pid):
                if is_l:
                    # Loitering: always fire, even if STATIONARY was already sent
                    # Remove STATIONARY from fired set so LOITERING can escalate
                    if pid in alert_mgr._fired:
                        alert_mgr._fired[pid].discard("LOITERING")
                    al = alert_mgr.process(pid=pid, level="LOITERING",
                        behavior="Loitering", duration_sec=dur, camera_id=0)
                    if al: event_log.log(al)
                elif is_stat:
                    # Stationary: panel only, box stays green
                    al = alert_mgr.process(pid=pid, level="STATIONARY",
                        behavior="Stationary", duration_sec=dur, camera_id=0)
                    if al: event_log.log(al)

        with persons_lock:
            last_persons = persons
        live_stats = {"people": crowd, "stationary": n_stat, "loitering": n_loit}


def stream():
    while True:
        try:    frame = frame_queue.get(timeout=1.0)
        except: time.sleep(0.04); continue
        with persons_lock: persons = list(last_persons)
        annotated = draw_boxes(frame, persons)
        _, buf = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 88])
        yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n"
               + buf.tobytes() + b"\r\n")


@app.route("/", methods=["GET", "POST"])
def dashboard():
    dataset = request.form.get("dataset", "Avenue")
    video   = request.form.get("video")
    base    = DATASETS[dataset]
    videos  = sorted(os.listdir(base)) if os.path.isdir(base) else []
    if video is None and videos: video = videos[0]
    return render_template("monitor.html",
        datasets=list(DATASETS.keys()),
        selected_dataset=dataset, videos=videos, selected_video=video)


@app.route("/api/start", methods=["POST"])
def api_start():
    global last_persons, prev_centers, session_id, last_frame
    stop_event.set(); time.sleep(0.4); stop_event.clear()
    for q in [frame_queue, detect_queue]:
        while not q.empty():
            try: q.get_nowait()
            except: pass
    with persons_lock: last_persons = []
    last_frame = None
    prev_centers.clear(); vel_history.clear(); alerted_pids.clear()
    loiter.start_time.clear(); loiter.positions.clear()
    alert_mgr.reset()
    # Wipe events log — retry loop handles Windows file lock
    event_log._counter = 0
    os.makedirs("logs", exist_ok=True)
    for _attempt in range(10):
        try:
            with open("logs/events.csv", "w", newline="") as f:
                csv.writer(f).writerow(["alert_id", "timestamp", "pid", "level",
                    "behavior", "duration_sec", "camera_id", "status", "snapshot_path"])
            break
        except PermissionError:
            time.sleep(0.2)
    session_id += 1
    live_stats.update({"people": 0, "stationary": 0, "loitering": 0})
    d = request.get_json(force=True)
    threading.Thread(target=video_reader,
        args=(d.get("dataset", "Avenue"), d.get("video", "")), daemon=True).start()
    threading.Thread(target=detector, daemon=True).start()
    return str(session_id)


@app.route("/api/stats")
def api_stats(): return jsonify(live_stats)

@app.route("/api/events")
def api_events(): return jsonify(event_log.read_recent(50))

@app.route("/api/events/clear", methods=["POST"])
def api_events_clear():
    os.makedirs("logs", exist_ok=True)
    with open("logs/events.csv", "w", newline="") as f:
        csv.writer(f).writerow(["alert_id", "timestamp", "pid", "level",
            "behavior", "duration_sec", "camera_id", "status", "snapshot_path"])
    return "ok"


@app.route("/api/override", methods=["POST"])
def api_override():
    global last_frame
    d      = request.get_json(force=True)
    pid    = int(d.get("pid", -1))
    action = d.get("action", "dismiss")
    snap   = ""

    # On confirm — take screenshot of current frame with boxes drawn
    if action == "confirm" and last_frame is not None:
        with persons_lock: persons = list(last_persons)
        annotated = draw_boxes(last_frame, persons)
        snap = "snapshots/confirm_pid{}_{}.jpg".format(pid, int(time.time()))
        cv2.imwrite(snap, annotated, [cv2.IMWRITE_JPEG_QUALITY, 95])
        # Update event log status + snapshot path
        event_log.update_confirmed(pid, snap)

    alert_mgr.human_override(pid, action)

    # Adaptive learning: adjust thresholds based on operator feedback
    # Find the level for this pid from event log
    level = "LOITERING" if pid in alerted_pids else "STATIONARY"
    learn_entry = learner.feedback(action=action, pid=pid, level=level)

    # Apply updated thresholds immediately to running detector
    loiter.time_threshold     = learner.get("loiter_time_threshold")
    loiter.movement_threshold = learner.get("loiter_move_threshold")
    STATIONARY_VEL            = learner.get("stationary_vel_threshold")

    return jsonify({"ok": True, "snapshot": snap,
                    "learning": learn_entry["changes"],
                    "params":   learn_entry["params_after"]})


@app.route("/snapshots/<path:filename>")
def serve_snapshot(filename):
    return send_from_directory("snapshots", filename)


@app.route("/api/learning")
def api_learning():
    return jsonify({
        "params":  learner.get_all(),
        "history": learner.get_history(20),
        "limits":  {k: {"min": v["min"], "max": v["max"], "default": v["default"]}
                    for k,v in __import__("adaptive_learning").LIMITS.items()}
    })

@app.route("/api/learning/reset", methods=["POST"])
def api_learning_reset():
    params = learner.reset_to_defaults()
    loiter.time_threshold     = params["loiter_time_threshold"]
    loiter.movement_threshold = params["loiter_move_threshold"]
    STATIONARY_VEL            = params["stationary_vel_threshold"]
    return jsonify({"ok": True, "params": params})

@app.route("/video_feed")
def video_feed():
    return Response(stream(), mimetype="multipart/x-mixed-replace; boundary=frame")


if __name__ == "__main__":
    app.run(debug=False, threaded=True)