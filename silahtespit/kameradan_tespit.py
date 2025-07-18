#test.py

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





#Train.py




from ultralytics import YOLO
import torch

# CUDA belleğini temizle
torch.cuda.empty_cache()

# Eğitim verisi dosyasının yolu
train_data = './data.yaml'

# Ana işlev
def main():
    # YOLOv10 modelini yükle (önceden eğitilmiş bir modeli veya sıfırdan eğitimi başlatacak modeli kullanabilirsin)
    model = YOLO('yolov10n.pt')  # Sıfırdan eğitim başlatmak için 'yolov10.yaml' dosyasını kullanabilirsiniz

    # GPU kullanımını kontrol et
    gpu = torch.cuda.is_available()
    print("GPU mevcut mu?:", gpu)

    # Eğer GPU varsa CUDA kullanılacak, yoksa CPU kullanılacak
    device = 'cuda' if gpu else 'cpu'

    # Eğitim sürecini başlat
    model.train(
        data=train_data,            # Eğitim ve doğrulama veri setlerinin yolu
        epochs=100,                 # Eğitim yapılacak epoch sayısı
        batch=16,                   # Batch size
        project='runs/train',       # Eğitim sonuçlarının kaydedileceği ana klasör
        name='yolov10_experiment',  # Eğitim projesine verilen isim
        save_period=1,              # Her kaç epoch'ta bir model kaydedilsin
        patience=10,                # Erken durdurma için sabır parametresi
        optimizer='Adam',           # Kullanılacak optimizasyon algoritması
        lr0=0.01,                   # Başlangıç öğrenme oranı
        device=device               # Cihaz olarak GPU veya CPU kullanılacak
    )

    # Modeli kaydet
    model.save("deneme.pt")

    # Eğitim sonuçları otomatik olarak belirtilen klasöre kaydedilecek
    # Kayıt yerleri: runs/train/yolov10_experiment/ altında bulunacak

# Bu kısım yalnızca script ana modül olarak çalıştırıldığında tetiklenir
if __name__ == '__main__':
    main()








import sqlite3  # SQLite kullanımı için gerekli
import cv2
from ultralytics import YOLO
import tkinter as tk
from tkinter import Label, Button, Frame, Toplevel, Scrollbar, Listbox
from datetime import datetime
import random
from PIL import Image, ImageTk
import os
import requests

from collections import Counter
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


def show_statistics_panel():
    cursor.execute("SELECT tarih_saat, konum FROM tespitler")
    rows = cursor.fetchall()

    # Verileri işle
    dates = []
    hours = []
    locations = []

    for tarih_saat, konum in rows:
        try:
            dt = datetime.strptime(tarih_saat, "%Y-%m-%d %H:%M:%S")
            dates.append(dt.date())
            hours.append(dt.hour)
            locations.append(konum)
        except:
            continue

    # Sayımları yap
    date_counts = Counter(dates)
    hour_counts = Counter(hours)
    location_counts = Counter(locations)

    # Panel oluştur
    stat_window = Toplevel(root)
    stat_window.title("İstatistik Paneli")
    stat_window.geometry("800x600")
    stat_window.configure(bg="#2C3E50")

    # Genel bilgiler
    summary_label = Label(stat_window, text=f"Toplam Tespit: {len(rows)}", font=("Helvetica", 14), bg="#2C3E50", fg="white")
    summary_label.pack(pady=5)

    if location_counts:
        most_common_loc, loc_count = location_counts.most_common(1)[0]
        location_label = Label(stat_window, text=f"En Yoğun Konum: {most_common_loc} ({loc_count} kez)", font=("Helvetica", 14), bg="#2C3E50", fg="white")
        location_label.pack(pady=5)

    # Grafik çiz (Günlük dağılım)
    fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
    ax.bar(date_counts.keys(), date_counts.values(), color="#3498DB")
    ax.set_title("Günlük Tespit Sayıları")
    ax.set_xlabel("Tarih")
    ax.set_ylabel("Tespit Sayısı")
    ax.tick_params(axis='x', rotation=45)

    canvas = FigureCanvasTkAgg(fig, master=stat_window)
    canvas.draw()
    canvas.get_tk_widget().pack(pady=10)

    # Yoğun saat aralığı
    if hour_counts:
        yoğun_saat = hour_counts.most_common(1)[0][0]
        hour_label = Label(stat_window, text=f"En Yoğun Saat Aralığı: {yoğun_saat}:00 - {yoğun_saat+1}:00", font=("Helvetica", 14), bg="#2C3E50", fg="white")
        hour_label.pack(pady=5)

