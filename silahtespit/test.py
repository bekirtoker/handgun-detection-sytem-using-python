import cv2
from ultralytics import YOLO

model = YOLO("runs/train/yolov10_experiment/weights/best.pt")

video_path = "./saldiri4.mp4" 
cap = cv2.VideoCapture(video_path)

output_path = "output_video1.mp4"
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = None

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    results = model(frame)

    annotated_frame = results[0].plot()

    if out is None:
        out = cv2.VideoWriter(output_path, fourcc, 30.0, (frame.shape[1], frame.shape[0]))

    out.write(annotated_frame)

    cv2.imshow("Detection", annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
if out is not None:
    out.release()
cv2.destroyAllWindows()