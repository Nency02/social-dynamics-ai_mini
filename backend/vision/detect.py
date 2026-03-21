from ultralytics import YOLO

model = YOLO("yolov8n.pt")

def detect_person(frame):
    results = model(frame)
    return results
    