from collections import Counter
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# YOLO modelini yükle
model = YOLO("runs/train/yolov10_experiment/weights/best.pt")


# SQLite veritabanı oluştur bağlan
conn = sqlite3.connect("silah_tespitleri.db")
cursor = conn.cursor()

# Tespit tablosu oluştur
cursor.execute('''
CREATE TABLE IF NOT EXISTS tespitler (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tarih_saat TEXT,
    konum TEXT,
    dosya_adi TEXT
)
''')
conn.commit()

# Küresel değişkenler
silah_tespit_saati = None
silah_tespit_konumu = None
tespit_durumu = False

# Ana pencere

root = tk.Tk()
root.title("Silah Tespit Sistemi")
root.configure(bg="#2C3E50")
root.geometry("800x600")
root.resizable(False, False)

# Tarih ve saat güncelleme fonksiyonu
def update_time():
    now = datetime.now()
    current_time = now.strftime("%Y-%m-%d %H:%M:%S")
    time_label.config(text=f"Tarih/Saat: {current_time}")
    root.after(1000, update_time)

# Rastgele konum oluşturma

def generate_location():
    try:
        response = requests.get("https://ipinfo.io")
        data = response.json()
        city = data.get("city", "Bilinmiyor")
        region = data.get("region", "Bilinmiyor")
        return f"{city}, {region}"
    except:
        return "Konum Bilgisi Alinamadi"
    


# Görüntüyü kaydetme fonksiyonu
def save_detection(frame):
    global silah_tespit_konumu
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    filename = f"kayıt/detection_{timestamp}.png"
    cv2.imwrite(filename, frame)

    # Veritabanına kaydet
    cursor.execute('INSERT INTO tespitler (tarih_saat, konum, dosya_adi) VALUES (?, ?, ?)',
                   (silah_tespit_saati, silah_tespit_konumu, filename))
    conn.commit()
    print(f"Görüntü kaydedildi: {filename}")

# Silah tespit sistemi
def start_camera_detection():
    global silah_tespit_saati, silah_tespit_konumu, tespit_durumu
    cap = cv2.VideoCapture(0)
    silah_tespit_saati = None
    silah_tespit_konumu = None
    tespit_durumu = False

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        # Görüntüyü yeniden boyutlandır
        frame = cv2.resize(frame, (640, 360))

        # YOLO modelinden sonuç al
        results = model(frame)
        annotated_frame = results[0].plot()

        # Silah tespiti (Sınıf filtresi ve güven skoru eklendi)
        for box in results[0].boxes:
            confidence = box.conf[0]  # Güven skoru
            class_id = int(box.cls[0])  # Sınıf ID
            class_name = results[0].names[class_id]  # Sınıf ismi

            # Yalnızca "handgun" veya "gun" sınıfı tespitini kontrol et
            if "handgun" in class_name.lower() or "gun" in class_name.lower():
                if confidence > 0.50 and not tespit_durumu:  # Güven skoru > 0.7
                    silah_tespit_saati = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    silah_tespit_konumu = generate_location()
                    tespit_durumu = True

                    # Arayüz güncellemeleri
                    status_label.config(text="Silah Tespit Edildi!", fg="red")
                    location_label.config(text=f"Tespit Konumu: {silah_tespit_konumu}")
                    time_detect_label.config(text=f"Tespit Zamanı: {silah_tespit_saati}")

                    # Görüntüyü kaydet
                    save_detection(frame)
                    print(f"Silah Tespit Edildi - Sınıf: {class_name}, Confidence: {confidence:.2f}")

        # Görüntüyü arayüzde göster
        frame = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame)
        imgtk = ImageTk.PhotoImage(image=img)
        video_label.imgtk = imgtk
        video_label.config(image=imgtk)
        root.update()

    cap.release()
    cv2.destroyAllWindows()


