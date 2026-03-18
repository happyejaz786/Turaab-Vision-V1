import os
import shutil

def organize_junk(target_path):
    # Categories define karein
    extensions = {
        'Images': ['.jpg', '.jpeg', '.png', '.gif'],
        'Documents': ['.pdf', '.docx', '.txt', '.xlsx', '.pptx'],
        'Software': ['.exe', '.msi'],
        'Archives': ['.zip', '.rar']
    }

    for filename in os.listdir(target_path):
        filepath = os.path.join(target_path, filename)
        
        # Folder ko skip karein
        if os.path.isdir(filepath):
            continue
            
        # Extension check karein
        file_ext = os.path.splitext(filename)[1].lower()
        
        for category, exts in extensions.items():
            if file_ext in exts:
                dest_dir = os.path.join(target_path, category)
                # Agar category folder nahi hai toh bana dein
                if not os.path.exists(dest_dir):
                    os.makedirs(dest_dir)
                
                shutil.move(filepath, os.path.join(dest_dir, filename))
                print(f"Moved {filename} to {category}")
                break

# Test ke liye: organize_junk("D:/Turaab_Test")