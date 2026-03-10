# Vision-Based Virtual AI Security Guard System

## Overview
A real-time AI surveillance system that detects and tracks people,
classifies behaviour as normal, stationary, or loitering using 
YOLOv8 and DeepSort, and generates alerts with adaptive learning.

## Features
- Real-time person detection using YOLOv8
- Persistent ID tracking using DeepSort
- Loitering detection with 30 second threshold
- Color-coded bounding boxes (Green / Red / Blue)
- Operator Confirm and Dismiss controls
- Adaptive learning from operator feedback
- Event logging with confirmed snapshots
- Flask-based live monitoring dashboard

## Tech Stack
- Python, Flask, OpenCV
- YOLOv8 (Ultralytics)
- DeepSort Realtime
- HTML, CSS, JavaScript

## Datasets
- Avenue Dataset
- ShanghaiTech Dataset

## Installation
pip install -r requirements.txt
python app.py

## How It Works
1. Select dataset and video from dashboard
2. System detects and tracks all persons
3. Loitering alert triggered after 30 seconds
4. Operator confirms or dismisses alert
5. System learns and improves from feedback
