from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort

model = YOLO("yolov8n.pt")

tracker = DeepSort(
    max_age=30,
    n_init=2,
    max_iou_distance=0.7,
    nms_max_overlap=0.5,
    embedder="mobilenet",
    bgr=True,
)

def detect_and_track(frame):
    results = model(frame, conf=0.15, classes=[0], imgsz=640, device="cpu", verbose=False)
    detections = []
    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            w, h = x2-x1, y2-y1
            if w < 12 or h < 12: continue
            if w > h*4.0: continue
            detections.append(([x1,y1,w,h], float(box.conf[0]), "person"))
    tracks  = tracker.update_tracks(detections, frame=frame)
    persons = []
    for t in tracks:
        if not t.is_confirmed(): continue
        x1,y1,x2,y2 = map(int, t.to_ltrb())
        fh,fw = frame.shape[:2]
        x1=max(0,x1); y1=max(0,y1); x2=min(fw,x2); y2=min(fh,y2)
        if (x2-x1)<12 or (y2-y1)<12: continue
        persons.append((t.track_id,(x1,y1,x2,y2),((x1+x2)//2,(y1+y2)//2)))
    return persons