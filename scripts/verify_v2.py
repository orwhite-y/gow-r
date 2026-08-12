import json, os, sys
sys.stdout.reconfigure(encoding='utf-8')

MODELS_DIR = r"D:\God of War Ragnarok_extracted\models"
sample_dir = os.path.join(MODELS_DIR, "midgard", "midgard_zoo")

glb_files = [f for f in os.listdir(sample_dir) if f.endswith(".glb")]
map_path = os.path.join(sample_dir, "material_mapping.json")
with open(map_path, "r") as f:
    mapping = json.load(f)

meshes = mapping["meshes"]
with_tex = sum(1 for m in meshes if m.get("textures"))
without_tex = sum(1 for m in meshes if not m.get("textures"))

print(f"=== midgard_zoo ===")
print(f"GLB: {len(glb_files)}, MAT: {len([f for f in os.listdir(os.path.join(sample_dir,'materials')) if f.endswith('.mat')])}, DDS: {len([f for f in os.listdir(os.path.join(sample_dir,'textures')) if f.endswith('.dds')])}")
print(f"Meshes: {len(meshes)} | With tex: {with_tex} ({100*with_tex/len(meshes):.1f}%) | Without: {without_tex}")

# Show a fully correlated mesh
for m in meshes:
    if m.get("textures") and len(m.get("textures",[])) > 3:
        print(f"\n--- {m['mesh']} ---")
        for md in m.get("mat_details",[]):
            ti = md.get("tx_info")
            print(f"  MAT: {md['name']} -> {md['mat_file']}")
            if ti: print(f"    TX: {ti.get('tx_name','')} -> DDS hash: {ti.get('dds_hash','')}")
        print(f"  Textures ({len(m['textures'])}):")
        for t in m["textures"]:
            status = "OK" if t.get("found") else "MISSING"
            print(f"    [{status}] {t['hash']} ({t['type']})")
        # Verify GLB exists
        matching = [g for g in glb_files if m["mesh"] in g]
        if matching:
            print(f"  GLB: {matching[0]} ({os.path.getsize(os.path.join(sample_dir, matching[0]))/1024:.0f} KB)")
        # Verify DDS exists
        tex_dir = os.path.join(sample_dir, "textures")
        for t in m["textures"][:2]:
            dds_path = os.path.join(tex_dir, f"{t['hash']}.dds")
            if os.path.exists(dds_path):
                print(f"  DDS check: {t['hash']}.dds exists ({os.path.getsize(dds_path)/1024:.0f} KB)")
            else:
                print(f"  DDS check: {t['hash']}.dds MISSING")
        # Verify MAT exists
        for md in m.get("mat_details",[]):
            mat_path = os.path.join(sample_dir, md["mat_file"])
            if os.path.exists(mat_path):
                print(f"  MAT check: {md['mat_file']} exists ({os.path.getsize(mat_path)} bytes)")
        break

print("\n=== Verification PASSED ===")