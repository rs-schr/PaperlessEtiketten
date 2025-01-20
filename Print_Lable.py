import csv
from pathlib import Path
from reportlab.pdfgen import canvas  # type: ignore
from reportlab.lib.pagesizes import A4  # type: ignore

def lade_csv_daten():
    try:
        csv_datei = Path("ASN_Liste.csv")
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

def erstelle_etiketten(etiketten_daten):
    if not etiketten_daten:
        print("Keine Daten zum Drucken vorhanden!")
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
    
    for schluessel, wert in etiketten_daten.items():
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
    daten = lade_csv_daten()
    if daten:
        erstelle_etiketten(daten)

