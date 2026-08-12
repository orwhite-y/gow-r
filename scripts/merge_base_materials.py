import os, json, shutil

MODELS_DIR = r"D:\God of War Ragnarok_extracted\models"
base_dir = os.path.join(MODELS_DIR, "base")

# Build index: wad_name -> list of {region, has_glb, glb_count, has_mat, mat_count}
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
        has_mapping = os.path.isfile(os.path.join(wpath, "material_mapping.json"))
        if wad not in wad_index:
            wad_index[wad] = []
        wad_index[wad].append({
            "region": region, "path": wpath,
            "has_glb": len(glbs) > 0, "glb_count": len(glbs),
            "has_mat": mat_count > 0, "mat_count": mat_count,
            "has_mapping": has_mapping
        })

# Process base dirs without GLB
merged = 0
deleted_empty = 0
errors = 0

for wad in sorted(os.listdir(base_dir)):
    wpath = os.path.join(base_dir, wad)
    if not os.path.isdir(wpath) or wad == "textures":
        continue
    
    glbs = [f for f in os.listdir(wpath) if f.endswith(".glb")]
    if glbs:
        continue  # Has GLB, skip (legit base dir)
    
    # Check mesh count in mapping
    map_file = os.path.join(wpath, "material_mapping.json")
    mesh_count = 0
    if os.path.isfile(map_file):
        try:
            with open(map_file) as f:
                mesh_count = len(json.load(f).get("meshes", []))
        except:
            pass
    
    if mesh_count == 0:
        # Empty WAD (no meshes) - just delete
        try:
            shutil.rmtree(wpath)
            deleted_empty += 1
        except Exception as e:
            errors += 1
            if errors <= 3:
                print(f"  ERROR deleting {wad}: {e}")
        continue
    
    # Find where GLB files are
    target = None
    if wad in wad_index:
        for entry in wad_index[wad]:
            if entry["region"] != "base" and entry["has_glb"]:
                target = entry
                break
    
    if not target:
        print(f"  NO TARGET for {wad} (meshes={mesh_count}, GLB not found anywhere)")
        continue
    
    # Merge materials from base to target
    target_path = target["path"]
    
    # Copy materials/
    src_mat = os.path.join(wpath, "materials")
    dst_mat = os.path.join(target_path, "materials")
    if os.path.isdir(src_mat):
        os.makedirs(dst_mat, exist_ok=True)
        for f in os.listdir(src_mat):
            src_f = os.path.join(src_mat, f)
            dst_f = os.path.join(dst_mat, f)
            if not os.path.exists(dst_f):
                try:
                    shutil.copy2(src_f, dst_f)
                except:
                    pass
    
    # Copy mat_index.json
    src_mi = os.path.join(wpath, "mat_index.json")
    dst_mi = os.path.join(target_path, "mat_index.json")
    if os.path.isfile(src_mi) and not os.path.isfile(dst_mi):
        shutil.copy2(src_mi, dst_mi)
    
    # Copy/merge material_mapping.json
    src_map = os.path.join(wpath, "material_mapping.json")
    dst_map = os.path.join(target_path, "material_mapping.json")
    if os.path.isfile(src_map):
        if not os.path.isfile(dst_map):
            # Just copy and update region
            with open(src_map) as f:
                m = json.load(f)
            m["region"] = target["region"]
            with open(dst_map, "w") as f:
                json.dump(m, f, indent=2, ensure_ascii=False)
        else:
            # Target already has mapping - check if base has more data
            try:
                with open(src_map) as f:
                    src_m = json.load(f)
                with open(dst_map) as f:
                    dst_m = json.load(f)
                # If source has more meshes, use it
                if len(src_m.get("meshes", [])) > len(dst_m.get("meshes", [])):
                    src_m["region"] = target["region"]
                    with open(dst_map, "w") as f:
                        json.dump(src_m, f, indent=2, ensure_ascii=False)
            except:
                pass
    
    # Copy textures/ (DDS files that target doesn't have)
    src_tex = os.path.join(wpath, "textures")
    dst_tex = os.path.join(target_path, "textures")
    if os.path.isdir(src_tex):
        os.makedirs(dst_tex, exist_ok=True)
        for f in os.listdir(src_tex):
            dst_f = os.path.join(dst_tex, f)
            if not os.path.exists(dst_f):
                try:
                    shutil.copy2(os.path.join(src_tex, f), dst_f)
                except:
                    pass
    
    # Delete the base dir
    try:
        shutil.rmtree(wpath)
        merged += 1
    except Exception as e:
        errors += 1
        if errors <= 3:
            print(f"  ERROR deleting {wad}: {e}")
    
    if merged % 50 == 0:
        print(f"  Merged {merged}...", flush=True)

print(f"\nDone!")
print(f"  Merged (MAT copied + base dir deleted): {merged}")
print(f"  Empty dirs deleted: {deleted_empty}")
print(f"  Errors: {errors}")

# Verify: count base dirs remaining
remaining = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d)) and d != "textures"]
print(f"  Base dirs remaining: {len(remaining)} (should be ~29 legit + any errors)")