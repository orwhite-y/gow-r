import os, json

MODELS_DIR = r"D:\God of War Ragnarok_extracted\models"

# Find all WAD dirs that have material_mapping.json but 0 GLB files
print("=== Scanning for dirs with mapping but no GLB ===", flush=True)
missing_dirs = []
total_dirs = 0
total_with_glb = 0

for region in sorted(os.listdir(MODELS_DIR)):
    rpath = os.path.join(MODELS_DIR, region)
    if not os.path.isdir(rpath) or region.startswith("_"):
        continue
    for wad in sorted(os.listdir(rpath)):
        wpath = os.path.join(rpath, wad)
        if not os.path.isdir(wpath) or wad == "textures":
            continue
        total_dirs += 1
        
        has_mapping = os.path.isfile(os.path.join(wpath, "material_mapping.json"))
        glb_files = [f for f in os.listdir(wpath) if f.endswith(".glb")]
        
        if glb_files:
            total_with_glb += 1
        elif has_mapping:
            # Has mapping but no GLB - check how many meshes in mapping
            try:
                with open(os.path.join(wpath, "material_mapping.json"), "r") as f:
                    m = json.load(f)
                mesh_count = len(m.get("meshes", []))
            except:
                mesh_count = -1
            missing_dirs.append((region, wad, mesh_count))

print(f"Total WAD dirs: {total_dirs}")
print(f"Dirs with GLB: {total_with_glb}")
print(f"Dirs with mapping but NO GLB: {len(missing_dirs)}")
print(f"\nMissing GLB dirs:")
for region, wad, mc in missing_dirs:
    print(f"  {region}/{wad} (meshes in mapping: {mc})")

# Also check: are there GLB files elsewhere that match these WAD names?
if missing_dirs:
    print(f"\n=== Checking if GLB files exist elsewhere ===", flush=True)
    # Build index of all GLB files by WAD name prefix
    glb_by_wad = {}
    for region in sorted(os.listdir(MODELS_DIR)):
        rpath = os.path.join(MODELS_DIR, region)
        if not os.path.isdir(rpath) or region.startswith("_"):
            continue
        for wad in sorted(os.listdir(rpath)):
            wpath = os.path.join(rpath, wad)
            if not os.path.isdir(wpath) or wad == "textures":
                continue
            glbs = [f for f in os.listdir(wpath) if f.endswith(".glb")]
            if glbs:
                glb_by_wad[wad] = (region, len(glbs))
    
    for region, wad, mc in missing_dirs:
        if wad in glb_by_wad:
            print(f"  {wad}: FOUND in {glb_by_wad[wad][0]} with {glb_by_wad[wad][1]} GLB")
        else:
            print(f"  {wad}: NOT FOUND anywhere")