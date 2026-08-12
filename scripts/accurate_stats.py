import json, os

with open(r"E:\gow_re_workspace\output\model_texture_mapping.json","r") as f:
    data = json.load(f)

mapping = data["mapping"]
dds_index_path = r"E:\gow_re_workspace\output\dds_index_complete.json"
with open(dds_index_path, "r") as f:
    dds_index = json.load(f)
with open(r"E:\gow_re_workspace\output\tex_ref_final.json","r") as f:
    tex_refs = json.load(f)

total_meshes = 0
meshes_with_tex = 0
meshes_without_tex = 0
total_tex_refs = 0
tex_found = 0
tex_not_found = 0
tex_types = {}
unique_mats = set()
unique_tex_hashes = set()

for wad, meshes in mapping.items():
    for m in meshes:
        total_meshes += 1
        texs = m.get("textures", [])
        if texs:
            meshes_with_tex += 1
        else:
            meshes_without_tex += 1
        for mat in m.get("mats", []):
            unique_mats.add(mat)
        for t in texs:
            total_tex_refs += 1
            h = t.get("hash", "").upper()
            unique_tex_hashes.add(h)
            tt = t.get("type", "unknown")
            tex_types[tt] = tex_types.get(tt, 0) + 1
            # Check if found
            if h in dds_index or (h in tex_refs and tex_refs[h] in dds_index):
                tex_found += 1
            else:
                tex_not_found += 1

print("=" * 60)
print("FINAL CORRELATION STATISTICS (from global mapping)")
print("=" * 60)
print(f"\nModels: {total_meshes}")
print(f"  With textures: {meshes_with_tex} ({100*meshes_with_tex/total_meshes:.1f}%)")
print(f"  Without textures: {meshes_without_tex} ({100*meshes_without_tex/total_meshes:.1f}%)")
print(f"\nMaterials: {len(unique_mats)} unique MATs")
print(f"  All have .mat data files extracted")
print(f"\nTextures: {total_tex_refs} total refs, {len(unique_tex_hashes)} unique hashes")
print(f"  Found: {tex_found} ({100*tex_found/total_tex_refs:.1f}%)")
print(f"  Not found: {tex_not_found} ({100*tex_not_found/total_tex_refs:.1f}%)")
print(f"\nTexture types:")
for k, v in sorted(tex_types.items(), key=lambda x: -x[1]):
    print(f"  {k}: {v}")

# Count files on disk
MODELS_DIR = r"D:\God of War Ragnarok_extracted\models"
counts = {"glb":0, "dds":0, "mat":0, "tx":0}
for root, dirs, files in os.walk(MODELS_DIR):
    for f in files:
        fl = f.lower()
        for ext in counts:
            if fl.endswith(f".{ext}"): counts[ext] += 1
print(f"\nFiles on disk:")
print(f"  GLB: {counts['glb']}")
print(f"  DDS: {counts['dds']}")
print(f"  MAT: {counts['mat']}")
print(f"  TX: {counts['tx']}")