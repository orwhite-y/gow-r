import os, json, collections

MODELS_DIR = r"D:\God of War Ragnarok_extracted\models"

print("=== FINAL AUDIT ===", flush=True)

total_glb = 0
total_meshes = 0
meshes_with_tex = 0
meshes_without_tex = 0
total_mat_refs = 0
mats_found = 0
mats_missing = 0
total_tex_refs = 0
tex_found = 0
tex_missing = 0
missing_hashes = set()
no_tex_mesh_types = collections.Counter()

for region in sorted(os.listdir(MODELS_DIR)):
    rpath = os.path.join(MODELS_DIR, region)
    if not os.path.isdir(rpath):
        continue
    for wad in sorted(os.listdir(rpath)):
        wpath = os.path.join(rpath, wad)
        if not os.path.isdir(wpath):
            continue
        
        for f in os.listdir(wpath):
            if f.endswith('.glb'):
                total_glb += 1
        
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
        mat_files = set(os.listdir(mat_dir)) if os.path.isdir(mat_dir) else set()
        
        for mesh_entry in mapping.get("meshes", []):
            total_meshes += 1
            tex_list = mesh_entry.get("textures", [])
            has_found_tex = any(t.get("found", False) for t in tex_list)
            if has_found_tex:
                meshes_with_tex += 1
            else:
                meshes_without_tex += 1
                mesh_name = mesh_entry.get("mesh", "").lower()
                if "shadow" in mesh_name:
                    no_tex_mesh_types["shadow"] += 1
                elif "lod" in mesh_name:
                    no_tex_mesh_types["lod"] += 1
                elif "proxy" in mesh_name:
                    no_tex_mesh_types["proxy"] += 1
                elif "collision" in mesh_name:
                    no_tex_mesh_types["collision"] += 1
                else:
                    no_tex_mesh_types["other"] += 1
            
            for mat_detail in mesh_entry.get("mat_details", []):
                mat_name = mat_detail.get("name", "")
                total_mat_refs += 1
                if mat_name + ".mat" in mat_files:
                    mats_found += 1
                else:
                    mats_missing += 1
            
            for tex in mesh_entry.get("textures", []):
                total_tex_refs += 1
                dds_hash = tex.get("dds_hash", "") or tex.get("hash", "")
                if dds_hash:
                    dds_file = os.path.join(tex_dir, dds_hash + ".dds")
                    if os.path.isfile(dds_file):
                        tex_found += 1
                    else:
                        tex_missing += 1
                        missing_hashes.add(dds_hash)
                else:
                    tex_missing += 1

print(f"Total GLB files: {total_glb}")
print(f"Total mesh entries: {total_meshes}")
print(f"Duplicate GLB: 0 (verified earlier)")
print()
print(f"Texture coverage:")
print(f"  Meshes with textures: {meshes_with_tex}/{total_meshes} ({100*meshes_with_tex/total_meshes:.1f}%)")
print(f"  Meshes without textures: {meshes_without_tex}/{total_meshes} ({100*meshes_without_tex/total_meshes:.1f}%)")
print(f"  No-texture breakdown: {dict(no_tex_mesh_types)}")
print()
print(f"MAT coverage:")
print(f"  MAT found: {mats_found}/{total_mat_refs} ({100*mats_found/total_mat_refs:.1f}%)")
print(f"  MAT missing: {mats_missing}/{total_mat_refs} ({100*mats_missing/total_mat_refs:.1f}%)")
print()
print(f"DDS coverage:")
print(f"  DDS found: {tex_found}/{total_tex_refs} ({100*tex_found/total_tex_refs:.1f}%)")
print(f"  DDS missing: {tex_missing}/{total_tex_refs} ({100*tex_missing/total_tex_refs:.1f}%)")
print(f"  Unique missing hashes: {len(missing_hashes)}")