import struct, lz4.frame, os, re, json, time, sys
from collections import defaultdict

PC_LE = r"E:\God of War Ragnarok\exec\wad\pc_le"
MODELS_DIR = r"D:\God of War Ragnarok_extracted\models"
OUT_DIR = r"E:\gow_re_workspace\output"

# Region mapping (from MEMORY.md)
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

def parse_wad(wad_path):
    with open(wad_path, "rb") as f:
        data = lz4.frame.decompress(f.read())
    ec = struct.unpack_from("<I", data, 8)[0]
    ds = 64 + 144 * ec
    cur = ds
    entries = []
    for i in range(ec):
        o = 64 + 144 * i
        word0 = struct.unpack_from("<H", data, o)[0]
        size = struct.unpack_from("<I", data, o+4)[0]
        hash_val = struct.unpack_from("<Q", data, o+8)[0]
        name = data[o+24:o+104].split(b"\x00")[0].decode("ascii", errors="replace")
        t109 = data[o+109]
        b111 = data[o+111]
        align = struct.unpack_from("<I", data, o+104)[0]
        fo = cur
        if align > 0: fo = (fo + align - 1) & ~(align - 1)
        cur = fo + size
        entries.append({"idx": i, "word0": word0, "size": size, "hash": hash_val,
                         "name": name, "t109": t109, "b111": b111, "fo": fo, "align": align})
    return entries, data

def extract_dds_hash(name):
    m = re.search(r'([0-9A-Fa-f]{16})$', name)
    return m.group(1).upper() if m else None

def extract_tex_base(name):
    base = name[3:] if name.startswith("TX_") else name
    m = re.search(r'_([0-9A-Fa-f]{16})$', base)
    if m: base = base[:m.start()]
    return base

def classify_tex_type(name, base):
    lb = base.lower()
    ln = name.lower()
    # More comprehensive patterns
    if any(x in lb for x in ["_normal", "_0n", "_nmap", "_nm"]): return "normal"
    if any(x in lb for x in ["_gloss", "_0g", "_glossiness", "_roughness", "_0r", "_rms"]): return "gloss"
    if any(x in lb for x in ["_diffuse", "_0d", "_diff", "_albedo", "_color", "_col"]): return "diffuse"
    if any(x in lb for x in ["_alpha", "_0a", "_opacity"]): return "alpha"
    if any(x in lb for x in ["_m1", "_m2", "_mask", "_mtl"]): return "mask"
    if any(x in lb for x in ["_thick", "_thickness"]): return "thickness"
    if any(x in lb for x in ["_ao", "_ambient"]): return "ao"
    if any(x in lb for x in ["_height", "_0h", "_disp", "_displace"]): return "height"
    if any(x in lb for x in ["_emiss", "_0e", "_emit", "_glow"]): return "emissive"
    if any(x in lb for x in ["_spec", "_0s", "_specular"]): return "specular"
    if any(x in lb for x in ["_metal", "_0m", "_metallic"]): return "metallic"
    if any(x in lb for x in ["_cube", "_env", "_sky"]): return "environment"
    return "unknown"

def parse_mat_params(edata):
    """Extract meaningful parameters from MAT data"""
    params = {}
    if len(edata) < 16: return params
    
    # Try to find DXBC shader bytecode offset
    dxbc_off = edata.find(b"DXBC")
    if dxbc_off >= 0:
        params["shader_offset"] = dxbc_off
        params["shader_size"] = len(edata) - dxbc_off
        params["has_shader"] = True
    
    # Extract float values from the parameter header (before shader bytecode)
    end = dxbc_off if dxbc_off >= 0 else min(len(edata), 256)
    floats = []
    for off in range(0, end - 3, 4):
        f = struct.unpack_from("<f", edata, off)[0]
        # Only keep meaningful floats
        if abs(f) > 0.001 and abs(f) < 10000:
            floats.append({"offset": off, "value": round(f, 6)})
    if floats:
        params["floats"] = floats[:32]  # Limit to first 32
    
    # Look for color values (0-1 range floats in groups of 4)
    colors = []
    for off in range(0, min(end, 64), 16):
        if off + 16 <= len(edata):
            r = struct.unpack_from("<f", edata, off)[0]
            g = struct.unpack_from("<f", edata, off+4)[0]
            b = struct.unpack_from("<f", edata, off+8)[0]
            a = struct.unpack_from("<f", edata, off+12)[0]
            if all(0.0 <= v <= 1.0 for v in [r, g, b, a]) and any(v > 0 for v in [r, g, b, a]):
                colors.append({"offset": off, "rgba": [round(r, 4), round(g, 4), round(b, 4), round(a, 4)]})
    if colors:
        params["potential_colors"] = colors
    
    return params

