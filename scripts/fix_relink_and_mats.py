import os, json, collections

MODELS_DIR = r"D:\God of War Ragnarok_extracted\models"

# === 1. Build global DDS index ===
print("=== Building global DDS index... ===")
global_dds = {}  # hash -> path
for region in sorted(os.listdir(MODELS_DIR)):
    rpath = os.path.join(MODELS_DIR, region)
    if not os.path.isdir(rpath):
        continue
    for root, dirs, files in os.walk(rpath):
        for f in files:
            if f.endswith('.dds'):
                h = f[:-4]
                if h not in global_dds:
                    global_dds[h] = os.path.join(root, f)
print(f"Global DDS: {len(global_dds)} unique")

# === 2. Build global MAT index ===
print("=== Building global MAT index... ===")
global_mat = {}  # mat_name -> path
for region in sorted(os.listdir(MODELS_DIR)):
    rpath = os.path.join(MODELS_DIR, region)
    if not os.path.isdir(rpath):
        continue
    for wad in sorted(os.listdir(rpath)):
        wpath = os.path.join(rpath, wad)
        if not os.path.isdir(wpath):
            continue
        mat_dir = os.path.join(wpath, "materials")
        if os.path.isdir(mat_dir):
            for f in os.listdir(mat_dir):
                if f.endswith('.mat'):
                    if f not in global_mat:
                        global_mat[f] = os.path.join(mat_dir, f)
                elif f.endswith('.tx'):
                    pass  # TX files tracked separately
print(f"Global MAT: {len(global_mat)} unique")

# === 3. Fix: relink missing DDS and MAT files ===
print("\n=== Fixing missing DDS and MAT files... ===")
dds_relinked = 0
dds_failed = 0
mat_relinked = 0
mat_failed = 0
mappings_updated = 0

for region in sorted(os.listdir(MODELS_DIR)):
    rpath = os.path.join(MODELS_DIR, region)
    if not os.path.isdir(rpath):
        continue
    for wad in sorted(os.listdir(rpath)):
        wpath = os.path.join(rpath, wad)
        if not os.path.isdir(wpath):
            continue
        
        map_file = os.path.join(wpath, "material_mapping.json")
        if not os.path.isfile(map_file):
            continue
        
        try:
            with open(map_file, 'r') as f:
                mapping = json.load(f)
        except:
            continue
        
        tex_dir = os.path.join(wpath, "textures")
        mat_dir = os.path.join(wpath, "materials")
        
        changed = False
        
        # Fix DDS
        for mesh_entry in mapping.get("meshes", []):
            for tex in mesh_entry.get("textures", []):
                dds_hash = tex.get("dds_hash", "") or tex.get("hash", "")
                if not dds_hash:
                    continue
                dds_file = os.path.join(tex_dir, dds_hash + ".dds")
                if not os.path.isfile(dds_file):
                    # Try to find in global index
                    if dds_hash in global_dds:
                        src = global_dds[dds_hash]
                        os.makedirs(tex_dir, exist_ok=True)
                        try:
                            # Create hard link (same D: volume)
                            os.link(src, dds_file)
                            dds_relinked += 1
                            if not tex.get("found", False):
                                tex["found"] = True
                                changed = True
                        except FileExistsError:
                            pass
                        except Exception as e:
                            dds_failed += 1
        
        # Fix MAT
        for mesh_entry in mapping.get("meshes", []):
            for mat_detail in mesh_entry.get("mat_details", []):
                mat_name = mat_detail.get("name", "")
                if not mat_name:
                    continue
                mat_file = mat_name + ".mat"
                dest_mat = os.path.join(mat_dir, mat_file)
                if not os.path.isfile(dest_mat):
                    if mat_file in global_mat:
                        src = global_mat[mat_file]
                        os.makedirs(mat_dir, exist_ok=True)
                        try:
                            os.link(src, dest_mat)
                            mat_relinked += 1
                        except FileExistsError:
                            pass
                        except:
                            mat_failed += 1
                    # Also link .tx file if exists
                    tx_file = mat_name + ".tx"
                    if tx_file in global_mat:
                        # Check global_mat only has .mat, search separately
                        pass
        
        # Also link .tx files for MATs
        if os.path.isdir(mat_dir):
            existing_tx = set(f for f in os.listdir(mat_dir) if f.endswith('.tx'))
            # Build tx index on the fly for this wad's mats
            for mesh_entry in mapping.get("meshes", []):
                for mat_detail in mesh_entry.get("mat_details", []):
                    mat_name = mat_detail.get("name", "")
                    tx_file = mat_name + ".tx"
                    if tx_file not in existing_tx:
                        # Search global for this tx
                        for reg2 in os.listdir(MODELS_DIR):
                            rp2 = os.path.join(MODELS_DIR, reg2)
                            if not os.path.isdir(rp2):
                                continue
                            for wad2 in os.listdir(rp2):
                                wp2 = os.path.join(rp2, wad2)
                                if not os.path.isdir(wp2):
                                    continue
                                src_tx = os.path.join(wp2, "materials", tx_file)
                                if os.path.isfile(src_tx):
                                    dest_tx = os.path.join(mat_dir, tx_file)
                                    try:
                                        os.link(src_tx, dest_tx)
                                        existing_tx.add(tx_file)
                                    except:
                                        pass
                                    break
        
        if changed:
            try:
                with open(map_file, 'w') as f:
                    json.dump(mapping, f, indent=2, ensure_ascii=False)
                mappings_updated += 1
            except:
                pass

print(f"DDS relinked: {dds_relinked}, failed: {dds_failed}")
print(f"MAT relinked: {mat_relinked}, failed: {mat_failed}")
print(f"Mappings updated: {mappings_updated}")