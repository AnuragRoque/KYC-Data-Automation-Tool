import customtkinter as ctk
import pandas as pd
import os
import datetime
import threading

class SheetCleanerFrame(ctk.CTkFrame):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure((0, 1, 2), weight=1)
        # Removed unsupported padx and pady from configure


        # Title
        ctk.CTkLabel(self, text="📊 Excel / CSV Sheet Cleaner", font=("Arial", 20, "bold")).grid(row=0, column=0, columnspan=3, pady=(0, 20))

        # Section 1: File Upload
        ctk.CTkLabel(self, text="1. Select File Type", anchor="w").grid(row=1, column=0, sticky="w")
        self.file_type_var = ctk.StringVar(value="Excel")
        self.file_type_menu = ctk.CTkOptionMenu(self, values=["Excel", "CSV"], variable=self.file_type_var, command=self.on_file_type_change)
        self.file_type_menu.grid(row=1, column=1, columnspan=2, sticky="ew", pady=5)

        ctk.CTkLabel(self, text="2. Upload Your File", anchor="w").grid(row=2, column=0, sticky="w", pady=(15, 0))
        self.file_entry = ctk.CTkEntry(self, placeholder_text="No file selected...")
        self.file_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=(15, 0))
        self.browse_button = ctk.CTkButton(self, text="Browse File", command=self.browse_file)
        self.browse_button.grid(row=2, column=2, padx=(5, 0), pady=(15, 0))

        self.sheet_var = ctk.StringVar(value="")
        self.sheet_menu = ctk.CTkOptionMenu(self, values=[], variable=self.sheet_var)
        self.sheet_menu.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(5, 15))
        self.sheet_menu.configure(state="disabled")

        # Section 2: Cleaning Options
        ctk.CTkLabel(self, text="3. Clean Data Options", font=("Arial", 14, "bold")).grid(row=4, column=0, columnspan=3, sticky="w", pady=(5, 5))

        self.clean_empty_button = ctk.CTkButton(self, text="🧹 Remove Completely Empty Rows and Columns", command=self.clean_empty)
        self.clean_empty_button.grid(row=5, column=0, columnspan=3, sticky="ew", pady=5)

        ctk.CTkLabel(self, text="Remove first N rows:", anchor="w").grid(row=6, column=0, sticky="w", pady=(10, 2))
        self.rows_entry = ctk.CTkEntry(self, placeholder_text="e.g., 1 or 2")
        self.rows_entry.grid(row=6, column=1, columnspan=2, sticky="ew", pady=(10, 2))

        ctk.CTkLabel(self, text="Remove first N columns:", anchor="w").grid(row=7, column=0, sticky="w", pady=(2, 10))
        self.cols_entry = ctk.CTkEntry(self, placeholder_text="e.g., 1 or 2")
        self.cols_entry.grid(row=7, column=1, columnspan=2, sticky="ew", pady=(2, 10))

        self.remove_button = ctk.CTkButton(self, text="✂️ Remove Selected Rows & Columns", command=self.remove_rows_cols)
        self.remove_button.grid(row=8, column=0, columnspan=3, sticky="ew", pady=5)

        # Section 3: Save Options
        ctk.CTkLabel(self, text="4. Save Cleaned Data", font=("Arial", 14, "bold")).grid(row=9, column=0, columnspan=3, sticky="w", pady=(15, 5))

        self.save_type_var = ctk.StringVar(value="Excel")
        self.save_type_menu = ctk.CTkOptionMenu(self, values=["Excel", "CSV"], variable=self.save_type_var)
        self.save_type_menu.grid(row=10, column=0, sticky="ew", pady=(0, 5))

        self.save_new_button = ctk.CTkButton(self, text="💾 Save As New File", command=self.save_new_file)
        self.save_new_button.grid(row=10, column=1, sticky="ew", padx=5, pady=(0, 5))

        self.save_button = ctk.CTkButton(self, text="💾 Overwrite (Save As)", command=self.save_file)
        self.save_button.grid(row=10, column=2, sticky="ew", pady=(0, 5))

        # Status message
        self.status_label = ctk.CTkLabel(self, text="", text_color="green")
        self.status_label.grid(row=11, column=0, columnspan=3, pady=(10, 5), sticky="ew")

        self.df = None

    def on_file_type_change(self, value):
        self.file_entry.delete(0, "end")
        self.sheet_menu.configure(state="disabled")
        self.sheet_menu.set("")
        self.sheet_menu.configure(values=[])
        self.df = None

    def browse_file(self):
        from tkinter import filedialog
        filetypes = [("Excel files", "*.xlsx *.xls")] if self.file_type_var.get() == "Excel" else [("CSV files", "*.csv")]
        file_path = filedialog.askopenfilename(filetypes=filetypes)
        if file_path:
            self.file_entry.delete(0, "end")
            self.file_entry.insert(0, file_path)
            if self.file_type_var.get() == "Excel":
                try:
                    sheets = pd.ExcelFile(file_path).sheet_names
                    self.sheet_menu.configure(values=sheets, state="normal")
                    self.sheet_var.set(sheets[0])
                except Exception as e:
                    self.status_label.configure(text=f"Error reading sheets: {e}", text_color="red")
            else:
                self.sheet_menu.configure(state="disabled")
                self.sheet_menu.set("")
                self.sheet_menu.configure(values=[])

    def set_loader(self, show=True):
        self.status_label.configure(text="Processing..." if show else "", text_color="blue" if show else "green")

    def load_dataframe(self):
        file_path = self.file_entry.get()
        if not file_path:
            self.status_label.configure(text="Please select a file.", text_color="red")
            return False
        try:
            if self.file_type_var.get() == "Excel":
                sheet = self.sheet_var.get()
                self.df = pd.read_excel(file_path, sheet_name=sheet)
            else:
                self.df = pd.read_csv(file_path)
            return True
        except Exception as e:
            self.status_label.configure(text=f"Error loading file: {e}", text_color="red")
            return False

    def clean_empty(self):
        def task():
            self.set_loader(True)
            if not self.load_dataframe():
                self.set_loader(False)
                return
            self.df.dropna(axis=0, how='all', inplace=True)
            self.df.dropna(axis=1, how='all', inplace=True)
            self.df.reset_index(drop=True, inplace=True)

            if any(str(col).startswith("Unnamed") or str(col).strip() == "" for col in self.df.columns):
                new_header = self.df.iloc[0]
                self.df = self.df[1:]
                self.df.columns = new_header
                self.df.reset_index(drop=True, inplace=True)
                self.df.dropna(axis=1, how='all', inplace=True)

            self.status_label.configure(text="✅ Cleaned empty rows and columns.", text_color="green")
            self.set_loader(False)
        threading.Thread(target=task).start()

    def remove_rows_cols(self):
        def task():
            self.set_loader(True)
            if not self.load_dataframe():
                self.set_loader(False)
                return
            try:
                n_rows = int(self.rows_entry.get() or 0)
                n_cols = int(self.cols_entry.get() or 0)
                if n_rows > 0:
                    self.df = self.df.iloc[n_rows:].reset_index(drop=True)
                if n_cols > 0:
                    self.df = self.df.iloc[:, n_cols:]
                self.status_label.configure(text="✅ Selected rows/columns removed.", text_color="green")
            except Exception as e:
                self.status_label.configure(text=f"Error: {e}", text_color="red")
            self.set_loader(False)
        threading.Thread(target=task).start()

    def save_file(self):
        def task():
            self.set_loader(True)
            if self.df is None:
                self.status_label.configure(text="No data to save.", text_color="red")
                self.set_loader(False)
                return
            from tkinter import filedialog
            save_type = self.save_type_var.get()
            filetypes = [("Excel files", "*.xlsx")] if save_type == "Excel" else [("CSV files", "*.csv")]
            def_ext = ".xlsx" if save_type == "Excel" else ".csv"
            file_path = filedialog.asksaveasfilename(defaultextension=def_ext, filetypes=filetypes)
            if file_path:
                try:
                    if save_type == "Excel":
                        self.df.to_excel(file_path, index=False)
                    else:
                        self.df.to_csv(file_path, index=False)
                    self.status_label.configure(text=f"✅ Saved: {os.path.basename(file_path)}", text_color="green")
                except Exception as e:
                    self.status_label.configure(text=f"Save error: {e}", text_color="red")
            self.set_loader(False)
        threading.Thread(target=task).start()

    def save_new_file(self):
        def task():
            self.set_loader(True)
            if self.df is None:
                self.status_label.configure(text="No data to save.", text_color="red")
                self.set_loader(False)
                return
            input_path = self.file_entry.get()
            if not input_path:
                self.status_label.configure(text="No file selected.", text_color="red")
                self.set_loader(False)
                return
            save_type = self.save_type_var.get()
            ext = ".xlsx" if save_type == "Excel" else ".csv"
            dir_name = os.path.dirname(input_path)
            base_name = os.path.splitext(os.path.basename(input_path))[0]
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            new_file_name = f"{base_name}_Cleaned_{timestamp}{ext}"
            new_file_path = os.path.join(dir_name, new_file_name)
            try:
                if save_type == "Excel":
                    self.df.to_excel(new_file_path, index=False)
                else:
                    self.df.to_csv(new_file_path, index=False)
                self.status_label.configure(text=f"✅ Saved: {new_file_name}", text_color="green")
            except Exception as e:
                self.status_label.configure(text=f"Save error: {e}", text_color="red")
            self.set_loader(False)
        threading.Thread(target=task).start()

if __name__ == "__main__":
    ctk.set_appearance_mode("light")  # Light theme for corporate users
    ctk.set_default_color_theme("blue")
    root = ctk.CTk()
    root.title("Excel / CSV Sheet Cleaner Tool")
    frame = SheetCleanerFrame(root)
    frame.pack(fill="both", expand=True, padx=30, pady=30)
    root.configure(bg="systemTransparent" if hasattr(root, "tk") else "white")
    frame.configure(fg_color="transparent")
    root.mainloop()
