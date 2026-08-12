import json, os, time

MODELS_DIR = r"D:\God of War Ragnarok_extracted\models"

# Count final stats
total_meshes = 0
meshes_with_tex = 0
meshes_without_tex = 0
meshes_with_mat_data = 0
total_tex_refs = 0
tex_found = 0
tex_not_found = 0
tex_types = {}
total_mats = 0
mats_with_data = 0

# Walk all material_mapping.json files
for root, dirs, files in os.walk(MODELS_DIR):
    for f in files:
        if f == "material_mapping.json":
            map_path = os.path.join(root, f)
            try:
                with open(map_path, "r") as fh:
                    data = json.load(fh)
                for m in data.get("meshes", []):
                    total_meshes += 1
                    
                    # Check MAT data
                    mat_details = m.get("mat_details", [])
                    if mat_details:
                        meshes_with_mat_data += 1
                        for md in mat_details:
                            total_mats += 1
                            if md.get("mat_file"):
                                mats_with_data += 1
                    
                    # Check textures
                    texs = m.get("textures", [])
                    if texs:
                        meshes_with_tex += 1
                    else:
                        meshes_without_tex += 1
                    
                    for t in texs:
                        total_tex_refs += 1
                        tt = t.get("type", "unknown")
                        tex_types[tt] = tex_types.get(tt, 0) + 1
                        if t.get("found"):
                            tex_found += 1
                        else:
                            tex_not_found += 1
            except:
                pass

print("=" * 60)
print("FINAL CORRELATION STATISTICS")
print("=" * 60)
print(f"\nModels (meshes):")
print(f"  Total: {total_meshes}")
print(f"  With textures: {meshes_with_tex} ({100*meshes_with_tex/total_meshes:.1f}%)")
print(f"  Without textures: {meshes_without_tex} ({100*meshes_without_tex/total_meshes:.1f}%)")
print(f"  With MAT data: {meshes_with_mat_data} ({100*meshes_with_mat_data/total_meshes:.1f}%)")

print(f"\nMaterials:")
print(f"  Total MAT references: {total_mats}")
print(f"  With .mat data files: {mats_with_data} ({100*mats_with_data/total_mats:.1f}%)")

print(f"\nTextures:")
print(f"  Total texture references: {total_tex_refs}")
print(f"  Found (DDS linked): {tex_found} ({100*tex_found/total_tex_refs:.1f}%)")
print(f"  Not found: {tex_not_found} ({100*tex_not_found/total_tex_refs:.1f}%)")

print(f"\nTexture type distribution:")
for k, v in sorted(tex_types.items(), key=lambda x: -x[1]):
    print(f"  {k}: {v} ({100*v/total_tex_refs:.1f}%)")

# Count actual files on disk
glb_count = 0
dds_count = 0
mat_count = 0
tx_count = 0
for root, dirs, files in os.walk(MODELS_DIR):
    for f in files:
        fl = f.lower()
        if fl.endswith(".glb"): glb_count += 1
        elif fl.endswith(".dds"): dds_count += 1
        elif fl.endswith(".mat"): mat_count += 1
        elif fl.endswith(".tx"): tx_count += 1

print(f"\nFiles on disk:")
print(f"  GLB models: {glb_count}")
print(f"  DDS textures: {dds_count}")
print(f"  MAT material files: {mat_count}")
print(f"  TX shader files: {tx_count}")
print(f"  material_mapping.json files: {sum(1 for r,d,f in os.walk(MODELS_DIR) for fn in f if fn=='material_mapping.json')}")
print(f"  mat_index.json files: {sum(1 for r,d,f in os.walk(MODELS_DIR) for fn in f if fn=='mat_index.json')}")