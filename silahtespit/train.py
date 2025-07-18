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
