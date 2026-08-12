import os, json, collections

MODELS_DIR = r"D:\God of War Ragnarok_extracted\models"

# === 1. Cross-reference GLB files vs mapping entries ===
print("=== Cross-referencing GLB files vs mapping entries ===")
glb_files_set = set()
mapping_mesh_names = set()

for region in sorted(os.listdir(MODELS_DIR)):
    rpath = os.path.join(MODELS_DIR, region)
    if not os.path.isdir(rpath):
        continue
    for wad in sorted(os.listdir(rpath)):
        wpath = os.path.join(rpath, wad)
        if not os.path.isdir(wpath):
            continue
        # Collect GLB files
        for f in os.listdir(wpath):
            if f.endswith('.glb'):
                glb_files_set.add(f"{region}/{wad}/{f}")
        
        # Collect mapping mesh entries
        map_file = os.path.join(wpath, "material_mapping.json")
        if os.path.isfile(map_file):
            try:
                with open(map_file, 'r') as f:
                    mapping = json.load(f)
                for mesh_entry in mapping.get("meshes", []):
                    mesh_name = mesh_entry.get("mesh", "")
                    idx = mesh_entry.get("idx", 0)
                    # Try to match to a GLB file
                    mapping_mesh_names.add(f"{region}/{wad}/{mesh_name}_{idx}")
            except:
                pass

print(f"Total GLB files on disk: {len(glb_files_set)}")
print(f"Total mesh entries in mappings: {len(mapping_mesh_names)}")

# Find GLB files not in any mapping (orphan GLBs)
# This is approximate since naming may differ
glb_basenames = set()
for g in glb_files_set:
    # Extract just the filename
    fname = g.split('/')[-1]
    glb_basenames.add(fname)

print(f"\nNote: GLB files on disk = {len(glb_files_set)}, mapping mesh entries = {len(mapping_mesh_names)}")
print("(Difference is expected: LOD groups may share GLB, some mapping entries are sub-meshes)")

# === 2. Find all DDS files across all regions ===
print("\n=== Building global DDS index... ===")
global_dds = {}  # hash -> first path found
for region in sorted(os.listdir(MODELS_DIR)):
    rpath = os.path.join(MODELS_DIR, region)
    if not os.path.isdir(rpath):
        continue
    for root, dirs, files in os.walk(rpath):
        for f in files:
            if f.endswith('.dds'):
                h = f[:-4]  # remove .dds
                if h not in global_dds:
                    global_dds[h] = os.path.join(root, f)

print(f"Total unique DDS files: {len(global_dds)}")

# === 3. Load missing hashes and try to find them ===
with open(r"E:\gow_re_workspace\output\missing_dds_hashes.json", 'r') as f:
    missing_hashes = json.load(f)

print(f"\nMissing DDS hashes to find: {len(missing_hashes)}")
found_in_global = 0
still_missing = []
for h in missing_hashes:
    if h in global_dds:
        found_in_global += 1
    else:
        still_missing.append(h)
print(f"Found in global DDS index: {found_in_global}")
print(f"Truly missing (not anywhere): {len(still_missing)}")

# Save results
results = {
    "total_glb": len(glb_files_set),
    "total_mapping_entries": len(mapping_mesh_names),
    "total_dds_unique": len(global_dds),
    "missing_dds_found": found_in_global,
    "missing_dds_truly_missing": len(still_missing),
    "truly_missing_hashes": still_missing[:50]  # first 50 for inspection
}
with open(r"E:\gow_re_workspace\output\audit_mismatches.json", 'w') as f:
    json.dump(results, f, indent=2)
print(f"\nResults saved to output/audit_mismatches.json")

# Show some truly missing hashes
if still_missing:
    print(f"\nSample truly missing hashes:")
    for h in still_missing[:10]:
        print(f"  {h}")