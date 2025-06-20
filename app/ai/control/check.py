import csv

def read_first_100_lines(file_path):
    """
    Reads the first 100 lines of a CSV file and prints them to the console.

    Args:
        file_path (str): The path to the CSV file.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            print(f"'{file_path}' dosyasının ilk 100 satırı:")
            for i, row in enumerate(reader):
                if i < 100:
                    print(f'{i+1}: {row}')
                else:
                    break
    except FileNotFoundError:
        print(f"Hata: '{file_path}' dosyası bulunamadı.")
    except Exception as e:
        print(f"Bir hata oluştu: {e}")

if __name__ == "__main__":
    csv_file_path = 'app/ai/control/first_hundred.csv'
    read_first_100_lines(csv_file_path)
