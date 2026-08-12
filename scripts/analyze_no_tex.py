import json

with open(r"E:\gow_re_workspace\output\model_texture_mapping.json","r") as f:
    data = json.load(f)

mapping = data["mapping"]

# Analyze meshes without textures
no_tex_meshes = []
for wad, meshes in mapping.items():
    for m in meshes:
        if not m.get("textures"):
            no_tex_meshes.append({"wad": wad, "mesh": m.get("mesh",""), "mats": m.get("mats",[])})

print(f"Meshes without textures: {len(no_tex_meshes)}")

# Check MAT distribution
mats_of_no_tex = {}
for nm in no_tex_meshes:
    for mat in nm["mats"]:
        mats_of_no_tex[mat] = mats_of_no_tex.get(mat, 0) + 1

print(f"Unique MATs used by no-tex meshes: {len(mats_of_no_tex)}")

# Load global mat index to check if these MATs have TX info
with open(r"E:\gow_re_workspace\output\global_mat_index.json","r") as f:
    mat_index = json.load(f)

mat_with_tx = 0
mat_without_tx = 0
mat_not_in_index = 0
for mat_name in mats_of_no_tex:
    if mat_name in mat_index:
        mi = mat_index[mat_name]
        if mi.get("tx_info"):
            mat_with_tx += 1
        else:
            mat_without_tx += 1
    else:
        mat_not_in_index += 1

print(f"  MATs with TX info: {mat_with_tx}")
print(f"  MATs without TX info: {mat_without_tx}")
print(f"  MATs not in index: {mat_not_in_index}")

# Sample meshes without textures
print(f"\nSample no-tex meshes:")
for nm in no_tex_meshes[:10]:
    mat_info = []
    for mat in nm["mats"]:
        mi = mat_index.get(mat, {})
        tx = mi.get("tx_info")
        if tx:
            mat_info.append(f"{mat}(TX:{tx.get('dds_hash','?')})")
        else:
            mat_info.append(f"{mat}(no TX)")
    print(f"  {nm['wad']}/{nm['mesh']} -> {', '.join(mat_info)}")

# Check what types of meshes these are (by name pattern)
name_patterns = {}
for nm in no_tex_meshes:
    mesh_name = nm["mesh"].lower()
    if "collision" in mesh_name or "col_" in mesh_name: pat = "collision"
    elif "shadow" in mesh_name or "shd" in mesh_name: pat = "shadow"
    elif "lod" in mesh_name: pat = "lod"
    elif "proxy" in mesh_name: pat = "proxy"
    elif "simple" in mesh_name or "simp" in mesh_name: pat = "simple"
    elif "occluder" in mesh_name: pat = "occluder"
    elif "trigger" in mesh_name: pat = "trigger"
    elif "water" in mesh_name: pat = "water"
    elif "physics" in mesh_name or "phys" in mesh_name: pat = "physics"
    elif "decal" in mesh_name: pat = "decal"
    elif "light" in mesh_name: pat = "light"
    else: pat = "other"
    name_patterns[pat] = name_patterns.get(pat, 0) + 1

print(f"\nNo-tex mesh name patterns:")
for k, v in sorted(name_patterns.items(), key=lambda x: -x[1]):
    print(f"  {k}: {v} ({100*v/len(no_tex_meshes):.1f}%)")