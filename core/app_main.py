from flask import Flask, render_template, Response, request
import cv2
import os
import time
import numpy as np

from person_detector import simple_detect

app = Flask(__name__)

DATA_ROOT = "datasets/UCF_Crime/Test"


@app.route("/", methods=["GET", "POST"])
def dashboard():
    sequences = sorted([
        d for d in os.listdir(DATA_ROOT)
        if os.path.isdir(os.path.join(DATA_ROOT, d))
    ])

    selected = sequences[0] if sequences else None

    if request.method == "POST":
        selected = request.form.get("sequence")

    return render_template(
        "viewer.html",
        sequences=sequences,
        selected=selected
    )


def stream_sequence(sequence):
    seq_path = os.path.join(DATA_ROOT, sequence)

    frames = sorted([
        f for f in os.listdir(seq_path)
        if f.lower().endswith(".png")
    ])

    for fname in frames:
        frame_path = os.path.join(seq_path, fname)
        frame = cv2.imread(frame_path)

        if frame is None:
            continue

        # ✅ Resize using correct interpolation (VERY IMPORTANT)
        frame = cv2.resize(
            frame,
            (960, 540),
            interpolation=cv2.INTER_CUBIC
        )

        # ✅ Light sharpening (prevents pixel blur)
        sharpen_kernel = np.array([
            [0, -1, 0],
            [-1, 5, -1],
            [0, -1, 0]
        ])
        frame = cv2.filter2D(frame, -1, sharpen_kernel)

        # Detection
        boxes = simple_detect(frame)

        for (x1, y1, x2, y2, suspicious) in boxes:
            color = (0, 0, 255) if suspicious else (0, 255, 0)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            label = "SUSPICIOUS" if suspicious else "NORMAL"
            cv2.putText(
                frame,
                label,
                (x1, y1 - 8),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                2
            )

        # High-quality JPEG encoding
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 95]
        _, buffer = cv2.imencode(".jpg", frame, encode_param)

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" +
            buffer.tobytes() +
            b"\r\n"
        )

        time.sleep(0.04)  # ~25 FPS


@app.route("/video_feed")
def video_feed():
    sequence = request.args.get("sequence")
    return Response(
        stream_sequence(sequence),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


if __name__ == "__main__":
    app.run(debug=True)
