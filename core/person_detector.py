import cv2
import random

def simple_detect(frame):
    h, w, _ = frame.shape

    # Fake person box (demo-safe)
    x1 = int(w * 0.3)
    y1 = int(h * 0.3)
    x2 = int(w * 0.6)
    y2 = int(h * 0.8)

    # Random suspicious behavior
    suspicious = random.random() > 0.7

    return [(x1, y1, x2, y2, suspicious)]
