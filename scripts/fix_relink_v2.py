import os, json, sys

MODELS_DIR = r"D:\God of War Ragnarok_extracted\models"

# === 1. Build global indexes in single pass ===
print("Building global DDS/MAT/TX indexes...", flush=True)
global_dds = {}   # hash -> path
global_mat = {}   # "MAT_xxx.mat" -> path
global_tx = {}    # "MAT_xxx.tx" -> path

wad_list = []  # (region, wad, wpath)

for region in sorted(os.listdir(MODELS_DIR)):
    rpath = os.path.join(MODELS_DIR, region)
    if not os.path.isdir(rpath):
        continue
    for wad in sorted(os.listdir(rpath)):
        wpath = os.path.join(rpath, wad)
        if not os.path.isdir(wpath):
            continue
        wad_list.append((region, wad, wpath))
        
        # Index textures dir
        tex_dir = os.path.join(wpath, "textures")
        if os.path.isdir(tex_dir):
            for f in os.listdir(tex_dir):
                if f.endswith('.dds'):
                    h = f[:-4]
                    if h not in global_dds:
                        global_dds[h] = os.path.join(tex_dir, f)
        
        # Index materials dir
        mat_dir = os.path.join(wpath, "materials")
        if os.path.isdir(mat_dir):
            for f in os.listdir(mat_dir):
                if f.endswith('.mat'):
                    if f not in global_mat:
                        global_mat[f] = os.path.join(mat_dir, f)
                elif f.endswith('.tx'):
                    if f not in global_tx:
                        global_tx[f] = os.path.join(mat_dir, f)

# Also index region-level textures (texpack)
for region in sorted(os.listdir(MODELS_DIR)):
    rpath = os.path.join(MODELS_DIR, region)
    if not os.path.isdir(rpath):
        continue
    rtex = os.path.join(rpath, "textures")
    if os.path.isdir(rtex):
        for root, dirs, files in os.walk(rtex):
            for f in files:
                if f.endswith('.dds'):
                    h = f[:-4]
                    if h not in global_dds:
                        global_dds[h] = os.path.join(root, f)

print(f"Indexes: DDS={len(global_dds)}, MAT={len(global_mat)}, TX={len(global_tx)}", flush=True)
print(f"WAD dirs to process: {len(wad_list)}", flush=True)

# === 2. Fix: relink missing DDS, MAT, TX ===
print("Relinking missing files...", flush=True)
dds_relinked = 0
mat_relinked = 0
tx_relinked = 0
mappings_updated = 0
processed = 0

for region, wad, wpath in wad_list:
    processed += 1
    if processed % 200 == 0:
        print(f"  Progress: {processed}/{len(wad_list)}...", flush=True)
    
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
    
    # Ensure dirs exist
    os.makedirs(tex_dir, exist_ok=True)
    os.makedirs(mat_dir, exist_ok=True)
    
    changed = False
    needed_dds = set()
    needed_mat = set()
    needed_tx = set()
    
    # Collect what's needed
    for mesh_entry in mapping.get("meshes", []):
        for tex in mesh_entry.get("textures", []):
            dds_hash = tex.get("dds_hash", "") or tex.get("hash", "")
            if dds_hash:
                needed_dds.add(dds_hash)
        for mat_detail in mesh_entry.get("mat_details", []):
            mat_name = mat_detail.get("name", "")
            if mat_name:
                needed_mat.add(mat_name + ".mat")
                needed_tx.add(mat_name + ".tx")
    
    # Check what's already present
    existing_dds = set(f[:-4] for f in os.listdir(tex_dir) if f.endswith('.dds')) if os.path.isdir(tex_dir) else set()
    existing_mat = set(os.listdir(mat_dir)) if os.path.isdir(mat_dir) else set()
    
    # Relink DDS
    for h in needed_dds:
        if h not in existing_dds and h in global_dds:
            try:
                os.link(global_dds[h], os.path.join(tex_dir, h + ".dds"))
                dds_relinked += 1
            except FileExistsError:
                pass
            except:
                pass
    
    # Relink MAT
    for mf in needed_mat:
        if mf not in existing_mat and mf in global_mat:
            try:
                os.link(global_mat[mf], os.path.join(mat_dir, mf))
                mat_relinked += 1
            except FileExistsError:
                pass
            except:
                pass
    
    # Relink TX
    for tf in needed_tx:
        if tf not in existing_mat and tf in global_tx:
            try:
                os.link(global_tx[tf], os.path.join(mat_dir, tf))
                tx_relinked += 1
            except FileExistsError:
                pass
            except:
                pass
    
    # Update mapping found flags
    for mesh_entry in mapping.get("meshes", []):
        for tex in mesh_entry.get("textures", []):
            dds_hash = tex.get("dds_hash", "") or tex.get("hash", "")
            if dds_hash and not tex.get("found", False):
                dds_file = os.path.join(tex_dir, dds_hash + ".dds")
                if os.path.isfile(dds_file):
                    tex["found"] = True
                    changed = True
    
    if changed:
        try:
            with open(map_file, 'w') as f:
                json.dump(mapping, f, indent=2, ensure_ascii=False)
            mappings_updated += 1
        except:
            pass

print(f"\nDone!", flush=True)
print(f"DDS relinked: {dds_relinked}")
print(f"MAT relinked: {mat_relinked}")
print(f"TX relinked: {tx_relinked}")
print(f"Mappings updated: {mappings_updated}")