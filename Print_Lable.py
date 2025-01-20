import csv
from pathlib import Path
from reportlab.pdfgen import canvas  # type: ignore
from reportlab.lib.pagesizes import A4  # type: ignore


def lade_csv_daten(pFile):
    try:
        csv_datei = Path(pFile)
        if not csv_datei.exists():
            raise FileNotFoundError("Die Datei ASN_Liste.csv wurde nicht gefunden!")

        etiketten_daten = {}
        with open(csv_datei, encoding="utf-8") as datei:
            csv_leser = csv.reader(datei, delimiter=";")
            counter = 0
            for zeile in csv_leser:
                # Zeile 1 ist der Header und kann übersprungen werden
                if counter == 0:
                    counter += 1
                else:
                    if len(zeile) >= 2:  # Prüfe ob mindestens 2 Spalten existieren
                        etiketten_daten[zeile[0]] = zeile[1]
                    else:
                        print(f"Überspringe ungültige Zeile: {zeile}")

        if not etiketten_daten:
            raise ValueError("Keine gültigen Daten in der CSV gefunden!")

        return etiketten_daten

    except Exception as fehler:
        print(f"Fehler beim Laden der CSV: {fehler}")
        return None


import qrcode
from pathlib import Path
from reportlab.pdfgen import canvas  # type: ignore
from reportlab.lib.pagesizes import A4  # type: ignore
import os

from datetime import datetime
import shutil


def backup_and_update_csv(csv_file, filtered_data):
    # Create backup with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"ASN_Liste_backup_{timestamp}.csv"
    shutil.copy2(csv_file, backup_file)

    # Read all data from original CSV
    all_data = []
    with open(csv_file, "r", encoding="utf-8") as file:
        csv_reader = csv.reader(file, delimiter=";")
        header = next(csv_reader)  # Save header
        all_data = list(csv_reader)

    # Remove entries that were in the filtered range
    filtered_asn_set = set(filtered_data.keys())
    updated_data = [row for row in all_data if row[0] not in filtered_asn_set]

    # Write back to CSV
    with open(csv_file, "w", encoding="utf-8", newline="") as file:
        csv_writer = csv.writer(file, delimiter=";")
        csv_writer.writerow(header)  # Write header
        csv_writer.writerows(updated_data)


def erstelle_etiketten(
    etiketten_daten, file_path, start_wert=None, end_wert=None, delete_data=False
):
    if not etiketten_daten:
        print("Keine Daten zum Drucken vorhanden!")
        return

    print(f"Original data count: {len(etiketten_daten)}")
    print(f"Filtering with start_wert: {start_wert}")

    filtered_daten = etiketten_daten
    if start_wert:
        # Remove 'ASN' prefix and leading zeros, then compare as integers
        filtered_daten = {
            k: v
            for k, v in filtered_daten.items()
            if int(k.replace("ASN", "").lstrip("0")) >= int(start_wert)
        }
    if end_wert:
        filtered_daten = {
            k: v
            for k, v in filtered_daten.items()
            if int(k.replace("ASN", "").lstrip("0")) <= int(end_wert)
        }

    print(f"Filtered data count: {len(filtered_daten)}")
    print(f"First few filtered items: {list(filtered_daten.items())[:3]}")

    if not filtered_daten:
        print("Keine Daten im angegebenen Bereich gefunden!")
        return

    # Etiketten Maße (in mm)
    etiketten_breite = 29
    etiketten_hoehe = 17.5
    rand_oben = 15
    rand_links = 10
    etiketten_pro_zeile = 7
    etiketten_pro_spalte = 16
    y_offset = 0  # Added Y offset in mm

    pdf = canvas.Canvas("etiketten.pdf", pagesize=A4)

    # Positionen berechnen (mm zu Punkten konvertieren - 1mm = 2.83465 points)
    mm_to_points = 2.83465
    x_positionen = [
        rand_links * mm_to_points + i * (etiketten_breite * mm_to_points)
        for i in range(etiketten_pro_zeile)
    ]
    y_positionen = [
        A4[1]
        - (rand_oben * mm_to_points)
        - j * (etiketten_hoehe * mm_to_points)
        - (y_offset * mm_to_points)
        for j in range(etiketten_pro_spalte)
    ]

    etiketten_zaehler = 0
    seite = 0

    for schluessel, wert in filtered_daten.items():
        if etiketten_zaehler >= etiketten_pro_zeile * etiketten_pro_spalte:
            pdf.showPage()
            etiketten_zaehler = 0
            seite += 1

        zeile = etiketten_zaehler // etiketten_pro_zeile
        spalte = etiketten_zaehler % etiketten_pro_zeile

        x = x_positionen[spalte]
        y = y_positionen[zeile]

        pdf.setFont("Helvetica", 8)
        qr = qrcode.QRCode(version=1, box_size=2, border=0)
        qr.add_data(schluessel)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_img_path = f"temp_qr_{schluessel}.png"
        qr_img.save(qr_img_path)
        pdf.drawImage(qr_img_path, x, y - 15, width=30, height=30)
        pdf.drawString(x + 35, y - 10, str(wert))
        os.remove(qr_img_path)

        etiketten_zaehler += 1
    pdf.save()
    print("PDF wurde erfolgreich erstellt!")
    if delete_data:
        backup_and_update_csv(file_path, filtered_daten)


