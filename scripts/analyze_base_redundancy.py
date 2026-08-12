import os, json

MODELS_DIR = r"D:\God of War Ragnarok_extracted\models"

# 1. Check which base dirs HAVE GLB (legit base content)
base_dir = os.path.join(MODELS_DIR, "base")
base_with_glb = []
base_without_glb = []

for wad in sorted(os.listdir(base_dir)):
    wpath = os.path.join(base_dir, wad)
    if not os.path.isdir(wpath) or wad == "textures":
        continue
    glbs = [f for f in os.listdir(wpath) if f.endswith(".glb")]
    if glbs:
        base_with_glb.append((wad, len(glbs)))
    else:
        base_without_glb.append(wad)

print(f"Base dirs WITH GLB: {len(base_with_glb)} ({sum(c for _,c in base_with_glb)} GLB files)")
print(f"Base dirs WITHOUT GLB: {len(base_without_glb)}")

# 2. For base dirs without GLB, check if GLB exists in other regions
# and whether that other region dir has materials
print(f"\n=== Checking if other regions have both GLB and materials ===", flush=True)

# Build index: wad_name -> [(region, has_glb, has_mat, glb_count, mat_count)]
wad_index = {}
for region in sorted(os.listdir(MODELS_DIR)):
    if region.startswith("_"):
        continue
    rpath = os.path.join(MODELS_DIR, region)
    if not os.path.isdir(rpath):
        continue
    for wad in sorted(os.listdir(rpath)):
        wpath = os.path.join(rpath, wad)
        if not os.path.isdir(wpath) or wad == "textures":
            continue
        glbs = [f for f in os.listdir(wpath) if f.endswith(".glb")]
        mat_dir = os.path.join(wpath, "materials")
        mat_count = len(os.listdir(mat_dir)) if os.path.isdir(mat_dir) else 0
        if wad not in wad_index:
            wad_index[wad] = []
        wad_index[wad].append({
            "region": region,
            "has_glb": len(glbs) > 0,
            "glb_count": len(glbs),
            "has_mat": mat_count > 0,
            "mat_count": mat_count
        })

# Check base dirs without GLB
redundant = []  # base dir is redundant (other region has GLB + mat)
needs_merge = []  # other region has GLB but no mat -> need to merge mat from base
not_found = []  # GLB not found anywhere

for wad in base_without_glb:
    if wad not in wad_index:
        not_found.append(wad)
        continue
    
    found_glb_elsewhere = False
    found_mat_elsewhere = False
    for entry in wad_index[wad]:
        if entry["region"] == "base":
            continue
        if entry["has_glb"]:
            found_glb_elsewhere = True
            if entry["has_mat"]:
                found_mat_elsewhere = True
    
    if found_glb_elsewhere and found_mat_elsewhere:
        redundant.append(wad)
    elif found_glb_elsewhere and not found_mat_elsewhere:
        needs_merge.append(wad)
    else:
        not_found.append(wad)

print(f"Redundant (GLB+MAT exist elsewhere): {len(redundant)}")
print(f"Needs merge (GLB elsewhere, MAT only in base): {len(needs_merge)}")
print(f"GLB not found anywhere: {len(not_found)}")

if needs_merge:
    print(f"\nDirs needing merge (GLB elsewhere, MAT in base):")
    for wad in needs_merge[:20]:
        locations = [f"{e['region']}({e['glb_count']}glb,{e['mat_count']}mat)" for e in wad_index[wad] if e["region"] != "base"]
        print(f"  {wad}: GLB in {locations}")

if not_found:
    print(f"\nDirs with GLB not found anywhere ({len(not_found)}):")
    for wad in not_found[:20]:
        # Check mesh count in mapping
        map_file = os.path.join(base_dir, wad, "material_mapping.json")
        mc = 0
        try:
            with open(map_file) as f:
                mc = len(json.load(f).get("meshes", []))
        except:
            pass
        print(f"  {wad} (meshes in mapping: {mc})")

# Also show legit base dirs
print(f"\nLegit base dirs (have GLB): {len(base_with_glb)}")
for wad, count in base_with_glb[:10]:
    print(f"  {wad}: {count} GLB")