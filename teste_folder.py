from pathlib import Path
import os
import re

def get_next_filename(folder_path):
    files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f)) and re.match(r'^\d+', f)]

    # Extract sequence numbers from file names
    sequence_numbers = [int(re.match(r'^(\d+)_', f).group(1)) for f in files] #type: ignore

    # Get the next sequence number
    next_sequence_number = max(sequence_numbers, default=0) + 1

    # Create your new file name
    new_file_name = f"{next_sequence_number:02d}_your_filename.txt"
    
    return new_file_name

folderpath = r"assets\adb\auto"
next_filename = get_next_filename(folderpath)
print(next_filename)


