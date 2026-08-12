import json, os, re, struct, lz4.frame
from collections import defaultdict

PC_LE = r"E:\God of War Ragnarok\exec\wad\pc_le"
MODELS_DIR = r"D:\God of War Ragnarok_extracted\models"

with open(r"E:\gow_re_workspace\output\model_texture_mapping.json","r") as f:
    data = json.load(f)
with open(r"E:\gow_re_workspace\output\dds_index_complete.json","r") as f:
    dds_index = json.load(f)
with open(r"E:\gow_re_workspace\output\tex_ref_final.json","r") as f:
    tex_refs = json.load(f)
with open(r"E:\gow_re_workspace\output\global_mat_index.json","r") as f:
    mat_index = json.load(f)

mapping = data["mapping"]

def classify_tex_type(base):
    lb = base.lower()
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
    h = hash_hex.upper()
    if h in dds_index:
        return dds_index[h][0], h
    if h in tex_refs:
        ref = tex_refs[h]
        if ref in dds_index:
            return dds_index[ref][0], ref
    return None, h

# Build per-WAD texture lookup from meshes that DO have textures
# This helps link LOD meshes to their parent's textures
wad_tex_cache = {}  # wad -> {tex_base -> [texture entries]}

# First pass: collect texture info from meshes with textures
for wad, meshes in mapping.items():
    cache = defaultdict(list)
    for m in meshes:
        for t in m.get("textures", []):
            # Get tex base from the texture's mat TX info
            mat = t.get("mat", "")
            mi = mat_index.get(mat, {})
            ti = mi.get("tx_info")
            if ti:
                tb = ti.get("tex_base", "")
                if tb:
                    cache[tb].append(t)
    wad_tex_cache[wad] = cache

# Second pass: try to add textures to meshes without them
added_count = 0
lod_linked = 0
mat_tx_linked = 0

for wad, meshes in mapping.items():
    # Build mesh name -> textures map for this WAD
    mesh_tex_map = {}
    for m in meshes:
        if m.get("textures"):
            # Extract base mesh name (without _lod suffix etc)
            base_name = m["mesh"]
            mesh_tex_map[base_name] = m["textures"]
    
    for m in meshes:
        if m.get("textures"):
            continue  # Already has textures
        
        mesh_name = m.get("mesh", "")
        mats = m.get("mats", [])
        
        # Strategy 1: Check if MAT has TX info with DDS hash
        new_textures = []
        for mat_name in mats:
            mi = mat_index.get(mat_name, {})
            ti = mi.get("tx_info")
            if ti and ti.get("dds_hash"):
                dds_str = ti["dds_hash"].upper()
                dds_path, actual_hash = get_dds_path(dds_str)
                if dds_path:
                    new_textures.append({
                        "hash": dds_str,
                        "type": "primary",
                        "mat": mat_name,
                        "found": True,
                        "dds_hash": actual_hash
                    })
                    
                    # Also try to find related textures by base name
                    tb = ti.get("tex_base", "")
                    if tb:
                        cache = wad_tex_cache.get(wad, {})
                        if tb in cache:
                            for ct in cache[tb]:
                                if ct["hash"] != dds_str:
                                    new_textures.append({
                                        "hash": ct["hash"],
                                        "type": ct.get("type", "unknown"),
                                        "mat": mat_name,
                                        "found": True,
                                        "dds_hash": ct.get("dds_hash", ct["hash"])
                                    })
        
        if new_textures:
            m["textures"] = new_textures
            added_count += 1
            mat_tx_linked += 1
            continue
        
        # Strategy 2: LOD linking - find parent mesh by stripping _lod suffix
        mesh_lower = mesh_name.lower()
        if "_lod" in mesh_lower:
            # Try to find parent mesh
            parent_name = re.sub(r'_lod\d*$', '', mesh_name, flags=re.IGNORECASE)
            parent_name = re.sub(r'_lod\d*_', '_', parent_name, flags=re.IGNORECASE)
            if parent_name in mesh_tex_map:
                m["textures"] = mesh_tex_map[parent_name][:]
                added_count += 1
                lod_linked += 1
                continue
            
            # Try progressively shorter names
            parts = mesh_name.split("_")
            for i in range(len(parts)-1, 0, -1):
                candidate = "_".join(parts[:i])
                if candidate in mesh_tex_map:
                    m["textures"] = mesh_tex_map[candidate][:]
                    added_count += 1
                    lod_linked += 1
                    break

print(f"Meshes with textures added: {added_count}")
print(f"  Via MAT TX info: {mat_tx_linked}")
print(f"  Via LOD parent linking: {lod_linked}")

# Count new totals
total_with_tex = sum(1 for wad, meshes in mapping.items() for m in meshes if m.get("textures"))
total_without = sum(1 for wad, meshes in mapping.items() for m in meshes if not m.get("textures"))
print(f"\nUpdated totals:")
print(f"  With textures: {total_with_tex} ({100*total_with_tex/127554:.1f}%)")
print(f"  Without textures: {total_without} ({100*total_without/127554:.1f}%)")

# Save updated global mapping
data["stats"]["meshes_with_tex"] = total_with_tex
data["stats"]["meshes_without_tex"] = total_without
with open(r"E:\gow_re_workspace\output\model_texture_mapping.json", "w") as f:
    json.dump(data, f)
print("Global mapping updated.")