import os
import json

class TuraabFileEngine:
    def __init__(self):
        self.index_file = "system_index.json"
        self.drives = self._get_available_drives()

    def _get_available_drives(self):
        import os
        drives = []
        
        # Check if system is Windows ('nt' means Windows)
        if os.name == 'nt':
            import string
            from ctypes import windll
            try:
                bitmask = windll.kernel32.GetLogicalDrives()
                for letter in string.ascii_uppercase:
                    if bitmask & 1:
                        drives.append(f"{letter}:\\")
                    bitmask >>= 1
            except Exception:
                pass
        else:
            # If it's Streamlit Cloud (Linux), don't look for C: or D: drives
            drives = ['/'] 
            
        return drives

    def v23_smart_scan(self):
        full_index = []
        try:
            for drive in self.drives:
                for root, dirs, files in os.walk(drive):
                    if any(x in root for x in ["$RECYCLE.BIN", "System Volume Information"]):
                        continue
                    
                    # NEW: Folders ko bhi index mein shamil kar rahe hain
                    for d in dirs:
                        full_index.append({
                            "name": d.lower(),
                            "path": os.path.join(root, d),
                            "type": "Folder"
                        })
                        
                    # Files indexing
                    for f in files:
                        full_index.append({
                            "name": f.lower(),
                            "path": os.path.join(root, f),
                            "type": "File"
                        })
            
            with open(self.index_file, "w") as f:
                json.dump(full_index, f)
            return f"Indexing complete. {len(full_index)} items indexed."
        except Exception as e:
            return f"Scan Error: {str(e)}"

    def v24_deep_search(self, query):
        if not os.path.exists(self.index_file):
            return []
        query = query.lower()
        with open(self.index_file, "r") as f:
            index_data = json.load(f)
        return [item for item in index_data if query in item["name"]]
