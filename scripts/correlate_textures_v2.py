import os, json, time, re

MODELS_DIR = r"D:\God of War Ragnarok_extracted\models"
MAPPING_PATH = r"E:\gow_re_workspace\output\model_texture_mapping.json"
DDS_CACHE = r"E:\gow_re_workspace\output\dds_index.json"

# === Step 1: Build or load DDS hash -> file path index ===
if os.path.exists(DDS_CACHE):
    print("Loading cached DDS index...")
    with open(DDS_CACHE, "r") as f:
        dds_index = json.load(f)
    print(f"  Loaded {len(dds_index)} DDS paths from cache")
else:
    print("Building DDS hash -> file path index...")
    dds_index = {}
    t0 = time.time()
    for root, dirs, files in os.walk(MODELS_DIR):
        # Skip textures subdirectories inside WAD dirs (we only want the original DDS locations)
        for f in files:
            if f.endswith(".dds"):
                hash_str = os.path.splitext(f)[0].upper()
                if hash_str not in dds_index:  # keep first found
                    dds_index[hash_str] = os.path.join(root, f)
    print(f"  Indexed {len(dds_index)} DDS files in {time.time()-t0:.1f}s")
    with open(DDS_CACHE, "w") as f:
        json.dump(dds_index, f)
    print(f"  Cache saved to {DDS_CACHE}")

# === Step 2: Load mapping ===
print("Loading mapping...")
with open(MAPPING_PATH, "r") as f:
    mapping_data = json.load(f)
mapping = mapping_data["mapping"]

# === Step 3: Build WAD -> region mapping ===
print("Building WAD -> region mapping...")
wad_to_region = {}
wad_to_dir = {}
for region in os.listdir(MODELS_DIR):
    region_path = os.path.join(MODELS_DIR, region)
    if not os.path.isdir(region_path): continue
    for wad_dir in os.listdir(region_path):
        wad_full = os.path.join(region_path, wad_dir)
        if os.path.isdir(wad_full):
            wad_to_region[wad_dir] = region
            wad_to_dir[wad_dir] = wad_full

print(f"  Found {len(wad_to_region)} WAD directories")

# === Step 4: Process each WAD ===
print("\nProcessing WADs...")
stats = {"wads_done": 0, "wads_skipped": 0, "tex_linked": 0, "tex_missing": 0,
         "tex_exists": 0, "total_unique_tex": 0}

t0 = time.time()
for wad_base, mesh_maps in mapping.items():
    if not mesh_maps:
        continue
    
    wad_dir = wad_to_dir.get(wad_base)
    if not wad_dir:
        continue
    
    # Skip if already processed (has material_mapping.json)
    map_path = os.path.join(wad_dir, "material_mapping.json")
    if os.path.exists(map_path):
        stats["wads_skipped"] += 1
        continue
    
    # Collect unique DDS hashes
    unique_dds = {}
    for m in mesh_maps:
        for t in m["textures"]:
            h = t["hash"]
            if h not in unique_dds:
                unique_dds[h] = t["type"]
    
    if not unique_dds:
        # Still create mapping file even without textures
        pass
    
    stats["wads_done"] += 1
    stats["total_unique_tex"] += len(unique_dds)
    
    # Create textures subdirectory and hard-link DDS files
    tex_dir = os.path.join(wad_dir, "textures")
    os.makedirs(tex_dir, exist_ok=True)
    
    for hash_str, tex_type in unique_dds.items():
        src = dds_index.get(hash_str)
        if src and os.path.exists(src):
            dst = os.path.join(tex_dir, f"{hash_str}.dds")
            if os.path.exists(dst):
                stats["tex_exists"] += 1
            else:
                try:
                    os.link(src, dst)  # Hard link - instant!
                    stats["tex_linked"] += 1
                except Exception:
                    try:
                        import shutil
                        shutil.copy2(src, dst)
                        stats["tex_linked"] += 1
                    except Exception:
                        stats["tex_missing"] += 1
        else:
            stats["tex_missing"] += 1
    
    # Create mapping JSON
    wad_mapping = {
        "wad": wad_base,
        "region": wad_to_region.get(wad_base, ""),
        "meshes": []
    }
    for m in mesh_maps:
        wad_mapping["meshes"].append({
            "mesh_name": m["mesh"],
            "entry_idx": m["idx"],
            "materials": m["mats"],
            "textures": m["textures"]
        })
    
    with open(map_path, "w") as f:
        json.dump(wad_mapping, f, indent=2)
    
    if stats["wads_done"] % 100 == 0:
        elapsed = time.time() - t0
        rate = stats["wads_done"] / elapsed if elapsed > 0 else 0
        remaining = len(mapping) - stats["wads_done"] - stats["wads_skipped"]
        eta = remaining / rate if rate > 0 else 0
        print(f"  [{stats['wads_done']+stats['wads_skipped']}/{len(mapping)}] "
              f"done={stats['wads_done']} skipped={stats['wads_skipped']} "
              f"linked={stats['tex_linked']} missing={stats['tex_missing']} "
              f"({rate:.1f} wad/s, ETA {eta:.0f}s)")

elapsed = time.time() - t0
print(f"\n=== DONE in {elapsed:.1f}s ===")
print(f"WADs processed: {stats['wads_done']}")
print(f"WADs skipped (already done): {stats['wads_skipped']}")
print(f"Textures linked: {stats['tex_linked']}")
print(f"Textures already exist: {stats['tex_exists']}")
print(f"Textures missing: {stats['tex_missing']}")
print(f"Total unique texture refs: {stats['total_unique_tex']}")