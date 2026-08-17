import os

# Betiğin bulunduğu dizini al
script_dir = os.path.dirname(os.path.abspath(__file__))

# Giriş ve çıkış dosyası yollarını tanımla
input_csv_path = os.path.join(script_dir, 'TMDB_movie_dataset_v11.csv')
output_csv_path = os.path.join(script_dir, 'first_hundred.csv')

try:
    with open(input_csv_path, 'r', encoding='utf-8') as f_in:
        # Orijinal dosyanın ilk 101 satırını oku (başlık + 100 veri)
        lines = [next(f_in) for _ in range(1000)]
    
    with open(output_csv_path, 'w', encoding='utf-8') as f_out:
        # Okunan satırları yeni dosyaya yaz
        f_out.writelines(lines)

    print(f"'{output_csv_path}' dosyası başarıyla oluşturuldu (ilk 101 satır kopyalandı).")

except FileNotFoundError:
    print(f"Hata: '{input_csv_path}' dosyası bulunamadı.")
except StopIteration:
    print(f"Hata: '{input_csv_path}' dosyası 101 satırdan daha az veri içeriyor.")
except Exception as e:
    print(f"Bir hata oluştu: {e}")