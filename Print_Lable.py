import csv
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import qrcode
import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime
import shutil
import os


class LabelGenerator:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.setup_dialog()

    def setup_dialog(self):
        self.dialog = tk.Toplevel(self.root)
        self.dialog.title("Load CSV and Select Range")
        self.dialog.geometry("450x300")

        main_frame = tk.Frame(self.dialog, padx=20, pady=15)
        main_frame.grid(row=0, column=0, sticky="nsew")

        # Configure grid weights for centering
        self.dialog.grid_rowconfigure(0, weight=1)
        self.dialog.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        # File selection button
        tk.Button(
            main_frame, text="Select CSV File", command=self.select_file, width=30
        ).grid(row=0, column=0, sticky="ew")

        # Range label with fixed dimensions and initial text
        self.range_label = tk.Label(
            main_frame, text="Please select a CSV file", height=3, width=40
        )
        self.range_label.grid(row=1, column=0, sticky="nsew", pady=10)
        # Input frames
        self.create_input_frames(main_frame)

        # Delete checkbox
        self.delete_var = tk.BooleanVar()
        self.delete_checkbox = tk.Checkbutton(
            main_frame, text="Delete data after processing", variable=self.delete_var
        )
        self.delete_checkbox.grid(row=4, column=0, sticky="ew")

        # OK button
        tk.Button(main_frame, text="OK", command=self.process).grid(
            row=5, column=0, sticky="ew"
        )

    def create_input_frames(self, parent):
        # Start frame
        start_frame = tk.Frame(parent)
        start_frame.grid(row=2, column=0, sticky="ew")
        tk.Label(start_frame, text="Start Value:", width=12, anchor="e").grid(
            row=0, column=0, padx=5
        )
        self.start_entry = tk.Entry(start_frame, width=20)
        self.start_entry.grid(row=0, column=1)

        # End frame
        end_frame = tk.Frame(parent)
        end_frame.grid(row=3, column=0, sticky="ew")
        tk.Label(end_frame, text="End Value:  ", width=12, anchor="e").grid(
            row=0, column=0, padx=5
        )
        self.end_entry = tk.Entry(end_frame, width=20)
        self.end_entry.grid(row=0, column=1)

    def select_file(self):
        self.file_path = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if self.file_path:
            self.data = self.load_csv_data(self.file_path)
            if self.data:
                sorted_keys = sorted(self.data.keys())
                # Continue with the rest of the processing

    def select_file(self):
        self.file_path = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if self.file_path:
            self.data = self.load_csv_data(self.file_path)
            if self.data:
                sorted_keys = sorted(self.data.keys())
                range_text = f"Range: {sorted_keys[0]} to {sorted_keys[-1]}"
                optional_text = "Optionally enter Start and End value:"
                self.range_label.configure(text=f"{range_text}\n{optional_text}")

    def process(self):
        if hasattr(self, "data"):
            start = self.start_entry.get()
            end = self.end_entry.get()
            print("Processing data...")
            self.create_labels(
                self.data,
                self.file_path,
                start_value=start,
                end_value=end,
                delete_data=self.delete_var.get(),
            )
            print("Labels created successfully!")
            # Only close after PDF creation
            self.dialog.destroy()
            self.root.destroy()

    def run(self):
        self.root.mainloop()

    def load_csv_data(self, file_path):
        csv_file = Path(file_path)
        if not csv_file.exists():
            raise FileNotFoundError("CSV file not found!")

        label_data = {}
        with open(csv_file, encoding="utf-8") as file:
            csv_reader = csv.reader(file, delimiter=";")
            next(csv_reader)  # Skip header row
            for row in csv_reader:
                if len(row) >= 2:
                    label_data[row[0]] = row[1]
                else:
                    print(f"Skipping invalid row: {row}")

        if not label_data:
            raise ValueError("No valid data found in CSV!")

        return label_data

    def backup_and_update_csv(self, csv_file, filtered_data):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"ASN_Liste_backup_{timestamp}.csv"
        shutil.copy2(csv_file, backup_file)

        all_data = []
        with open(csv_file, "r", encoding="utf-8") as file:
            csv_reader = csv.reader(file, delimiter=";")
            header = next(csv_reader)
            all_data = list(csv_reader)

        filtered_asn_set = set(filtered_data.keys())
        updated_data = [row for row in all_data if row[0] not in filtered_asn_set]

        with open(csv_file, "w", encoding="utf-8", newline="") as file:
            csv_writer = csv.writer(file, delimiter=";")
            csv_writer.writerow(header)
            csv_writer.writerows(updated_data)

    def create_labels(
        self,
        data,
        file_path,
        start_value=None,
        end_value=None,
        delete_data=False,
    ):
        print("Starting label creation...")
        print(f"Data items: {len(data)}")

        filtered_data = data
        if start_value:
            filtered_data = {
                k: v
                for k, v in filtered_data.items()
                if int(k.replace("ASN", "").lstrip("0")) >= int(start_value)
            }
        if end_value:
            filtered_data = {
                k: v
                for k, v in filtered_data.items()
                if int(k.replace("ASN", "").lstrip("0")) <= int(end_value)
            }

        print(f"Filtered data items: {len(filtered_data)}")

        if not filtered_data:
            print("No data to process")
            return

        print("Creating PDF...")

        # Label dimensions (in mm)
        label_width = 29
        label_height = 17.5
        top_margin = 15
        left_margin = 10
        labels_per_row = 7
        labels_per_column = 16
        y_offset = 0

        pdf = canvas.Canvas("labels.pdf", pagesize=A4)

        # Calculate positions (mm to points conversion - 1mm = 2.83465 points)
        mm_to_points = 2.83465
        x_positions = [
            left_margin * mm_to_points + i * (label_width * mm_to_points)
            for i in range(labels_per_row)
        ]
        y_positions = [
            A4[1]
            - (top_margin * mm_to_points)
            - j * (label_height * mm_to_points)
            - (y_offset * mm_to_points)
            for j in range(labels_per_column)
        ]

        label_counter = 0
        page = 0

        for key, value in filtered_data.items():
            if label_counter >= labels_per_row * labels_per_column:
                pdf.showPage()
                label_counter = 0
                page += 1

            row = label_counter // labels_per_row
            column = label_counter % labels_per_row

            x = x_positions[column]
            y = y_positions[row]

            pdf.setFont("Helvetica", 8)
            qr = qrcode.QRCode(version=1, box_size=2, border=0)
            qr.add_data(key)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white")
            qr_img_path = f"temp_qr_{key}.png"
            qr_img.save(qr_img_path)
            pdf.drawImage(qr_img_path, x, y - 15, width=30, height=30)
            pdf.drawString(x + 35, y - 10, str(value))
            Path(qr_img_path).unlink()

            label_counter += 1

        pdf.save()

        print(f"PDF saved to: {os.getcwd()}/labels.pdf")

        if delete_data:
            self.backup_and_update_csv(file_path, filtered_data)


if __name__ == "__main__":
    app = LabelGenerator()
    app.run()