# Process all WADs
wads = sorted([f for f in os.listdir(PC_LE) if f.endswith(".wad")])
print(f"Processing {len(wads)} WADs for MAT extraction...")

all_mat_data = {}  # mat_name -> {params, wad, size}
mat_file_count = 0
wad_count = 0
t0 = time.time()

for wad_file in wads:
    wad_name = wad_file.replace(".wad", "")
    wad_path = os.path.join(PC_LE, wad_file)
    region = wad_to_region(wad_name)
    wad_dir = os.path.join(MODELS_DIR, region, wad_name)
    
    try:
        entries, data = parse_wad(wad_path)
    except Exception as e:
        continue
    
    # Find MAT entries (t109=0x0a = material definitions)
    mat_entries = [e for e in entries if e["name"].startswith("MAT_") and e["t109"] == 0x0a]
    if not mat_entries:
        wad_count += 1
        continue
    
    # Create materials subdirectory
    mat_dir = os.path.join(wad_dir, "materials")
    os.makedirs(mat_dir, exist_ok=True)
    
    wad_mats = {}
    for me in mat_entries:
        mat_name = me["name"]
        edata = data[me["fo"]:me["fo"]+me["size"]]
        
        # Save raw MAT binary
        mat_file = os.path.join(mat_dir, f"{mat_name}.mat")
        with open(mat_file, "wb") as f:
            f.write(edata)
        mat_file_count += 1
        
        # Find associated TX entry (next entry with word0=60)
        tx_info = None
        for j in range(me["idx"]+1, min(me["idx"]+5, len(entries))):
            ne = entries[j]
            if ne["name"].startswith("MAT_") and ne["t109"] == 0x0a: break
            if ne["name"].startswith("TX_") and ne["word0"] == 60:
                tx_data = data[ne["fo"]:ne["fo"]+ne["size"]]
                # Save TX binary too
                tx_file = os.path.join(mat_dir, f"{mat_name}.tx")
                with open(tx_file, "wb") as f:
                    f.write(tx_data)
                dds_hash = extract_dds_hash(ne["name"])
                tex_base = extract_tex_base(ne["name"])
                tx_info = {
                    "tx_name": ne["name"],
                    "dds_hash": dds_hash,
                    "tex_base": tex_base,
                    "tx_size": ne["size"]
                }
                break
        
        # Parse parameters
        params = parse_mat_params(edata)
        
        mat_info = {
            "name": mat_name,
            "size": me["size"],
            "wad": wad_name,
            "region": region,
            "mat_file": f"materials/{mat_name}.mat",
            "tx_info": tx_info,
            "params": params
        }
        wad_mats[mat_name] = mat_info
        
        # Track unique MATs across all WADs
        if mat_name not in all_mat_data:
            all_mat_data[mat_name] = mat_info
    
    # Save per-WAD MAT index
    mat_index_file = os.path.join(wad_dir, "mat_index.json")
    with open(mat_index_file, "w") as f:
        json.dump(wad_mats, f, indent=2)
    
    wad_count += 1
    if wad_count % 100 == 0:
        elapsed = time.time() - t0
        print(f"  [{wad_count}/{len(wads)}] {wad_count/elapsed:.1f} WADs/s, {mat_file_count} MAT files extracted")

elapsed = time.time() - t0
print(f"\nDone! {wad_count} WADs, {mat_file_count} MAT files in {elapsed:.1f}s")
print(f"Unique MATs: {len(all_mat_data)}")

# Save global MAT index
mat_index_path = os.path.join(OUT_DIR, "global_mat_index.json")
with open(mat_index_path, "w") as f:
    json.dump(all_mat_data, f, indent=2)
print(f"Global MAT index saved: {mat_index_path}")