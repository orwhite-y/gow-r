import json, os

MODELS_DIR = r"D:\God of War Ragnarok_extracted\models"

# Pick a sample WAD with good texture coverage
sample_wad = "midgard_zoo"
sample_dir = os.path.join(MODELS_DIR, "midgard", sample_wad)

print(f"=== Sample: {sample_wad} ===")
print(f"Path: {sample_dir}")

# List contents
glb_files = [f for f in os.listdir(sample_dir) if f.endswith(".glb")]
mat_dir = os.path.join(sample_dir, "materials")
tex_dir = os.path.join(sample_dir, "textures")

print(f"GLB files: {len(glb_files)}")
if os.path.exists(mat_dir):
    mat_files = [f for f in os.listdir(mat_dir) if f.endswith(".mat")]
    tx_files = [f for f in os.listdir(mat_dir) if f.endswith(".tx")]
    print(f"MAT files: {len(mat_files)}")
    print(f"TX files: {len(tx_files)}")
if os.path.exists(tex_dir):
    dds_files = [f for f in os.listdir(tex_dir) if f.endswith(".dds")]
    print(f"DDS files: {len(dds_files)}")

# Show mapping
map_path = os.path.join(sample_dir, "material_mapping.json")
with open(map_path, "r") as f:
    mapping = json.load(f)

meshes = mapping["meshes"]
with_tex = sum(1 for m in meshes if m.get("textures"))
without_tex = sum(1 for m in meshes if not m.get("textures"))

print(f"\nMapping: {len(meshes)} meshes")
print(f"  With textures: {with_tex} ({100*with_tex/len(meshes):.1f}%)")
print(f"  Without textures: {without_tex} ({100*without_tex/len(meshes):.1f}%)")

# Show a sample mesh with full correlation
for m in meshes:
    if m.get("textures") and len(m.get("textures",[])) > 3:
        print(f"\n--- Sample mesh: {m['mesh']} ---")
        print(f"  MAT: {m.get('mats',[])}")
        for md in m.get("mat_details",[]):
            print(f"  MAT detail: {md['name']} -> {md['mat_file']}")
            ti = md.get("tx_info")
            if ti:
                print(f"    TX: {ti.get('tx_name','')} -> DDS: {ti.get('dds_hash','')}")
        print(f"  Textures:")
        for t in m["textures"]:
            found = "✓" if t.get("found") else "✗"
            print(f"    {found} {t['hash']} ({t['type']}) -> {t.get('dds_hash','')}")
        
        # Verify files exist
        glb_name = m.get("mesh", "")
        # Find the GLB file
        matching_glbs = [g for g in glb_files if glb_name in g]
        if matching_glbs:
            glb_path = os.path.join(sample_dir, matching_glbs[0])
            glb_size = os.path.getsize(glb_path)
            print(f"  GLB: {matching_glbs[0]} ({glb_size/1024:.0f} KB)")
        break

# Also check a mesh without textures
for m in meshes:
    if not m.get("textures"):
        print(f"\n--- No-tex mesh: {m['mesh']} ---")
        print(f"  MAT: {m.get('mats',[])}")
        for md in m.get("mat_details",[]):
            ti = md.get("tx_info")
            print(f"  MAT: {md['name']} | TX info: {'yes' if ti else 'no'}")
        break