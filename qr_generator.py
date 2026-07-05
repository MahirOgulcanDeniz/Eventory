import qrcode
import os

def toplu_qr_olustur():
    print("--- TOPLU QR KOD OLUŞTURUCU ---")
    
    base_name = input("Ürün Temel Adı (Örn: Monster_PC): ").strip()
    if not base_name:
        print("Hata: İsim boş olamaz.")
        return

    try:
        count = int(input("Kaç adet üretilecek? (Örn: 45): "))
        start_num = int(input("Kaçtan başlasın? (Genelde 1): "))
    except ValueError:
        print("Hata: Lütfen sayı giriniz.")
        return

    # Klasör oluştur (Masaüstünde veya projenin yanında)
    folder_name = f"QR_{base_name}"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    print(f"\n'{folder_name}' klasörüne QR kodlar oluşturuluyor...\n")

    for i in range(start_num, start_num + count):
        # Benzersiz ID formatı: URINADI-001, URINADI-002 gibi
        # zfill(3) sayesinde 1 yerine 001 yazar, sıralama düzgün olur.
        unique_id = f"{base_name}-{str(i).zfill(3)}"
        
        # QR Kodu Oluştur
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(unique_id)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        
        # Dosyayı kaydet
        file_path = os.path.join(folder_name, f"{unique_id}.png")
        img.save(file_path)
        
        print(f"✔ Oluşturuldu: {unique_id}")

    print(f"\n✅ İşlem Tamamlandı! Toplam {count} adet QR kod '{folder_name}' klasöründe hazır.")

if __name__ == "__main__":
    toplu_qr_olustur()