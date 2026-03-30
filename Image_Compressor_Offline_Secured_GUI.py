import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image
import shutil  # Import shutil for file copy operation

# Default quality
default_quality = 35

# Function to compress a single image
def compress_image(input_path, output_path, quality, dpi=(72, 72)):
    try:
        with Image.open(input_path) as img:
            img.save(output_path, "JPEG", quality=quality, dpi=dpi)
    except Exception as e:
        # If compression fails, print the error and copy the file instead
        print(f"Failed to compress {input_path}: {e}")
        copy_file(input_path, output_path)

# Function to copy non-image files
def copy_file(input_path, output_path):
    shutil.copy2(input_path, output_path)  # Copy with metadata

# Function to process all images in a directory
def process_directory(input_dir, output_dir, quality):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for root, dirs, files in os.walk(input_dir):
        for file in files:
            input_file_path = os.path.join(root, file)
            relative_path = os.path.relpath(root, input_dir)
            output_file_dir = os.path.join(output_dir, relative_path)
                
            if not os.path.exists(output_file_dir):
                os.makedirs(output_file_dir)

            output_file_path = os.path.join(output_file_dir, file)

            # Check if the file is an image (jpg, jpeg, png)
            if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                compress_image(input_file_path, output_file_path, quality)
            else:
                copy_file(input_file_path, output_file_path)  # Copy non-image files

# Function to run compression in a separate thread
def start_compression():
    global input_directory, output_directory

    if not input_directory or not output_directory:
        messagebox.showwarning("Warning", "Please select both input and output folders!")
        return

    try:
        # Validate custom quality input
        quality = int(quality_entry.get())
        if quality < 1 or quality > 100:
            raise ValueError
        
    except ValueError:
        messagebox.showwarning("Invalid Input", "Please enter a valid quality between 1 and 100.")
        return

    # Disable button during processing
    compress_btn.config(text="Compressing...", state=tk.DISABLED)

    def run():
        process_directory(input_directory, output_directory, quality)
        compress_btn.config(text="Compress", state=tk.NORMAL)
        messagebox.showinfo("Success", "Image compression completed!")

    # Start compression in a separate thread
    thread = threading.Thread(target=run)
    thread.start()

# Function to select input directory
def select_input_directory():
    global input_directory
    input_directory = filedialog.askdirectory()
    input_label.config(text=f"Input Folder: {input_directory}" if input_directory else "No Folder Selected")

# Function to select output directory
def select_output_directory():
    global output_directory
    output_directory = filedialog.askdirectory()
    output_label.config(text=f"Output Folder: {output_directory}" if output_directory else "No Folder Selected")

# Initialize GUI window
root = tk.Tk()
root.title("Image Compression Tool")
root.geometry("500x350")
root.resizable(False, False)

# Heading
heading = tk.Label(root, text="TRPW", font=("Arial", 14, "bold"))
heading.pack(pady=10)
heading = tk.Label(root, text="Image Compression Tool", font=("Arial", 14, "bold"))
heading.pack(pady=10)

# Input Folder Selection
input_btn = tk.Button(root, text="Select Input Folder", command=select_input_directory)
input_btn.pack(pady=5)
input_label = tk.Label(root, text="No Folder Selected", wraplength=450)
input_label.pack()

# Output Folder Selection
output_btn = tk.Button(root, text="Select Output Folder", command=select_output_directory)
output_btn.pack(pady=5)
output_label = tk.Label(root, text="No Folder Selected", wraplength=450)
output_label.pack()

# Quality Selection
quality_label = tk.Label(root, text="Recommended Quality: 35% (Enter Custom 1-100)", font=("Arial", 10))
quality_label.pack(pady=5)
quality_entry = tk.Entry(root, width=10, justify="center")
quality_entry.insert(0, str(default_quality))  # Default value is 35
quality_entry.pack()

# Compress Button
compress_btn = tk.Button(root, text="Compress", command=start_compression, bg="#c16d18", fg="white", font=("Arial", 12, "bold"))
compress_btn.pack(pady=20)

# Run the GUI event loop
root.mainloop()
