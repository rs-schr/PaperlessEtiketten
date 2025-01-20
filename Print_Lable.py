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
        with open(csv_datei, encoding='utf-8') as datei:
            csv_leser = csv.reader(datei, delimiter=';')
            counter = 0
            for zeile in csv_leser:
                # Zeile 1 ist der Header und kann übersprungen werden
                if (counter == 0):
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

def erstelle_etiketten(etiketten_daten, start_wert=None, end_wert=None):
    if not etiketten_daten:
        print("Keine Daten zum Drucken vorhanden!")
        return
        
    print(f"Original data count: {len(etiketten_daten)}")
    print(f"Filtering with start_wert: {start_wert}")

    filtered_daten = etiketten_daten
    if start_wert:
        # Remove 'ASN' prefix and leading zeros, then compare as integers
        filtered_daten = {k: v for k, v in filtered_daten.items() 
                         if int(k.replace('ASN', '').lstrip('0')) >= int(start_wert)}
    if end_wert:
        filtered_daten = {k: v for k, v in filtered_daten.items() 
                         if int(k.replace('ASN', '').lstrip('0')) <= int(end_wert)}

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
    y_offset = 1  # Added Y offset in mm
    
    pdf = canvas.Canvas("etiketten.pdf", pagesize=A4)
    
    # Positionen berechnen (mm zu Punkten konvertieren - 1mm = 2.83465 points)
    mm_to_points = 2.83465
    x_positionen = [rand_links * mm_to_points + i * (etiketten_breite * mm_to_points) for i in range(etiketten_pro_zeile)]
    y_positionen = [A4[1] - (rand_oben * mm_to_points) - j * (etiketten_hoehe * mm_to_points) - (y_offset * mm_to_points) for j in range(etiketten_pro_spalte)]
    
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
        pdf.drawImage(qr_img_path, x, y-15, width=30, height=30)
        pdf.drawString(x + 35, y - 10, str(wert))
        os.remove(qr_img_path)

        
        etiketten_zaehler += 1
    pdf.save()    
    print("PDF wurde erfolgreich erstellt!")
# Hauptprogramm
if __name__ == "__main__":
    import tkinter as tk
    from tkinter import filedialog, messagebox
    
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    
    # Create main dialog
    dialog = tk.Toplevel(root)
    dialog.title("CSV Laden und Bereichsauswahl")
    
    # Center the dialog
    dialog.geometry("400x300")
    dialog.update_idletasks()
    x = (dialog.winfo_screenwidth() - dialog.winfo_width()) // 2
    y = (dialog.winfo_screenheight() - dialog.winfo_height()) // 2
    dialog.geometry(f"+{x}+{y}")
    
    file_path = None
    daten = None
    
    def select_file():
        global file_path, daten
        file_path = filedialog.askopenfilename(
            title="Wählen Sie die CSV-Datei",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if file_path:
            daten = lade_csv_daten(file_path)
            if daten:
                # Get first and last values
                sorted_keys = sorted(daten.keys())
                first_value = sorted_keys[0]
                last_value = sorted_keys[-1]
                
                # Enable input fields and show range info
                range_label.config(text=f"Erster Wert: {first_value}\nLetzter Wert: {last_value}\n\nWenn gewünscht, den Start- und Endwert eingeben: (Leer bedeutet alles)")
                start_frame.pack(pady=5)
                end_frame.pack(pady=5)
                ok_button.pack(pady=10)
                dialog.bind('<Return>', lambda event: process())
    # File selection button
    tk.Button(dialog, text="CSV-Datei auswählen", command=select_file).pack(pady=10)
    
    # Range info label
    range_label = tk.Label(dialog, text="")
    range_label.pack(pady=10)
    
    # Create frames but don't pack them yet
    start_frame = tk.Frame(dialog)
    tk.Label(start_frame, text="Start Wert:").pack(side=tk.LEFT)
    start_entry = tk.Entry(start_frame)
    start_entry.pack(side=tk.LEFT)
    
    end_frame = tk.Frame(dialog)
    tk.Label(end_frame, text="End Wert:").pack(side=tk.LEFT)
    end_entry = tk.Entry(end_frame)
    end_entry.pack(side=tk.LEFT)
        
    
    def process():
        if daten:
            start = start_entry.get()
            end = end_entry.get()
            print(start, end)
            if start and not end:
                # Extract the numeric part from the max key
                max_key = max(daten.keys())
                end = max_key.replace('ASN', '').lstrip('0')
            dialog.destroy()
            root.destroy()
            erstelle_etiketten(daten, start_wert=start, end_wert=end)    
    ok_button = tk.Button(dialog, text="OK", command=process)
    
    root.mainloop()