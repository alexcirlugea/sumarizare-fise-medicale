import os
import csv
import sys

maxInt = sys.maxsize
while True:
    try:
        csv.field_size_limit(maxInt)
        break
    except OverflowError:
        maxInt = int(maxInt/10)

def extract_clinical_notes():
    csv_filename = "mimic-iv-bhc.csv"
    output_folder = "FiseMedicale"

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Am creat folderul: {output_folder}")

    print(f"Începem procesarea fișierului {csv_filename}...")
    print("Acest proces poate dura câteva minute din cauza dimensiunii fișierului.\n")

    count = 0
    try:
        with open(csv_filename, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                note_id = row.get('note_id')
                note_content = row.get('input')
                
                if note_id and note_content:
                    file_path = os.path.join(output_folder, f"{note_id}.txt")
                    
                    with open(file_path, mode='w', encoding='utf-8') as txt_file:
                        txt_file.write(note_content)
                    
                    count += 1
                    
                    if count % 1000 == 0:
                        print(f"Au fost generate {count} fișiere...")

        print(f"\nSucces! Au fost extrase și salvate {count} fișiere .txt în folderul '{output_folder}'.")
        
    except FileNotFoundError:
        print(f"Eroare: Nu am putut găsi fișierul '{csv_filename}'. Asigură-te că este în același folder cu scriptul.")
    except Exception as e:
        print(f"A apărut o eroare: {e}")

if __name__ == "__main__":
    extract_clinical_notes()