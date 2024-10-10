import os
import sys
import subprocess
from datetime import datetime, timedelta

def create_backup_filename(path, prefix, add_weekday=False):
    # Aktueller Monat und Jahr
    now = datetime.now()
    date_str = now.strftime("%m%Y")
    
    # Optional: Wochentag als Präfix hinzufügen
    if add_weekday:
        weekday = now.strftime("%A")  # Name des Wochentags (z.B. Monday, Tuesday)
        filename = f"{weekday}_{prefix}_{date_str}.img"
    else:
        filename = f"{prefix}_{date_str}.img"
    
    full_path = os.path.join(path, filename)
    
    # Fehlerbehandlung: Pfad überprüfen
    if not os.path.isdir(path):
        raise FileNotFoundError(f"Der angegebene Pfad existiert nicht oder ist kein Verzeichnis: {path}")
    
    return full_path

def delete_old_images(path):
    # Fehlerbehandlung: Pfad überprüfen
    if not os.path.isdir(path):
        raise FileNotFoundError(f"Der Pfad '{path}' ist kein gültiges Verzeichnis.")
    
    # Grenze für das Löschen: 12 Monate
    cutoff_date = datetime.now() - timedelta(days=365)
    
    # Gehe durch alle .img-Dateien im Verzeichnis
    for filename in os.listdir(path):
        if filename.endswith(".img"):
            file_path = os.path.join(path, filename)
            
            try:
                file_creation_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                # Datei löschen, wenn sie älter als 12 Monate ist
                if file_creation_time < cutoff_date:
                    print(f"Lösche alte Datei: {file_path}")
                    os.remove(file_path)
            except OSError as e:
                print(f"Fehler beim Löschen der Datei '{file_path}': {e}")

def run_image_backup(backup_filename):
    # Führe den image-backup Befehl mit sudo aus
    command = ["sudo", "image-backup", "-i", backup_filename]
    print(f"Führe Befehl aus: {' '.join(command)}")
    
    try:
        # Versuche, den Befehl auszuführen
        result = subprocess.run(command, capture_output=True, text=True)
        
        # Prüfe, ob der Befehl fehlerfrei ausgeführt wurde
        if result.returncode != 0:
            print(f"Fehler bei der Ausführung von image-backup: {result.stderr}")
            return False  # Fehler aufgetreten
        return True  # Erfolgreich
    
    except FileNotFoundError:
        print(f"Fehler: Das Programm 'image-backup' wurde nicht gefunden.")
        return False
    except subprocess.SubprocessError as e:
        print(f"Fehler bei der Ausführung von image-backup: {e}")
        return False

def main():
    # Überprüfe, ob genügend Argumente übergeben wurden
    if len(sys.argv) != 3:
        print("Fehler: Pfad und Prefix müssen übergeben werden.")
        print("Verwendung: python script.py <pfad> <prefix>")
        sys.exit(1)
    
    path = sys.argv[1]
    prefix = sys.argv[2]
    
    # Fehlerbehandlung: Überprüfe, ob der Pfad existiert
    if not os.path.exists(path):
        print(f"Fehler: Der Pfad '{path}' existiert nicht.")
        sys.exit(1)
    
    # Fehlerbehandlung: Überprüfe, ob der Pfad ein Verzeichnis ist
    if not os.path.isdir(path):
        print(f"Fehler: '{path}' ist kein Verzeichnis.")
        sys.exit(1)
    
    # Fehlerbehandlung: Überprüfe, ob ein gültiges Prefix übergeben wurde
    if not prefix:
        print("Fehler: Es wurde kein gültiges Prefix übergeben.")
        sys.exit(1)
    
    try:
        # Erstelle den Dateinamen für das Backup (ohne Wochentag)
        backup_filename = create_backup_filename(path, prefix)
        
        # Lösche alte .img-Dateien
        delete_old_images(path)
        
        # Führe den ersten Backup-Versuch aus
        success = run_image_backup(backup_filename)
        
        # Falls ein Fehler auftritt, führe den Befehl erneut mit Wochentag-Präfix aus
        if not success:
            print("Erneuter Versuch mit Wochentag im Dateinamen.")
            backup_filename_with_weekday = create_backup_filename(path, prefix, add_weekday=True)
            run_image_backup(backup_filename_with_weekday)
    
    except Exception as e:
        print(f"Ein unerwarteter Fehler ist aufgetreten: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
