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
from config import LABEL_CONFIG
import logging


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

        self.dialog.grid_rowconfigure(0, weight=1)
        self.dialog.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        tk.Button(
            main_frame, text="Select CSV File", command=self.select_file, width=30
        ).grid(row=0, column=0, sticky="ew")

        self.range_label = tk.Label(
            main_frame, text="Please select a CSV file", height=3, width=40
        )
        self.range_label.grid(row=1, column=0, sticky="nsew", pady=10)

        self.create_input_frames(main_frame)

        self.delete_var = tk.BooleanVar()
        self.delete_checkbox = tk.Checkbutton(
            main_frame, text="Delete data after processing", variable=self.delete_var
        )
        self.delete_checkbox.grid(row=4, column=0, sticky="ew")

        ok_button = tk.Button(main_frame, text="OK", command=self.process)
        ok_button.grid(row=5, column=0, sticky="ew")
        self.dialog.bind("<Return>", lambda e: self.process())

    def create_input_frames(self, parent):
        start_frame = tk.Frame(parent)
        start_frame.grid(row=2, column=0, sticky="ew")
        tk.Label(start_frame, text="Start Value:", width=12, anchor="e").grid(
            row=0, column=0, padx=5
        )
        self.start_entry = tk.Entry(start_frame, width=20)
        self.start_entry.grid(row=0, column=1)

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

    def filter_data(self, data, start_value=None, end_value=None):
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
        return filtered_data

    def check_page_capacity(self, filtered_data):
        items_count = len(filtered_data)
        page_capacity = LABEL_CONFIG["per_row"] * LABEL_CONFIG["per_column"]

        if items_count % page_capacity != 0:
            current_pages = items_count // page_capacity + 1
            labels_needed = current_pages * page_capacity
            message = f"Current selection ({items_count} labels) will leave empty spaces on the last page.\nAdjust to {labels_needed} labels for full pages?"
            if messagebox.askyesno("Adjust Range", message):
                return True
        return False

    def create_labels(
        self, data, file_path, start_value=None, end_value=None, delete_data=False
    ):
        filtered_data = self.filter_data(data, start_value, end_value)

        if self.check_page_capacity(filtered_data):
            # Adjust the range to fill complete pages
            page_capacity = LABEL_CONFIG["per_row"] * LABEL_CONFIG["per_column"]

            print(f"Number of filtered labels: {len(filtered_data)}")
            print(f"Labels per page: {page_capacity}")
            needed_labels = ((len(filtered_data) // page_capacity) + 1) * page_capacity
            # Extend the range to include more labels
            additional_needed = needed_labels - len(filtered_data)
            # Add more items from the original data
            all_keys = sorted(data.keys())
            current_end_idx = all_keys.index(list(filtered_data.keys())[-1])
            if current_end_idx + additional_needed < len(all_keys):
                for key in all_keys[
                    current_end_idx + 1 : current_end_idx + additional_needed + 1
                ]:
                    filtered_data[key] = data[key]

        print("Starting label creation...")
        print(f"Data items: {len(data)}")
        print(f"Filtered data items: {len(filtered_data)}")

        if not filtered_data:
            print("No data to process")
            return

        print("Creating PDF...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_file_name = f"labels_{timestamp}.pdf"

        pdf = canvas.Canvas(pdf_file_name, pagesize=A4)

        # Calculate positions using config values
        mm_to_points = 2.83465
        x_positions = [
            + i * (LABEL_CONFIG["width"] * mm_to_points)
            for i in range(LABEL_CONFIG["per_row"])
        ]
        y_positions = [
            A4[1]
            - (LABEL_CONFIG["margin_top"] * mm_to_points)
            - j * (LABEL_CONFIG["height"] * mm_to_points)            
            for j in range(LABEL_CONFIG["per_column"])
        ]

        label_counter = 0
        page = 0

        for key, value in filtered_data.items():
            if label_counter >= LABEL_CONFIG["per_row"] * LABEL_CONFIG["per_column"]:
                pdf.showPage()
                label_counter = 0
                page += 1

            row = label_counter // LABEL_CONFIG["per_row"]
            column = label_counter % LABEL_CONFIG["per_row"]

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

            LABEL_CONFIG["margin_left"] * mm_to_points

    def backup_and_update_csv(self, file_path, filtered_data):
        # Create backup with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{file_path}.{timestamp}.bak"
        shutil.copy2(file_path, backup_path)

        # Read all data from original CSV
        all_rows = []
        with open(file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.reader(file, delimiter=';')
            header = next(csv_reader)
            all_rows.append(header)
            
            
            # Only keep rows that weren't in filtered_data
            for row in csv_reader:
                if row[0] not in filtered_data:
                    all_rows.append(row)

        # Write remaining data back to CSV
        with open(file_path, 'w', newline='', encoding='utf-8') as file:
            csv_writer = csv.writer(file, delimiter=';')
            csv_writer.writerows(all_rows)


def validate_input(self, value):
    if value and not value.isdigit():
        return False
    return True


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    app = LabelGenerator()
    app.run()


def run(self):
    self.root.mainloop()

