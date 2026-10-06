import os
import zipfile

SOURCE_DIR = r"C:\Users\Aryan\Desktop\heartbeat"
OUTPUT_ZIP = r"C:\Users\Aryan\Desktop\heartbeat_release.zip"

# Folders and files to exclude
EXCLUDE_DIRS = {"__pycache__", "chroma_store", "node_modules", ".git", "data"}
EXCLUDE_FILES = {".env", "heartbeat.db", "debug_chats.py", "debug_memory_audit.py", 
                 "force_purify_guevara.py", "audit_log.txt", "diagnose_history.py",
                 "inspect_db.py", "debug_db.py"}
EXCLUDE_EXTENSIONS = {".db", ".sqlite", ".pyc", ".pyo"}

def should_skip(path):
    parts = path.replace(SOURCE_DIR, "").split(os.sep)
    # Skip excluded directories
    for part in parts:
        if part in EXCLUDE_DIRS:
            return True
    # Skip excluded files by name or extension
    basename = os.path.basename(path)
    if basename in EXCLUDE_FILES:
        return True
    _, ext = os.path.splitext(basename)
    if ext in EXCLUDE_EXTENSIONS:
        return True
    return False

count = 0
with zipfile.ZipFile(OUTPUT_ZIP, 'w', zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk(SOURCE_DIR):
        # Prune excluded directories in-place so os.walk skips them
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        for file in files:
            filepath = os.path.join(root, file)
            if should_skip(filepath):
                continue
            arcname = os.path.relpath(filepath, os.path.dirname(SOURCE_DIR))
            zf.write(filepath, arcname)
            count += 1

print(f"✅ ZIP created: {OUTPUT_ZIP}")
print(f"📦 Total files included: {count}")
size_mb = os.path.getsize(OUTPUT_ZIP) / (1024 * 1024)
print(f"📏 File size: {size_mb:.2f} MB")
