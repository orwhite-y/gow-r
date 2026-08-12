import os, sys
sys.stdout.reconfigure(encoding='utf-8')

MODELS_DIR = r"D:\God of War Ragnarok_extracted\models"

# Separate files by type and location
glb_size = 0; glb_count = 0
dds_unique_size = 0; dds_unique_count = 0  # In texpack dirs
dds_linked_size = 0; dds_linked_count = 0  # In WAD texture dirs (hard links)
mat_size = 0; mat_count = 0
tx_size = 0; tx_count = 0
json_size = 0; json_count = 0

for root, dirs, files in os.walk(MODELS_DIR):
    rel = os.path.relpath(root, MODELS_DIR)
    is_texpack = "\\textures\\" in rel + "\\" and not "\\textures\\materials" in rel + "\\"
    
    # Check if this is a texpack texture dir (region/textures/texpack_name)
    parts = rel.replace("\\", "/").split("/")
    is_texpack_tex = len(parts) == 3 and parts[1] == "textures"
    is_wad_tex = len(parts) == 3 and parts[2] == "textures"
    
    for f in files:
        fp = os.path.join(root, f)
        try:
            sz = os.path.getsize(fp)
        except: continue
        fl = f.lower()
        
        if fl.endswith(".glb"):
            glb_size += sz; glb_count += 1
        elif fl.endswith(".dds"):
            if is_texpack_tex:
                dds_unique_size += sz; dds_unique_count += 1
            else:
                dds_linked_size += sz; dds_linked_count += 1
        elif fl.endswith(".mat"):
            mat_size += sz; mat_count += 1
        elif fl.endswith(".tx"):
            tx_size += sz; tx_count += 1
        elif fl.endswith(".json"):
            json_size += sz; json_count += 1

print("=== File breakdown ===")
print(f"GLB models:     {glb_count:>8} files, {glb_size/1024/1024/1024:.1f} GB")
print(f"DDS (unique):   {dds_unique_count:>8} files, {dds_unique_size/1024/1024/1024:.1f} GB")
print(f"DDS (hardlink): {dds_linked_count:>8} files, {dds_linked_size/1024/1024/1024:.1f} GB (shared, 0 extra disk)")
print(f"MAT files:      {mat_count:>8} files, {mat_size/1024/1024:.1f} MB")
print(f"TX files:       {tx_count:>8} files, {tx_size/1024/1024:.1f} MB")
print(f"JSON files:     {json_count:>8} files, {json_size/1024/1024:.1f} MB")
print(f"\nActual unique data: {(glb_size+dds_unique_size+mat_size+tx_size+json_size)/1024/1024/1024:.1f} GB")
print(f"  GLB: {glb_size/1024/1024/1024:.1f} GB")
print(f"  DDS (unique): {dds_unique_size/1024/1024/1024:.1f} GB")
print(f"  MAT+TX+JSON: {(mat_size+tx_size+json_size)/1024/1024:.1f} MB")