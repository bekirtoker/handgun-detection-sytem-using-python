import cv2
from ultralytics import YOLO
import tkinter as tk
from tkinter import Label, Button, filedialog
from datetime import datetime
from PIL import Image, ImageTk

# YOLO modelini yükle
model = YOLO("runs/train/yolov10_experiment/weights/best.pt")

# Küresel değişkenler
video_path = None
silah_tespit_saati = None

# Arayüz için ana pencere
root = tk.Tk()
root.title("Silah Tespit Sistemi")
root.geometry("800x600")

# Tarih ve saat gösterme fonksiyonu
def update_time():
    now = datetime.now()
    current_time = now.strftime("%Y-%m-%d %H:%M:%S")
    time_label.config(text=f"Tarih/Saat: {current_time}")
    root.after(1000, update_time)

# Video yükleme butonu
def load_video():
    global video_path
    video_path = filedialog.askopenfilename(filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")])
    if video_path:
        status_label.config(text=f"Video Seçildi: {video_path.split('/')[-1]}", fg="blue")

# Video işleme ve tespit fonksiyonu
def start_detection():
    global video_path, silah_tespit_saati
    if not video_path:
        status_label.config(text="Lütfen bir video yükleyin!", fg="red")
        return

    cap = cv2.VideoCapture(video_path)
    out = None
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    output_path = "output_video1.mp4"

    silah_tespit_saati = None  # Yeniden başlatma durumunda sıfırla

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # YOLO modelinden sonuç al
        results = model(frame)
        annotated_frame = results[0].plot()

        # Silah tespiti kontrolü
        if "silah" in results[0].names.values() and not silah_tespit_saati:
            silah_tespit_saati = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            status_label.config(text=f"Silah Tespit Edildi! ({silah_tespit_saati})", fg="red")
            time_detect_label.config(text=f"Tespit Zamanı: {silah_tespit_saati}")

        # Video kaydını başlat
        if out is None:
            out = cv2.VideoWriter(output_path, fourcc, 30.0, (frame.shape[1], frame.shape[0]))

        out.write(annotated_frame)

        # Görüntüyü arayüzde göster
        frame = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame)
        imgtk = ImageTk.PhotoImage(image=img)
        video_label.imgtk = imgtk
        video_label.config(image=imgtk)
        root.update_idletasks()

    cap.release()
    if out:
        out.release()
    cv2.destroyAllWindows()
    status_label.config(text="Video Tamamlandı!", fg="green")

# Arayüz elemanları
time_label = Label(root, text="Tarih/Saat: --:--:--", font=("Helvetica", 12))
time_label.pack()

status_label = Label(root, text="Durum: Bekleniyor...", font=("Helvetica", 16), fg="green")
status_label.pack()

time_detect_label = Label(root, text="Tespit Zamanı: --:--:--", font=("Helvetica", 12))
time_detect_label.pack()

video_label = Label(root)
video_label.pack()

load_button = Button(root, text="Video Yükle", command=load_video, font=("Helvetica", 12))
load_button.pack()

start_button = Button(root, text="Başlat", command=start_detection, font=("Helvetica", 14))
start_button.pack()

# Tarih ve saat güncellemesini başlat
update_time()

# Arayüzü başlat
root.mainloop()
