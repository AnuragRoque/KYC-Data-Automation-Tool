import csv
import tkinter as tk
from tkinter import filedialog

# Function to generate the next unique identifier
def get_next_unique_identifier(existing_identifiers, base_identifier):
    suffix = 1
    new_identifier = f"{base_identifier}-{suffix}"
    while new_identifier in existing_identifiers:
        suffix += 1
        new_identifier = f"{base_identifier}-{suffix}"
    return new_identifier

def process_csv(input_file_path, output_file_path, column_index):
    # Open the CSV file
    with open(input_file_path, mode='r') as file:
        # Create a CSV reader object
        csv_reader = csv.reader(file)
        header = next(csv_reader)  # Read the header
        data = list(csv_reader)  # Read the rest of the data

    # Process the data to ensure unique identifiers in the specified column
    existing_identifiers = set()
    for row in data:
        base_identifier = row[column_index].rsplit('-', 1)[0]  # Extract the base identifier
        row[column_index] = get_next_unique_identifier(existing_identifiers, base_identifier)
        existing_identifiers.add(row[column_index])

    # Write the updated data to a new CSV file
    with open(output_file_path, mode='w', newline='') as file:
        csv_writer = csv.writer(file)
        csv_writer.writerow(header)  # Write the header
        csv_writer.writerows(data)  # Write the data

def select_input_file():
    input_file_path.set(filedialog.askopenfilename())

def select_output_file():
    output_file_path.set(filedialog.asksaveasfilename(defaultextension=".csv"))

def generate():
    process_csv(input_file_path.get(), output_file_path.get(), int(column_index.get()))

# Create the main window
root = tk.Tk()
root.title("CSV Unique Identifier Generator")

# Input file selection
tk.Label(root, text="Input File:").grid(row=0, column=0, padx=10, pady=5)
input_file_path = tk.StringVar()
tk.Entry(root, textvariable=input_file_path, width=50).grid(row=0, column=1, padx=10, pady=5)
tk.Button(root, text="Select File", command=select_input_file).grid(row=0, column=2, padx=10, pady=5)

# Output file selection
tk.Label(root, text="Output File:").grid(row=1, column=0, padx=10, pady=5)
output_file_path = tk.StringVar()
tk.Entry(root, textvariable=output_file_path, width=50).grid(row=1, column=1, padx=10, pady=5)
tk.Button(root, text="Select File", command=select_output_file).grid(row=1, column=2, padx=10, pady=5)

# Column index selection
tk.Label(root, text="Column Index (starts from 0):").grid(row=2, column=0, padx=10, pady=5)
column_index = tk.StringVar()
tk.Entry(root, textvariable=column_index, width=5).grid(row=2, column=1, padx=10, pady=5)

# Generate button
tk.Button(root, text="Generate", command=generate).grid(row=3, column=1, padx=10, pady=20)

# Run the application
root.mainloop()