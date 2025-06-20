import pandas as pd

# CSV dosyasını doğru şekilde oku
# Problem: Dosyada çift tırnak formatı var ve pandas bunu düzgün parse edemiyor
# Çözüm: Manuel olarak parse etmek gerekiyor

def load_movie_data():
    """TMDB film veri setini yükler ve temizler"""
    
    # Dosyayı text olarak oku
    with open('app/ai/data/TMDB_movie_dataset_v11.csv', 'r', encoding='utf-8') as file:
        lines = file.readlines()

    # Header'ı doğru şekilde parse et
    header_line = lines[0].strip()
    header_line = header_line.strip('"')
    
    if header_line.startswith('id,'):
        after_id = header_line[3:]  # 'id,' kısmını atla
        columns = ['id', 'title'] + [col.strip('""') for col in after_id.split('","')[1:]]
    else:
        columns = [col.strip('""') for col in header_line.split('","')]

    # Veriyi parse et
    data_rows = []
    for line in lines[1:]:  # Header'ı atla
        line = line.strip()
        if line:
            line = line.strip('"')  # Başındaki ve sonundaki tırnakları kaldır
            if ',' in line:
                first_comma = line.find(',')
                id_val = line[:first_comma]
                rest = line[first_comma+1:]
                rest_values = [val.strip('""') for val in rest.split('","')]
                values = [id_val] + rest_values
                
                if len(values) == len(columns):  # Sütun sayısı eşleşiyorsa
                    data_rows.append(values)

    # DataFrame oluştur
    df = pd.DataFrame(data_rows, columns=columns)

    # Veri tiplerini düzelt
    numeric_columns = ['id', 'vote_average', 'vote_count', 'revenue', 'runtime', 'budget', 'popularity']

    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].replace('', '0'), errors='coerce').fillna(0)

    # Boolean sütunu düzelt
    if 'adult' in df.columns:
        df['adult'] = df['adult'].map({'True': True, 'False': False, 'true': True, 'false': False})

    # Tarih sütununu düzelt
    if 'release_date' in df.columns:
        df['release_date'] = pd.to_datetime(df['release_date'], errors='coerce')

    return df

def display_movie_table():
    """Film verilerini tablo halinde gösterir"""
    
    # Veriyi yükle
    df = load_movie_data()
    
    print("=== TMDB FİLM VERİ SETİ ===")
    print(f"Toplam Film Sayısı: {len(df)}")
    print(f"Toplam Sütun Sayısı: {len(df.columns)}")
    
    # Temel bilgileri göster
    print(f"\nSütun İsimleri:")
    for i, col in enumerate(df.columns, 1):
        print(f"{i:2d}. {col}")
    
    # Ana tablo - seçilmiş sütunlar
    print(f"\n=== FİLM TABLOSU ===")
    display_columns = ['id', 'title', 'vote_average', 'vote_count', 'release_date', 'revenue', 'runtime', 'genres']
    available_columns = [col for col in display_columns if col in df.columns]
    
    # İlk 20 filmi göster
    print("\nİlk 20 Film:")
    print(df[available_columns].head(20).to_string(index=False))
    
    # Tüm veriyi görmek için:
    print(f"\n=== TÜM VERİ ===")
    print("Tüm veriyi görmek için df değişkenini kullanabilirsiniz.")
    print("Örnek kullanım:")
    print("- df.head(50)  # İlk 50 satır")
    print("- df.tail(20)  # Son 20 satır") 
    print("- df.info()    # Veri hakkında bilgi")
    print("- df.shape     # Boyut bilgisi")
    print("- df.columns   # Sütun isimleri")
    
    return df

# Çalıştır
if __name__ == "__main__":
    movie_df = display_movie_table() 