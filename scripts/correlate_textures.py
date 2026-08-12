import os, json, time, shutil, re

MODELS_DIR = r"D:\God of War Ragnarok_extracted\models"
MAPPING_PATH = r"E:\gow_re_workspace\output\model_texture_mapping.json"

# === Step 1: Build DDS hash -> file path index ===
print("Building DDS hash -> file path index...")
dds_index = {}  # hash_str -> full_path
t0 = time.time()

for root, dirs, files in os.walk(MODELS_DIR):
    for f in files:
        if f.endswith(".dds"):
            # DDS filename is the hash: XXXXXXXXXXXXXXXX.dds
            hash_str = os.path.splitext(f)[0].upper()
            dds_index[hash_str] = os.path.join(root, f)

print(f"  Indexed {len(dds_index)} DDS files in {time.time()-t0:.1f}s")

# === Step 2: Load mapping ===
print("Loading mapping...")
with open(MAPPING_PATH, "r") as f:
    mapping_data = json.load(f)

mapping = mapping_data["mapping"]
print(f"  Loaded mapping for {len(mapping)} WADs")

# === Step 3: For each WAD with meshes, copy textures and create mapping ===
print("\nProcessing WADs...")

stats = {"wads_with_tex": 0, "tex_copied": 0, "tex_missing": 0, 
         "tex_skipped": 0, "total_unique_tex": 0}

# Find which region each WAD belongs to
wad_to_region = {}
for region in os.listdir(MODELS_DIR):
    region_path = os.path.join(MODELS_DIR, region)
    if not os.path.isdir(region_path): continue
    for wad_dir in os.listdir(region_path):
        wad_full = os.path.join(region_path, wad_dir)
        if os.path.isdir(wad_full):
            # Check if this dir has GLB files
            has_glb = any(f.endswith(".glb") for f in os.listdir(wad_full))
            if has_glb:
                wad_to_region[wad_dir] = region

print(f"  Found {len(wad_to_region)} WAD directories with GLB files")

t0 = time.time()
processed = 0

for wad_base, mesh_maps in mapping.items():
    if not mesh_maps:
        continue
    
    # Find the WAD directory on disk
    region = wad_to_region.get(wad_base)
    if not region:
        # Try to find it
        for r in os.listdir(MODELS_DIR):
            p = os.path.join(MODELS_DIR, r, wad_base)
            if os.path.isdir(p):
                region = r
                wad_to_region[wad_base] = r
                break
    
    if not region:
        continue
    
    wad_dir = os.path.join(MODELS_DIR, region, wad_base)
    if not os.path.isdir(wad_dir):
        continue
    
    # Collect all unique DDS hashes for this WAD
    unique_dds = {}  # hash -> tex_type
    for m in mesh_maps:
        for t in m["textures"]:
            h = t["hash"]
            if h not in unique_dds:
                unique_dds[h] = t["type"]
    
    if not unique_dds:
        continue
    
    stats["wads_with_tex"] += 1
    stats["total_unique_tex"] += len(unique_dds)
    
    # Create textures subdirectory
    tex_dir = os.path.join(wad_dir, "textures")
    os.makedirs(tex_dir, exist_ok=True)
    
    # Copy DDS files
    for hash_str, tex_type in unique_dds.items():
        src = dds_index.get(hash_str)
        if src:
            dst = os.path.join(tex_dir, f"{hash_str}.dds")
            if os.path.exists(dst):
                stats["tex_skipped"] += 1
            else:
                try:
                    shutil.copy2(src, dst)
                    stats["tex_copied"] += 1
                except Exception as ex:
                    stats["tex_missing"] += 1
        else:
            stats["tex_missing"] += 1
    
    # Create per-WAD mapping JSON with MAT info
    wad_mapping = {
        "wad": wad_base,
        "region": region,
        "meshes": []
    }
    for m in mesh_maps:
        glb_files = []
        # Find GLB files for this mesh entry
        for f in os.listdir(wad_dir):
            if f.endswith(".glb") and f"_{m['idx']}." in f:
                glb_files.append(f)
        
        wad_mapping["meshes"].append({
            "mesh_name": m["mesh"],
            "entry_idx": m["idx"],
            "materials": m["mats"],
            "glb_files": glb_files,
            "textures": m["textures"]
        })
    
    map_path = os.path.join(wad_dir, "material_mapping.json")
    with open(map_path, "w") as f:
        json.dump(wad_mapping, f, indent=2)
    
    processed += 1
    if processed % 50 == 0:
        elapsed = time.time() - t0
        print(f"  [{processed}] {wad_base[:35]:<35} tex={len(unique_dds):<4} "
              f"copied={stats['tex_copied']} missing={stats['tex_missing']} "
              f"({elapsed:.0f}s)")

elapsed = time.time() - t0
print(f"\n=== DONE in {elapsed:.1f}s ===")
print(f"WADs with textures: {stats['wads_with_tex']}")
print(f"Total unique texture refs: {stats['total_unique_tex']}")
print(f"Textures copied: {stats['tex_copied']}")
print(f"Textures skipped (already exist): {stats['tex_skipped']}")
print(f"Textures missing (not found): {stats['tex_missing']}")