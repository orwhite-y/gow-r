import struct, lz4.frame, os, re, json, time
from collections import defaultdict

PC_LE = r"E:\God of War Ragnarok\exec\wad\pc_le"
MODELS_DIR = r"D:\God of War Ragnarok_extracted\models"
OUT_DIR = r"E:\gow_re_workspace\output"

with open(r"E:\gow_re_workspace\output\model_texture_mapping.json","r") as f:
    mapping_data = json.load(f)
with open(r"E:\gow_re_workspace\output\dds_index_complete.json","r") as f:
    dds_index = json.load(f)
with open(r"E:\gow_re_workspace\output\tex_ref_final.json","r") as f:
    tex_refs = json.load(f)

mapping = mapping_data["mapping"]

def wad_to_region(wad_name):
    w = wad_name.lower()
    if w.startswith("alf"): return "alfheim"
    if w.startswith("asg"): return "asgard"
    if w.startswith("hel") or w.startswith("nif_hel"): return "helheim"
    if w.startswith("jot"): return "jotunheim"
    if w.startswith("mid"): return "midgard"
    if w.startswith("mus"): return "muspelheim"
    if w.startswith("nif"): return "niflheim"
    if w.startswith("sva"): return "svartalfheim"
    if w.startswith("van"): return "vanaheim"
    if w.startswith("r_") or w.startswith("ui"): return "base"
    if "cutscene" in w or "cs_" in w: return "cutscenes"
    if "atreus" in w or "companion" in w or "kratos" in w: return "characters"
    return "base"

def get_dds_path(hash_hex):
    h = hash_hex.upper()
    if h in dds_index:
        return dds_index[h][0], h
    if h in tex_refs:
        ref = tex_refs[h]
        if ref in dds_index:
            return dds_index[ref][0], ref
    return None, h

# Update all per-WAD mapping files
print("Syncing per-WAD material_mapping.json files...")
t0 = time.time()
updated = 0
linked = 0
already = 0

for wad_name, meshes in mapping.items():
    if not meshes: continue
    
    region = wad_to_region(wad_name)
    wad_dir = os.path.join(MODELS_DIR, region, wad_name)
    tex_dir = os.path.join(wad_dir, "textures")
    
    # Load mat_index.json
    mat_index_path = os.path.join(wad_dir, "mat_index.json")
    mat_index = {}
    if os.path.exists(mat_index_path):
        with open(mat_index_path, "r") as f:
            mat_index = json.load(f)
    
    # Update mesh entries
    for m in meshes:
        # Add MAT details
        mats = m.get("mats", [])
        mat_details = []
        for mat_name in mats:
            mi = mat_index.get(mat_name, {})
            mat_details.append({
                "name": mat_name,
                "mat_file": mi.get("mat_file", f"materials/{mat_name}.mat"),
                "tx_info": mi.get("tx_info"),
                "params": mi.get("params", {})
            })
        m["mat_details"] = mat_details
        
        # Update texture entries
        for t in m.get("textures", []):
            hash_hex = t.get("hash", "").upper()
            dds_path, actual_hash = get_dds_path(hash_hex)
            t["found"] = dds_path is not None
            t["dds_hash"] = actual_hash
            
            if dds_path:
                target = os.path.join(tex_dir, f"{hash_hex}.dds")
                if not os.path.exists(target):
                    try:
                        os.makedirs(tex_dir, exist_ok=True)
                        os.link(dds_path, target)
                        linked += 1
                    except:
                        try:
                            import shutil
                            shutil.copy2(dds_path, target)
                            linked += 1
                        except:
                            pass
                else:
                    already += 1
    
    # Save updated mapping
    map_path = os.path.join(wad_dir, "material_mapping.json")
    out_data = {
        "wad": wad_name,
        "region": region,
        "meshes": meshes
    }
    with open(map_path, "w") as f:
        json.dump(out_data, f, indent=2)
    
    updated += 1

elapsed = time.time() - t0
print(f"Done! {updated} files updated in {elapsed:.1f}s")
print(f"Newly linked: {linked}")
print(f"Already linked: {already}")

# Final count
total_with = sum(1 for wad, meshes in mapping.items() for m in meshes if m.get("textures"))
total_without = sum(1 for wad, meshes in mapping.items() for m in meshes if not m.get("textures"))
print(f"\nFinal: {total_with} with tex ({100*total_with/127554:.1f}%), {total_without} without ({100*total_without/127554:.1f}%)")