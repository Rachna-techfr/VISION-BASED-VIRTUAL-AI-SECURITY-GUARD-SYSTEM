# VISION-BASED-VIRTUAL-AI-SECURITY-GUARD-SYSTEM

# 🛡️ Vision-Based Virtual AI Security Guard System (YOLOv8 + DeepSort)

## 📌 Overview
This project is a real-time AI surveillance system built using YOLOv8, 
DeepSort, Flask, and OpenCV. The system automatically detects and tracks 
people in surveillance videos, classifies their behaviour as normal, 
stationary, or loitering, and generates real-time color-coded alerts on 
a live monitoring dashboard. The system incorporates adaptive learning 
that continuously improves detection accuracy based on operator feedback.

---

## 🚀 Features

### 📹 Real-Time Detection & Tracking
- Person detection using YOLOv8 nano model
- Persistent unique ID assignment using DeepSort tracker
- Tracks persons across frames even when temporarily hidden
- Supports Avenue and ShanghaiTech datasets

### 🎨 Color-Coded Bounding Boxes
- 🟢 Green → Normal / Stationary person
- 🔴 Red → Loitering alert triggered
- 🔵 Blue → Operator confirmed threat
- No box → Dismissed person

### 🚨 Alert Panel
- Real-time stationary and loitering alert cards
- Confirm and Dismiss buttons for each alert
- Alert escalation from stationary to loitering
- Snapshot saved automatically on operator confirmation

### 📋 Event Log
- Logs all events with timestamp, person ID, level, duration, and status
- CSV-based logging with Windows file lock handling
- View complete event history in the Event Log tab

### 🧠 Adaptive Learning
- Adjusts detection thresholds based on operator feedback
- Confirm → tightens thresholds (detect sooner)
- Dismiss → relaxes thresholds (fewer false alarms)
- Learned values saved to JSON and persist across restarts
- Visual threshold bars in the Learning tab

### 🖥️ Monitoring Dashboard
- Flask-based real-time web dashboard
- Live video streaming with annotated bounding boxes
- Stats bar showing People, Stationary, and Loitering counts
- Alerts, Event Log, and Learning tabs

---

## 🧠 Project Workflow

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Add Dataset
Place your dataset videos in:
```
src1/datasets/avenue/videos/
src1/datasets/SHANGHAI/SHANGHAI_Test/frames/
```

### Step 3: Run the Application
```bash
cd src1
python app.py
```

### Step 4: Open Dashboard
Open your browser and go to:
```
http://127.0.0.1:5000
```

### Step 5: Select Video and Monitor
- Select dataset from dropdown
- Click a video from the sidebar
- Monitor detections and alerts in real time
- Confirm or Dismiss alerts to trigger adaptive learning

---

## 🛠️ Technologies Used
- Python
- Flask
- OpenCV
- YOLOv8 (Ultralytics)
- DeepSort Realtime
- HTML, CSS, JavaScript

---

## 📁 Project Structure
```
src1/
├── app.py
├── detection.py
├── loitering.py
├── alert_manager.py
├── event_logger.py
├── adaptive_learning.py
└── templates/
    └── monitor.html
dashboard/
├── Initial Person Detection.png
├── Alert Panel - Confirmed and Stationary Alerts.png
├── Adaptive Learning Tab.png
└── Event Log Tab.png
requirements.txt
README.md
```

---

## ⚙️ Installation
1. Clone the repository:
```bash
git clone https://github.com/Rachna-techfr/VISION-BASED-VIRTUAL-AI-SECURITY-GUARD-SYSTEM.git
cd VISION-BASED-VIRTUAL-AI-SECURITY-GUARD-SYSTEM
```

2. Create virtual environment:
```bash
python -m venv venv
venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the project:
```bash
cd src1
python app.py
```

---

## 📸 Screenshots

### Initial Person Detection
![Detection](dashboard/Initial%20Person%20Detection.png)

### Alert Panel — Confirmed and Stationary Alerts
![Alerts](dashboard/Alert%20Panel%20-%20Confirmed%20and%20Stationary%20Alerts.png)

### Adaptive Learning Tab
![Learning](dashboard/Adaptive%20Learning%20Tab.png)

### Event Log Tab
![EventLog](dashboard/Event%20Log%20Tab.png)

---

## 🎯 Applications
- Real-time surveillance monitoring
- Loitering and suspicious behaviour detection
- Reduction of manual security monitoring
- AI-based smart security systems
- Campus and public area surveillance

---

## 📈 Future Improvements
- GPU support for faster detection
- Multi-camera feed support
- Deep learning based behaviour classification
- Mobile application integration
- Cloud-based alert notification system

---

## 👩‍💻 Author
**Rachna R**
B.Voc (AI & ML)
