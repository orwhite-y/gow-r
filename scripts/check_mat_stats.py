import json

# Load global mapping
with open(r"E:\gow_re_workspace\output\model_texture_mapping.json","r") as f:
    data = json.load(f)

stats = data["stats"]
mapping = data["mapping"]

# Count unique MATs
all_mats = set()
meshes_with_mats = 0
meshes_without_mats = 0
for wad, meshes in mapping.items():
    for m in meshes:
        mats = m.get("mats", [])
        if mats:
            meshes_with_mats += 1
            for mat in mats:
                all_mats.add(mat)
        else:
            meshes_without_mats += 1

print(f"Total meshes: {stats['total_meshes']}")
print(f"Meshes with MAT refs: {meshes_with_mats} ({100*meshes_with_mats/stats['total_meshes']:.1f}%)")
print(f"Meshes without MAT refs: {meshes_without_mats} ({100*meshes_without_mats/stats['total_meshes']:.1f}%)")
print(f"Unique MAT names: {len(all_mats)}")
print(f"Total texture refs: {stats['total_tex_refs']}")

# Check texture types distribution
tex_types = {}
for wad, meshes in mapping.items():
    for m in meshes:
        for t in m.get("textures", []):
            tt = t.get("type", "unknown")
            tex_types[tt] = tex_types.get(tt, 0) + 1
print(f"\nTexture type distribution:")
for k, v in sorted(tex_types.items(), key=lambda x: -x[1]):
    print(f"  {k}: {v}")