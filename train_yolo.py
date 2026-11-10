import cv2
import numpy as np
from ultralytics import YOLO
import time
import threading
import requests

import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
COOLDOWN_SEC = 10
last_sent = {}

def send_violation(camera_id, confidence):
    payload = {
        "camera_id": camera_id,
        "violation_type": "no_helmet",
        "confidence": confidence,
    }
    try:
        r = requests.post(WEBHOOK_URL, json=payload, timeout=5)
        print("Webhook:", r.status_code, r.text)
    except requests.RequestException as e:
        print("Webhook hatası:", e)


def notify(camera_id, confidence):
    if not WEBHOOK_URL:  # .env yoksa bildirim gönderme
        return
    now = time.time()
    if now - last_sent.get(camera_id, 0) < COOLDOWN_SEC:
        return
    last_sent[camera_id] = now
    threading.Thread(
        target=send_violation,
        args=(camera_id, float(confidence)),
        daemon=True,
    ).start()

# YOLOv8 modelini yüklüyoruz
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)
model = YOLO(os.path.join(BASE_DIR, "models", "best.pt"))

import torch
DEVICE = 0 if torch.cuda.is_available() else "cpu"
HALF = DEVICE != "cpu"
print("Cihaz:", torch.cuda.get_device_name(0) if HALF else "CPU")

# Videoları ve frame listelerini oluşturuyoruz
video_paths = ["deneme.mp4", "deneme2.mp4", "deneme3.mp4", "deneme4.mp4"]
caps = [cv2.VideoCapture(path) for path in video_paths]

# Kare boyutları ve konumları
positions = [((20, 20), (500, 500)),
             ((520, 20), (1000, 500)),
             ((20, 520), (500, 1000)),
             ((520, 520), (1000, 1000))]

cv2.namedWindow("Baret Tespiti", cv2.WINDOW_NORMAL)

while True:
    frames = []
    rets = []

    # Videolardan kareleri okuyoruz
    for cap in caps:
        ret, frame = cap.read()
        rets.append(ret)
        if ret:
            frame = cv2.resize(frame, (480, 480))
        frames.append(frame)

    # Herhangi bir video bitmişse döngüyü sonlandırıyoruz
    if not all(rets):
        break

    # Tespit sonuçlarını ve "baret yok" flag'lerini tutmak için boş listeler
    # 4 kareyi tek seferde (batch) işle; GPU varsa FP16 kullan, log basma
    results = model(frames, imgsz=480, device=DEVICE, verbose=False)
    results = [[r] for r in results]
    baret_yok_flags = [False] * 4

    # Tüm framelerde nesne tespiti yapıyoruz
    for idx, (result, frame) in enumerate(zip(results, frames)):
        for r in result:
            boxes = r.boxes
            for box in boxes:
                cls = int(box.cls[0])
                conf = box.conf[0]
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                label = model.names[cls]
                color = (0, 255, 0) if label == "hat" else (0, 0, 255)

                # Kutu ve etiket çizimi
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, f"{label} {conf:.2f}", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

                if label == "person":
                    cv2.putText(frame, "Baret yok!", (x1, y2 + 30),
                                cv2.FONT_HERSHEY_DUPLEX, 0.8, (0, 0, 255), 2)
                    baret_yok_flags[idx] = True
                    notify(f"cam-{idx + 1}", conf)

    # Arka planı beyaz olarak seçiyoruz
    background = np.ones((1080, 1280, 3), dtype=np.uint8) * 255

    # Kareleri arka plana yerleştiriyoruz
    for i, frame in enumerate(frames):
        (x1, y1), (x2, y2) = positions[i]
        background[y1:y2, x1:x2] = frame

    # "Baret yok" varsa kırmızı ile çerçeveliyoruz
    for i, alert in enumerate(baret_yok_flags):
        if alert:
            (x1, y1), (x2, y2) = positions[i]
            cv2.rectangle(background, (x1, y1), (x2, y2), (0, 0, 255), 5)

    # Kamera etiketleri
    label_coords = [(20, 30), (520, 30), (20, 510), (520, 510)]
    for i, coord in enumerate(label_coords):
        cv2.putText(background, f"Kamera {i+1}", coord, cv2.FONT_HERSHEY_SIMPLEX,
                    1, (0, 0, 0), 2, cv2.LINE_AA)

    cv2.imshow("Baret Tespiti", background)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

for cap in caps:
    cap.release()
cv2.destroyAllWindows()