# Hauptprogramm
if __name__ == "__main__":
    import tkinter as tk
    from tkinter import filedialog, messagebox

    root = tk.Tk()
    root.withdraw()  # Hide the main window
# Create main dialog with modern dimensions and padding
dialog = tk.Toplevel(root)
dialog.title("CSV Laden und Bereichsauswahl")
dialog.geometry("450x250")

# Create main container frame with padding
main_frame = tk.Frame(dialog, padx=20, pady=15)
main_frame.grid(row=0, column=0, sticky="nsew")

# Configure grid weights for centering
dialog.grid_rowconfigure(0, weight=1)
dialog.grid_columnconfigure(0, weight=1)
main_frame.grid_columnconfigure(0, weight=1)


# Define select_file function first
def select_file():
    global file_path, daten
    file_path = filedialog.askopenfilename(
        title="Wählen Sie die CSV-Datei",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
    )
    if file_path:
        daten = lade_csv_daten(file_path)
        if daten:
            sorted_keys = sorted(daten.keys())
            first_value = sorted_keys[0]
            last_value = sorted_keys[-1]
            range_label.config(
                text=f"Bereich: {first_value} bis {last_value}\n\nOptional zum Filtern Start- und Endwert eingeben:"
            )
            start_frame.grid(row=2, column=0, sticky="ew")
            end_frame.grid(row=3, column=0, sticky="ew")
            delete_checkbox.grid(row=4, column=0, sticky="ew")
            ok_button.grid(row=5, column=0, sticky="ew")
            dialog.bind("<Return>", lambda event: process())


# File selection section - centered
file_button = tk.Button(
    main_frame, text="CSV-Datei auswählen", command=select_file, width=30
)
file_button.grid(row=0, column=0, sticky="ew")

# Range info - centered
range_label = tk.Label(main_frame, text="", height=3, wraplength=400)
range_label.grid(row=1, column=0, sticky="ew")

file_path = None
daten = None
# Create frames with grid layout and fixed-width labels
start_frame = tk.Frame(main_frame)
tk.Label(start_frame, text="Start Wert:", width=12, anchor="e").grid(
    row=0, column=0, padx=5
)
start_entry = tk.Entry(start_frame, width=20)
start_entry.grid(row=0, column=1)

end_frame = tk.Frame(main_frame)
tk.Label(end_frame, text="End Wert:  ", width=12, anchor="e").grid(
    row=0, column=0, padx=5
)
end_entry = tk.Entry(end_frame, width=20)
end_entry.grid(row=0, column=1)  # Create checkbox (without packing)
delete_var = tk.BooleanVar()
delete_checkbox = tk.Checkbutton(
    main_frame, text="Lösche Daten nach der Bearbeitung", variable=delete_var
)


def process():
    if daten:
        start = start_entry.get()
        end = end_entry.get()
        print(start, end)
        if start and not end:
            max_key = max(daten.keys())
            end = max_key.replace("ASN", "").lstrip("0")
        dialog.destroy()
        root.destroy()
        erstelle_etiketten(
            daten,
            file_path,
            start_wert=start,
            end_wert=end,
            delete_data=delete_var.get(),
        )


# OK button with distinct styling
ok_button = tk.Button(main_frame, text="OK", command=process)

root.mainloop()
