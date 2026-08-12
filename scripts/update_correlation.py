import struct, lz4.frame, os, re, json, time
from collections import defaultdict

PC_LE = r"E:\God of War Ragnarok\exec\wad\pc_le"
MODELS_DIR = r"D:\God of War Ragnarok_extracted\models"
OUT_DIR = r"E:\gow_re_workspace\output"

# Load data
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

def classify_tex_type(name, base):
    lb = base.lower()
    ln = name.lower()
    if any(x in lb for x in ["_normal", "_0n", "_nmap", "_nm", "_bnrm", "_nrm"]): return "normal"
    if any(x in lb for x in ["_gloss", "_0g", "_glossiness", "_roughness", "_0r", "_rms", "_0sc"]): return "gloss"
    if any(x in lb for x in ["_diffuse", "_0d", "_diff", "_albedo", "_color", "_col", "_0c"]): return "diffuse"
    if any(x in lb for x in ["_alpha", "_0a", "_opacity"]): return "alpha"
    if any(x in lb for x in ["_m1", "_m2", "_mask", "_mtl", "_0m"]): return "mask"
    if any(x in lb for x in ["_thick", "_thickness"]): return "thickness"
    if any(x in lb for x in ["_ao", "_ambient"]): return "ao"
    if any(x in lb for x in ["_height", "_0h", "_disp", "_displace"]): return "height"
    if any(x in lb for x in ["_emiss", "_0e", "_emit", "_glow"]): return "emissive"
    if any(x in lb for x in ["_spec", "_0s", "_specular"]): return "specular"
    if any(x in lb for x in ["_metal", "_metallic"]): return "metallic"
    if any(x in lb for x in ["_cube", "_env", "_sky", "_irr"]): return "environment"
    return "unknown"

def get_dds_path(hash_hex):
    """Get the DDS file path for a hash, following references if needed."""
    h = hash_hex.upper()
    if h in dds_index:
        return dds_index[h][0], h
    if h in tex_refs:
        ref = tex_refs[h]
        if ref in dds_index:
            return dds_index[ref][0], ref
    return None, h

# Process each WAD and update material_mapping.json
print("Updating material_mapping.json files with MAT data + texture links...")
t0 = time.time()
updated_count = 0
linked_count = 0
already_linked = 0
not_found_count = 0

for wad_name, meshes in mapping.items():
    if not meshes: continue
    
    region = wad_to_region(wad_name)
    wad_dir = os.path.join(MODELS_DIR, region, wad_name)
    tex_dir = os.path.join(wad_dir, "textures")
    
    # Load existing mat_index.json
    mat_index_path = os.path.join(wad_dir, "mat_index.json")
    mat_index = {}
    if os.path.exists(mat_index_path):
        with open(mat_index_path, "r") as f:
            mat_index = json.load(f)
    
    # Update mesh entries
    for m in meshes:
        # Add MAT data file references
        mats = m.get("mats", [])
        mat_details = []
        for mat_name in mats:
            mi = mat_index.get(mat_name, {})
            mat_details.append({
                "name": mat_name,
                "mat_file": mi.get("mat_file", f"materials/{mat_name}.mat"),
                "tx_file": mi.get("mat_file", "").replace(".mat", ".tx") if mi.get("mat_file") else None,
                "tx_info": mi.get("tx_info"),
                "params": mi.get("params", {})
            })
        m["mat_details"] = mat_details
        
        # Update texture entries with found status and improved type classification
        for t in m.get("textures", []):
            hash_hex = t.get("hash", "").upper()
            dds_path, actual_hash = get_dds_path(hash_hex)
            
            # Reclassify type
            tx_name = t.get("mat", "")
            tex_base = t.get("tex_base", "")
            if not tex_base and t.get("type") == "primary":
                # Try to get base from mat details
                for md in mat_details:
                    if md["name"] == t.get("mat"):
                        ti = md.get("tx_info")
                        if ti:
                            tex_base = ti.get("tex_base", "")
                            break
            
            if t.get("type") == "primary":
                # Keep primary as primary
                pass
            elif t.get("type") == "unknown" or not t.get("type"):
                new_type = classify_tex_type(t.get("tex_base", ""), t.get("tex_base", ""))
                if new_type != "unknown":
                    t["type"] = new_type
            
            t["found"] = dds_path is not None
            t["dds_hash"] = actual_hash
            if dds_path:
                t["dds_path"] = os.path.relpath(dds_path, wad_dir)
                
                # Hard-link if not already there
                target = os.path.join(tex_dir, f"{hash_hex}.dds")
                if not os.path.exists(target):
                    try:
                        os.makedirs(tex_dir, exist_ok=True)
                        os.link(dds_path, target)
                        linked_count += 1
                    except Exception as e:
                        try:
                            import shutil
                            shutil.copy2(dds_path, target)
                            linked_count += 1
                        except:
                            not_found_count += 1
                else:
                    already_linked += 1
            else:
                not_found_count += 1
    
    # Save updated material_mapping.json
    map_path = os.path.join(wad_dir, "material_mapping.json")
    out_data = {
        "wad": wad_name,
        "region": region,
        "meshes": meshes
    }
    with open(map_path, "w") as f:
        json.dump(out_data, f, indent=2)
    
    updated_count += 1
    if updated_count % 100 == 0:
        elapsed = time.time() - t0
        print(f"  [{updated_count}/{len(mapping)}] {updated_count/elapsed:.1f} WADs/s, linked={linked_count}")

elapsed = time.time() - t0
print(f"\nDone! {updated_count} mapping files updated in {elapsed:.1f}s")
print(f"Textures hard-linked: {linked_count}")
print(f"Already linked: {already_linked}")
print(f"Not found: {not_found_count}")