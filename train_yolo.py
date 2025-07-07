import cv2
import numpy as np
from ultralytics import YOLO

# YOLOv8 modelini yüklüyoruz
model = YOLO("runs/detect/helmet_detect_yolov8m9/weights/best.pt")

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
    results = [model(frame) for frame in frames]
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