# Tespit geçmişini gösterme fonksiyonu
# Tespit geçmişini gösterme ve işlemler

def show_detection_history():
    def delete_selected_record():
        selected = listbox.curselection()
        if not selected:
            return

        # Seçilen kaydın ID'sini al
        record_text = listbox.get(selected[0])
        record_id = record_text.split("|")[0].split(":")[1].strip()

        # Veritabanından kaydı sil
        cursor.execute("DELETE FROM tespitler WHERE id = ?", (record_id,))
        conn.commit()

        # Listeyi güncelle
        listbox.delete(selected[0])
        print(f"Silinen Kayit ID: {record_id}")

    def update_selected_record():
        selected = listbox.curselection()
        if not selected:
            return

        # Yeni değerler için pencere oluştur
        update_window = Toplevel(history_window)
        update_window.title("Kayit Güncelleme")
        update_window.geometry("400x200")
        update_window.configure(bg="#2C3E50")

        # Seçilen kaydın ID'sini al
        record_text = listbox.get(selected[0])
        record_id = record_text.split("|")[0].split(":")[1].strip()

        # Yeni konum ve zaman giriş alanları
        new_time_label = Label(update_window, text="Yeni Tarih/Saat:", bg="#2C3E50", fg="white")
        new_time_label.pack(pady=5)
        new_time_entry = tk.Entry(update_window, width=30)
        new_time_entry.pack(pady=5)

        new_location_label = Label(update_window, text="Yeni Konum:", bg="#2C3E50", fg="white")
        new_location_label.pack(pady=5)
        new_location_entry = tk.Entry(update_window, width=30)
        new_location_entry.pack(pady=5)

        # Güncelle butonu
        def save_updates():
            new_time = new_time_entry.get()
            new_location = new_location_entry.get()

            # Veritabanını güncelle
            if new_time or new_location:
                cursor.execute("UPDATE tespitler SET tarih_saat = ?, konum = ? WHERE id = ?",
                               (new_time, new_location, record_id))
                conn.commit()
                print(f"Güncellenen Kayıt ID: {record_id}")

                # Listeyi güncelle
                listbox.delete(selected[0])
                updated_text = f"ID: {record_id} | Tarih/Saat: {new_time} | Konum: {new_location}"
                listbox.insert(selected[0], updated_text)
                update_window.destroy()

        save_button = Button(update_window, text="Kaydet", command=save_updates, bg="#27AE60", fg="white")
        save_button.pack(pady=10)

    # Yeni pencere oluştur
    history_window = Toplevel(root)
    history_window.title("Tespit Geçmişi")
    history_window.geometry("600x500")
    history_window.configure(bg="#2C3E50")

    # Liste kutusu
    listbox = Listbox(history_window, font=("Helvetica", 12),                              bg="white", fg="black", width=80, height=20)
    listbox.pack(padx=10, pady=10, fill="both", expand=True)

    # Kaydırma çubuğu
    scrollbar = Scrollbar(history_window)
    scrollbar.pack(side="right", fill="y")
    listbox.config(yscrollcommand=scrollbar.set)
    scrollbar.config(command=listbox.yview)

    # Veritabanından kayıtları çek
    cursor.execute("SELECT id, tarih_saat, konum FROM tespitler")
    rows = cursor.fetchall()

    for row in rows:
        listbox.insert(tk.END, f"ID: {row[0]} | Tarih/Saat: {row[1]} | Konum: {row[2]}")

    # Silme butonu
    delete_button = Button(history_window, text="Seçili Kaydı Sil", command=delete_selected_record,
                           bg="#E74C3C", fg="white", font=("Helvetica", 12, "bold"))
    delete_button.pack(pady=5)

    # Güncelleme butonu
    update_button = Button(history_window, text="Seçili Kaydı Güncelle", command=update_selected_record,
                           bg="#F39C12", fg="white", font=("Helvetica", 12, "bold"))
    update_button.pack(pady=5)


# Üst çerçeve (Başlık ve Zaman)
top_frame = Frame(root, bg="#34495E", height=50)
top_frame.pack(side="top", fill="x")

