import os
import sys
import subprocess
from datetime import datetime, timedelta

def create_backup_filename(path, prefix, add_weekday=False):
    """
    Erstellt den Backup-Dateinamen basierend auf dem angegebenen Pfad, Prefix und Datum.
    Optional kann auch der Wochentag als Präfix hinzugefügt werden.

    Args:
    path (str): Der Pfad, in dem das Backup gespeichert wird.
    prefix (str): Das Prefix für den Dateinamen.
    add_weekday (bool): Wenn True, wird der aktuelle Wochentag als Präfix hinzugefügt.

    Returns:
    str: Der vollständige Pfad zur Backup-Datei.

    Raises:
    FileNotFoundError: Wenn der angegebene Pfad kein Verzeichnis ist.
    """
    # Aktuelles Datum (Monat und Jahr)
    now = datetime.now()
    date_str = now.strftime("%m%Y")  # Format MMYYYY
    
    # Optional: Wochentag als Präfix hinzufügen
    if add_weekday:
        weekday = now.strftime("%A")  # Z.B. Monday, Tuesday
        filename = f"{weekday}_{prefix}_{date_str}.img"
    else:
        filename = f"{prefix}_{date_str}.img"
    
    full_path = os.path.join(path, filename)
    
    # Fehlerbehandlung: Überprüfen, ob der Pfad existiert und ein Verzeichnis ist
    if not os.path.isdir(path):
        raise FileNotFoundError(f"Der angegebene Pfad existiert nicht oder ist kein Verzeichnis: {path}")
    
    # Überprüfe, ob die Datei bereits existiert; falls nicht, hänge ,,1024 an
    if not os.path.exists(full_path):
        full_path += ",,1024"
    
    return full_path

def delete_old_images(path):
    """
    Löscht alle .img-Dateien im angegebenen Verzeichnis, die älter als 12 Monate sind.

    Args:
    path (str): Der Pfad, in dem nach alten .img-Dateien gesucht wird.

    Raises:
    FileNotFoundError: Wenn der angegebene Pfad kein Verzeichnis ist.
    """
    # Fehlerbehandlung: Überprüfen, ob der Pfad ein gültiges Verzeichnis ist
    if not os.path.isdir(path):
        raise FileNotFoundError(f"Der Pfad '{path}' ist kein gültiges Verzeichnis.")
    
    # Berechne das Löschdatum (12 Monate zurück)
    cutoff_date = datetime.now() - timedelta(days=365)
    
    # Iteriere durch alle Dateien im Verzeichnis
    for filename in os.listdir(path):
        if filename.endswith(".img"):
            file_path = os.path.join(path, filename)
            try:
                # Erstelle Datum der Datei
                file_creation_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                # Lösche Datei, wenn sie älter als 12 Monate ist
                if file_creation_time < cutoff_date:
                    print(f"Lösche alte Datei: {file_path}")
                    os.remove(file_path)
            except OSError as e:
                # Fehlerbehandlung beim Löschen
                print(f"Fehler beim Löschen der Datei '{file_path}': {e}")

def run_image_backup(backup_filename):
    """
    Führt den Backup-Befehl 'image_backup' mit sudo aus und leitet die Ausgabe von stdout und stderr
    sowohl an die Konsole als auch an dmesg weiter. Gibt die Ausgabe im Fehlerfall zurück.

    Args:
    backup_filename (str): Der vollständige Pfad zur Backup-Datei.

    Returns:
    tuple: (bool, stdout, stderr) - True, wenn der Befehl erfolgreich war, False bei einem Fehler, 
                                    sowie die stdout und stderr Ausgabe.
    """
    # Befehl, um das Backup durchzuführen
    command = ["sudo", "image-backup", "-i", backup_filename]
    print(f"Führe Befehl aus: {' '.join(command)}")
    
    try:
        # Führe den Befehl aus und leite stdout und stderr ab
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Ausgabe von stdout und stderr direkt an die Konsole
        stdout_output = result.stdout.decode()
        stderr_output = result.stderr.decode()
        
        print(stdout_output)
        print(stderr_output, file=sys.stderr)
        
        # Weiterleiten der Ausgaben an dmesg mit dem Befehl 'logger'
        if stdout_output:
            subprocess.run(f'echo "{stdout_output}" | logger -t image-backup', shell=True)
        if stderr_output:
            subprocess.run(f'echo "{stderr_output}" | logger -t image-backup', shell=True)

        # Überprüfen, ob der Befehl erfolgreich ausgeführt wurde
        if result.returncode != 0:
            # Fehlerausgabe im Falle eines Fehlers
            print(f"Fehler bei der Ausführung von image-backup (Exit-Code {result.returncode})")
            return False, stdout_output, stderr_output  # Fehler aufgetreten
        return True, stdout_output, stderr_output  # Erfolgreich
    
    except FileNotFoundError:
        # Fehler, wenn das Programm 'image_backup' nicht gefunden wurde
        error_msg = "Fehler: Das Programm 'image-backup' wurde nicht gefunden."
        print(error_msg)
        return False, "", error_msg
    except subprocess.SubprocessError as e:
        # Allgemeine Fehlerbehandlung bei der Befehlsausführung
        error_msg = f"Fehler bei der Ausführung von image-backup: {e}"
        print(error_msg)
        return False, "", error_msg

