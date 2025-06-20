import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# CSV dosyasını doğru şekilde oku
# Problem: Dosyada çift tırnak formatı var ve pandas bunu düzgün parse edemiyor
# Çözüm: Manuel olarak parse etmek gerekiyor

# İlk önce dosyayı text olarak okuyup analiz edelim
with open('app/ai/data/TMDB_movie_dataset_v11.csv', 'r', encoding='utf-8') as file:
    lines = file.readlines()

print("CSV Dosyası Analizi:")
print(f"Toplam satır sayısı: {len(lines)}")
print(f"İlk satır (header): {lines[0][:100]}...")

# Header'ı doğru şekilde parse edelim
header_line = lines[0].strip()
# Başındaki ve sonundaki çift tırnakları kaldır
header_line = header_line.strip('"')
# İlk sütun id ve title'ı ayrı ayrı parse etmek için özel işlem
if header_line.startswith('id,'):
    # İlk virgülden sonrasını al ve çift tırnakları düzelt
    after_id = header_line[3:]  # 'id,' kısmını atla
    columns = ['id', 'title'] + [col.strip('""') for col in after_id.split('","')[1:]]
else:
    columns = [col.strip('""') for col in header_line.split('","')]

print(f"\nToplam sütun sayısı: {len(columns)}")
print("\nSütun isimleri:")
for i, col in enumerate(columns):
    print(f"{i+1:2d}. {col}")

# Şimdi manuel olarak veriyi parse edelim
data_rows = []
for line in lines[1:]:  # Header'ı atla
    line = line.strip()
    if line:
        # Her satırı parse et
        line = line.strip('"')  # Başındaki ve sonundaki tırnakları kaldır
        # İlk virgülü id ve title ayırmak için özel işle
        if ',' in line:
            # İlk virgülü bul
            first_comma = line.find(',')
            id_val = line[:first_comma]
            rest = line[first_comma+1:]
            # Geri kalan kısmı normal şekilde parse et
            rest_values = [val.strip('""') for val in rest.split('","')]
            values = [id_val] + rest_values
            
            if len(values) == len(columns):  # Sütun sayısı eşleşiyorsa
                data_rows.append(values)

# DataFrame oluştur
df = pd.DataFrame(data_rows, columns=columns)

print(f"\nDataFrame başarıyla oluşturuldu!")
print(f"Satır sayısı: {len(df)}")
print(f"Sütun sayısı: {len(df.columns)}")

# Veri tiplerini düzelt
# Numerik sütunları belirle ve dönüştür
numeric_columns = ['id', 'vote_average', 'vote_count', 'revenue', 'runtime', 'budget', 'popularity']

for col in numeric_columns:
    if col in df.columns:
        # Boş değerleri 0 ile değiştir ve numeric'e çevir
        df[col] = pd.to_numeric(df[col].replace('', '0'), errors='coerce').fillna(0)

# Boolean sütunu düzelt
if 'adult' in df.columns:
    df['adult'] = df['adult'].map({'True': True, 'False': False, 'true': True, 'false': False})

# Tarih sütununu düzelt
if 'release_date' in df.columns:
    df['release_date'] = pd.to_datetime(df['release_date'], errors='coerce')

print("\nVeri Seti Hakkında Genel Bilgiler:")
print(df.info())

print("\nİlk 5 Film:")
display_columns = ['title', 'vote_average', 'vote_count', 'release_date', 'revenue']
print(df[display_columns].head())

print("\nTemel İstatistikler (Numerik Sütunlar):")
numeric_df = df[numeric_columns]
print(numeric_df.describe())

# En yüksek puanlı 10 film
print("\nEn Yüksek Puanlı 10 Film:")
top_rated = df.nlargest(10, 'vote_average')
print(top_rated[['title', 'vote_average', 'vote_count', 'release_date']])

# En çok oy alan 10 film
print("\nEn Çok Oy Alan 10 Film:")
most_voted = df.nlargest(10, 'vote_count')
print(most_voted[['title', 'vote_count', 'vote_average', 'release_date']])

# En yüksek hasılat yapan 10 film
print("\nEn Yüksek Hasılat Yapan 10 Film:")
highest_revenue = df.nlargest(10, 'revenue')
print(highest_revenue[['title', 'revenue', 'budget', 'vote_average']])

# Türleri analiz et
print("\nTür Analizi:")
all_genres = []
for genres in df['genres'].dropna():
    if genres and genres != '':
        genre_list = [g.strip() for g in genres.split(',')]
        all_genres.extend(genre_list)

from collections import Counter
genre_counts = Counter(all_genres)
print("En popüler türler:")
for genre, count in genre_counts.most_common(10):
    print(f"{genre}: {count} film")

# Görselleştirme
plt.figure(figsize=(12, 6))
plt.subplot(1, 2, 1)
plt.hist(df['vote_average'], bins=20, edgecolor='black')
plt.title('Film Puanlarının Dağılımı')
plt.xlabel('IMDB Puanı')
plt.ylabel('Film Sayısı')

plt.subplot(1, 2, 2)
# Logaritmik ölçekte revenue vs budget
valid_data = df[(df['budget'] > 0) & (df['revenue'] > 0)]
plt.scatter(valid_data['budget'], valid_data['revenue'], alpha=0.7)
plt.title('Bütçe vs Hasılat İlişkisi')
plt.xlabel('Bütçe ($)')
plt.ylabel('Hasılat ($)')
plt.xscale('log')
plt.yscale('log')

plt.tight_layout()
plt.savefig('movie_analysis.png', dpi=300, bbox_inches='tight')
plt.close()

print("\nAnaliz tamamlandı! movie_analysis.png dosyası oluşturuldu.")
print(f"\nÖzet:")
print(f"- Toplam {len(df)} film analiz edildi")
print(f"- Ortalama IMDB puanı: {df['vote_average'].mean():.2f}")
print(f"- En yüksek puan: {df['vote_average'].max():.2f}")
print(f"- En düşük puan: {df['vote_average'].min():.2f}")
print(f"- Toplam hasılat: ${df['revenue'].sum():,.0f}")

# Sütun bilgilerini detaylı olarak yazdır
print(f"\n=== SÜTUN ANALİZİ ===")
print(f"Veri setinde bulunan tüm sütunlar:")
for i, col in enumerate(df.columns):
    print(f"{i+1:2d}. {col} - {df[col].dtype}")
    if col in numeric_columns:
        print(f"    Min: {df[col].min()}, Max: {df[col].max()}, Ortalama: {df[col].mean():.2f}")
    elif col == 'genres':
        print(f"    Örnek türler: {df[col].iloc[0][:50]}...")
    elif col == 'title':
        print(f"    Örnek filmler: {', '.join(df[col].head(3).tolist())}")
    print() 