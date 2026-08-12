import os, json, hashlib, collections

MODELS_DIR = r"D:\God of War Ragnarok_extracted\models"

# === 1. Collect all GLB files ===
print("=== Scanning all GLB files... ===")
all_glbs = []  # (full_path, region, wad, filename, size)
region_stats = collections.Counter()
wad_dirs = []

for region in sorted(os.listdir(MODELS_DIR)):
    rpath = os.path.join(MODELS_DIR, region)
    if not os.path.isdir(rpath):
        continue
    for wad in sorted(os.listdir(rpath)):
        wpath = os.path.join(rpath, wad)
        if not os.path.isdir(wpath):
            continue
        wad_dirs.append((region, wad, wpath))
        for f in os.listdir(wpath):
            if f.endswith('.glb'):
                fpath = os.path.join(wpath, f)
                size = os.path.getsize(fpath)
                all_glbs.append((fpath, region, wad, f, size))
                region_stats[region] += 1

print(f"Total GLB: {len(all_glbs)}")
print("Per region:")
for r, c in sorted(region_stats.items()):
    print(f"  {r}: {c}")

# === 2. Check duplicates by filename ===
print("\n=== Checking duplicate filenames... ===")
fname_map = collections.defaultdict(list)
for fp, region, wad, fname, size in all_glbs:
    fname_map[fname].append((region, wad, size))

dup_filenames = {k: v for k, v in fname_map.items() if len(v) > 1}
print(f"Duplicate filenames: {len(dup_filenames)}")
if dup_filenames:
    # Check if they're true duplicates (same size) or different content with same name
    true_dups = 0
    diff_content_same_name = 0
    for fname, entries in list(dup_filenames.items())[:20]:
        sizes = set(e[2] for e in entries)
        if len(sizes) == 1:
            true_dups += 1
        else:
            diff_content_same_name += 1
    print(f"  Same name + same size (true dups): {true_dups} (in first 20)")
    print(f"  Same name + diff size: {diff_content_same_name} (in first 20)")
    # Show a few examples
    for fname, entries in list(dup_filenames.items())[:5]:
        print(f"  Example: {fname}")
        for r, w, s in entries:
            print(f"    {r}/{w} size={s}")

# === 3. Check duplicates by content hash (for same-size same-name) ===
if dup_filenames:
    print("\n=== Hashing true duplicate candidates... ===")
    hashed = 0
    confirmed_dups = 0
    for fname, entries in dup_filenames.items():
        sizes = set(e[2] for e in entries)
        if len(sizes) == 1:
            # Hash first 4KB to check
            hashes = []
            for r, w, s in entries:
                fp = os.path.join(MODELS_DIR, r, w, fname)
                h = hashlib.md5()
                with open(fp, 'rb') as fh:
                    h.update(fh.read(4096))
                hashes.append(h.hexdigest())
            if len(set(hashes)) == 1:
                confirmed_dups += 1
            hashed += 1
            if hashed <= 5:
                print(f"  {fname}: hash_match={len(set(hashes))==1}")
    print(f"Confirmed duplicates (same name+size+hash): {confirmed_dups} out of {hashed} checked")

# === 4. Check texture coverage ===
print("\n=== Checking texture coverage... ===")
total_meshes = 0
meshes_with_tex = 0
meshes_without_tex = 0
meshes_without_mapping = 0

for region, wad, wpath in wad_dirs:
    map_file = os.path.join(wpath, "material_mapping.json")
    if not os.path.isfile(map_file):
        meshes_without_mapping += len([f for f in os.listdir(wpath) if f.endswith('.glb')])
        continue
    try:
        with open(map_file, 'r') as f:
            mapping = json.load(f)
    except:
        meshes_without_mapping += len([f for f in os.listdir(wpath) if f.endswith('.glb')])
        continue
    
    for mesh_entry in mapping.get("meshes", []):
        total_meshes += 1
        tex_list = mesh_entry.get("textures", [])
        if tex_list and any(t.get("found", False) for t in tex_list):
            meshes_with_tex += 1
        else:
            meshes_without_tex += 1