def send_error_email(error_message, stdout_output="", stderr_output=""):
    """
    Sendet eine E-Mail mit der Fehlermeldung, wenn das Backup-Skript fehlschlägt.
    Fügt die stdout und stderr Ausgaben in die E-Mail ein.

    Args:
    error_message (str): Die Fehlermeldung, die per E-Mail versendet wird.
    stdout_output (str): Der stdout-Inhalt im Fehlerfall.
    stderr_output (str): Der stderr-Inhalt im Fehlerfall.
    """
    recipient = "hst@gamebox.at"  # Empfänger der Fehlermeldung
    subject = "Fehler bei der Ausführung von image-backup"  # Betreff der E-Mail
    body = f"{error_message}\n\nSTDOUT:\n{stdout_output}\n\nSTDERR:\n{stderr_output}"
    email_content = f"Subject: {subject}\n\n{body}"
    # Kommando für das Versenden der E-Mail
    command = f'echo "{email_content}" | msmtp {recipient}'
    
    try:
        # Führe den E-Mail-Befehl aus
        subprocess.run(command, shell=True)
    except Exception as e:
        # Fehlerbehandlung beim Versenden der E-Mail
        print(f"Fehler beim Versenden der Fehler-E-Mail: {e}")

def main():
    """
    Hauptfunktion, die das Backup durchführt:
    - Überprüft die Argumente (Pfad, Prefix).
    - Erstellt den Dateinamen für das Backup.
    - Löscht alte Backups.
    - Führt das Backup durch und sendet im Fehlerfall eine E-Mail mit der Ausgabe.
    """
    # Überprüfe, ob genügend Argumente übergeben wurden
    if len(sys.argv) != 3:
        print("Fehler: Pfad und Prefix müssen übergeben werden.")
        print("Verwendung: python script.py <pfad> <prefix>")
        sys.exit(1)
    
    path = sys.argv[1]  # Verzeichnis für das Backup
    prefix = sys.argv[2]  # Prefix für den Dateinamen
    
    # Fehlerbehandlung: Überprüfen, ob der Pfad existiert
    if not os.path.exists(path):
        error_message = f"Fehler: Der Pfad '{path}' existiert nicht."
        print(error_message)
        send_error_email(error_message)  # Sende E-Mail bei Fehler
        sys.exit(1)
    
    # Fehlerbehandlung: Überprüfen, ob der Pfad ein Verzeichnis ist
    if not os.path.isdir(path):
        error_message = f"Fehler: '{path}' ist kein Verzeichnis."
        print(error_message)
        send_error_email(error_message)  # Sende E-Mail bei Fehler
        sys.exit(1)
    
    # Fehlerbehandlung: Überprüfen, ob ein gültiges Prefix übergeben wurde
    if not prefix:
        error_message = "Fehler: Es wurde kein gültiges Prefix übergeben."
        print(error_message)
        send_error_email(error_message)  # Sende E-Mail bei Fehler
        sys.exit(1)
    
    try:
        # Erstelle den Dateinamen für das Backup
        backup_filename = create_backup_filename(path, prefix)
        
        # Lösche alte Backups
        delete_old_images(path)
        
        # Führe den ersten Backup-Versuch aus
        success, stdout_output, stderr_output = run_image_backup(backup_filename)
        
        # Falls ein Fehler auftritt, führe das Backup erneut mit Wochentag im Dateinamen aus
        if not success:
            print("Erneuter Versuch mit Wochentag im Dateinamen.")
            backup_filename_with_weekday = create_backup_filename(path, prefix, add_weekday=True)
            success, stdout_output, stderr_output = run_image_backup(backup_filename_with_weekday)
        
        # Wenn beide Versuche fehlschlagen, sende eine Fehlermeldung per E-Mail
        if not success:
            error_message = "Fehler bei beiden Versuchen, das Backup durchzuführen."
            send_error_email(error_message, stdout_output, stderr_output)
    
    except Exception as e:
        # Fange unerwartete Fehler ab und sende eine E-Mail
        error_message = f"Ein unerwarteter Fehler ist aufgetreten: {e}"
        print(error_message)
        send_error_email(error_message)
        sys.exit(1)

if __name__ == "__main__":
    main()