time_label = Label(top_frame, text="Tarih/Saat: --:--:--", font=("Helvetica", 12), fg="white", bg="#34495E")
time_label.pack(side="left", padx=10, pady=5)

# Ana bilgiler bölgesi
info_frame = Frame(root, bg="#2C3E50")
info_frame.pack(side="top", fill="x")

status_label = Label(info_frame, text="Durum: Bekleniyor...", font=("Helvetica", 16, "bold"), fg="green", bg="#2C3E50")
status_label.pack(pady=5)

location_label = Label(info_frame, text="Tespit Konumu: --:--", font=("Helvetica", 12), fg="white", bg="#2C3E50")
location_label.pack(pady=2)

time_detect_label = Label(info_frame, text="Tespit Zamanı: --:--:--", font=("Helvetica", 12), fg="white", bg="#2C3E50")
time_detect_label.pack(pady=2)

# Butonlar
start_button = Button(root, text="Silah Tespit Sistemini Başlat", command=start_camera_detection,
                      font=("Helvetica", 14, "bold"), bg="#27AE60", fg="white", relief="raised", borderwidth=3)
start_button.pack(pady=10)

history_button = Button(root, text="Tespit Geçmişi", command=show_detection_history,
                        font=("Helvetica", 14, "bold"), bg="#2980B9", fg="white", relief="raised", borderwidth=3)
history_button.pack(pady=10)


statistics_button = Button(root, text="İstatistik Paneli", command=show_statistics_panel,
                           font=("Helvetica", 14, "bold"), bg="#8E44AD", fg="white", relief="raised", borderwidth=3)
statistics_button.pack(pady=10)

# Video alanı
video_label = Label(root, bg="black", width=640, height=360)
video_label.pack(pady=5)

# Tarih ve saat güncellemesini başlat
update_time()

# Arayüzü başlat
root.mainloop()

def show_statistics_panel():
    cursor.execute("SELECT tarih_saat, konum FROM tespitler")
    rows = cursor.fetchall()

    # Verileri işle
    dates = []
    hours = []
    locations = []

    for tarih_saat, konum in rows:
        try:
            dt = datetime.strptime(tarih_saat, "%Y-%m-%d %H:%M:%S")
            dates.append(dt.date())
            hours.append(dt.hour)
            locations.append(konum)
        except:
            continue

    # Sayımları yap
    date_counts = Counter(dates)
    hour_counts = Counter(hours)
    location_counts = Counter(locations)

    # Panel oluştur
    stat_window = Toplevel(root)
    stat_window.title("İstatistik Paneli")
    stat_window.geometry("800x600")
    stat_window.configure(bg="#2C3E50")

    # Genel bilgiler
    summary_label = Label(stat_window, text=f"Toplam Tespit: {len(rows)}", font=("Helvetica", 14), bg="#2C3E50", fg="white")
    summary_label.pack(pady=5)

    if location_counts:
        most_common_loc, loc_count = location_counts.most_common(1)[0]
        location_label = Label(stat_window, text=f"En Yoğun Konum: {most_common_loc} ({loc_count} kez)", font=("Helvetica", 14), bg="#2C3E50", fg="white")
        location_label.pack(pady=5)

    # Grafik çiz (Günlük dağılım)
    fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
    ax.bar(date_counts.keys(), date_counts.values(), color="#3498DB")
    ax.set_title("Günlük Tespit Sayıları")
    ax.set_xlabel("Tarih")
    ax.set_ylabel("Tespit Sayısı")
    ax.tick_params(axis='x', rotation=45)

    canvas = FigureCanvasTkAgg(fig, master=stat_window)
    canvas.draw()
    canvas.get_tk_widget().pack(pady=10)

    # Yoğun saat aralığı
    if hour_counts:
        yoğun_saat = hour_counts.most_common(1)[0][0]
        hour_label = Label(stat_window, text=f"En Yoğun Saat Aralığı: {yoğun_saat}:00 - {yoğun_saat+1}:00", font=("Helvetica", 14), bg="#2C3E50", fg="white")
        hour_label.pack(pady=5)