print(f"Total meshes in mappings: {total_meshes}")
print(f"Meshes with textures: {meshes_with_tex} ({100*meshes_with_tex/max(total_meshes,1):.1f}%)")
print(f"Meshes without textures: {meshes_without_tex} ({100*meshes_without_tex/max(total_meshes,1):.1f}%)")
print(f"Meshes without mapping file: {meshes_without_mapping}")

# === 5. Check MAT coverage ===
print("\n=== Checking MAT coverage... ===")
total_mats_in_mapping = 0
mats_with_file = 0
mats_without_file = 0

for region, wad, wpath in wad_dirs:
    map_file = os.path.join(wpath, "material_mapping.json")
    if not os.path.isfile(map_file):
        continue
    try:
        with open(map_file, 'r') as f:
            mapping = json.load(f)
    except:
        continue
    
    mat_dir = os.path.join(wpath, "materials")
    mat_files = set()
    if os.path.isdir(mat_dir):
        mat_files = set(os.listdir(mat_dir))
    
    for mesh_entry in mapping.get("meshes", []):
        for mat_detail in mesh_entry.get("mat_details", []):
            mat_name = mat_detail.get("name", "")
            total_mats_in_mapping += 1
            if mat_name + ".mat" in mat_files:
                mats_with_file += 1
            else:
                mats_without_file += 1

print(f"Total MAT refs in mappings: {total_mats_in_mapping}")
print(f"MAT files found: {mats_with_file} ({100*mats_with_file/max(total_mats_in_mapping,1):.1f}%)")
print(f"MAT files missing: {mats_without_file} ({100*mats_without_file/max(total_mats_in_mapping,1):.1f}%)")

# === 6. Check texture files exist ===
print("\n=== Checking DDS file existence... ===")
total_tex_refs = 0
tex_found = 0
tex_missing = 0
missing_hashes = set()

for region, wad, wpath in wad_dirs:
    map_file = os.path.join(wpath, "material_mapping.json")
    if not os.path.isfile(map_file):
        continue
    try:
        with open(map_file, 'r') as f:
            mapping = json.load(f)
    except:
        continue
    
    tex_dir = os.path.join(wpath, "textures")
    
    for mesh_entry in mapping.get("meshes", []):
        for tex in mesh_entry.get("textures", []):
            total_tex_refs += 1
            dds_hash = tex.get("dds_hash", "")
            if not dds_hash:
                dds_hash = tex.get("hash", "")
            if dds_hash:
                dds_file = os.path.join(tex_dir, dds_hash + ".dds")
                if os.path.isfile(dds_file):
                    tex_found += 1
                else:
                    tex_missing += 1
                    missing_hashes.add(dds_hash)
            else:
                tex_missing += 1

print(f"Total texture refs: {total_tex_refs}")
print(f"DDS files found: {tex_found} ({100*tex_found/max(total_tex_refs,1):.1f}%)")
print(f"DDS files missing: {tex_missing} ({100*tex_missing/max(total_tex_refs,1):.1f}%)")
print(f"Unique missing hashes: {len(missing_hashes)}")

# === Summary ===
print("\n" + "="*60)
print("AUDIT SUMMARY")
print("="*60)
print(f"Total GLB files: {len(all_glbs)}")
print(f"Duplicate filenames: {len(dup_filenames)}")
print(f"Meshes with textures: {meshes_with_tex}/{total_meshes} ({100*meshes_with_tex/max(total_meshes,1):.1f}%)")
print(f"MAT files found: {mats_with_file}/{total_mats_in_mapping} ({100*mats_with_file/max(total_mats_in_mapping,1):.1f}%)")
print(f"DDS files found: {tex_found}/{total_tex_refs} ({100*tex_found/max(total_tex_refs,1):.1f}%)")
print(f"Meshes without mapping: {meshes_without_mapping}")

# Save missing hashes for later fix
if missing_hashes:
    with open(r"E:\gow_re_workspace\output\missing_dds_hashes.json", 'w') as f:
        json.dump(sorted(list(missing_hashes)), f, indent=2)
    print(f"\nMissing DDS hashes saved to output/missing_dds_hashes.json")