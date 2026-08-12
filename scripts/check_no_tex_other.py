import os, json, collections

MODELS_DIR = r"D:\God of War Ragnarok_extracted\models"

print("=== Analyzing no-texture 'other' meshes ===", flush=True)

other_meshes = []
other_with_mat = 0
other_without_mat = 0
name_patterns = collections.Counter()

for region in sorted(os.listdir(MODELS_DIR)):
    rpath = os.path.join(MODELS_DIR, region)
    if not os.path.isdir(rpath):
        continue
    for wad in sorted(os.listdir(rpath)):
        wpath = os.path.join(rpath, wad)
        if not os.path.isdir(wpath):
            continue
        map_file = os.path.join(wpath, "material_mapping.json")
        if not os.path.isfile(map_file):
            continue
        try:
            with open(map_file, 'r') as f:
                mapping = json.load(f)
        except:
            continue
        
        for mesh_entry in mapping.get("meshes", []):
            tex_list = mesh_entry.get("textures", [])
            has_found_tex = any(t.get("found", False) for t in tex_list)
            if not has_found_tex:
                mesh_name = mesh_entry.get("mesh", "").lower()
                if "shadow" in mesh_name or "lod" in mesh_name or "proxy" in mesh_name or "collision" in mesh_name:
                    continue
                # This is "other"
                mat_details = mesh_entry.get("mat_details", [])
                if mat_details:
                    other_with_mat += 1
                else:
                    other_without_mat += 1
                
                # Extract pattern from mesh name
                parts = mesh_name.replace("mesh_", "").split("_")
                if parts:
                    name_patterns[parts[0]] += 1
                
                if len(other_meshes) < 30:
                    other_meshes.append({
                        "mesh": mesh_entry.get("mesh", ""),
                        "wad": wad,
                        "region": region,
                        "has_mat": bool(mat_details),
                        "mat_names": [m.get("name","")[:20] for m in mat_details[:3]],
                        "tex_count": len(tex_list),
                        "tex_found": sum(1 for t in tex_list if t.get("found", False))
                    })

print(f"'Other' no-texture meshes: {other_with_mat + other_without_mat}")
print(f"  With MAT reference: {other_with_mat}")
print(f"  Without MAT reference: {other_without_mat}")
print(f"\nTop name patterns:")
for p, c in name_patterns.most_common(20):
    print(f"  {p}: {c}")
print(f"\nSample meshes:")
for m in other_meshes[:15]:
    print(f"  {m['region']}/{m['wad']}/{m['mesh']} | mat={m['has_mat']} tex={m['tex_found']}/{m['tex_count']}")