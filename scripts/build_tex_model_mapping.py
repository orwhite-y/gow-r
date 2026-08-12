import struct, lz4.frame, os, re, json, glob

PC_LE = r"E:\God of War Ragnarok\exec\wad\pc_le"
OUT_BASE = r"D:\God of War Ragnarok_extracted\models"

def parse_wad(wad_path):
    """Parse a WAD file and return entries list."""
    with open(wad_path, "rb") as f:
        data = lz4.frame.decompress(f.read())
    ec = struct.unpack_from("<I", data, 8)[0]
    ds = 64 + 144 * ec
    entries = []
    cur = ds
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
                         "name": name, "t109": t109, "b111": b111, "fo": fo, "data": data})
    return entries, data

def extract_dds_hash(name):
    """Extract DDS hash from TX entry name."""
    m = re.search(r'([0-9A-Fa-f]{16})$', name)
    return int(m.group(1), 16) if m else None

def extract_tex_base(name):
    """Extract texture base name from TX entry name (without TX_ prefix and hash)."""
    base = name[3:]  # remove TX_
    m = re.search(r'_([0-9A-Fa-f]{16})$', base)
    if m:
        base = base[:m.start()]
    return base

def build_wad_mapping(entries, data):
    """Build MESH -> MAT -> TX -> DDS mapping for a WAD."""
    # Build MAT name hash -> MAT def entry
    mat_by_nh = {}
    mat_defs = []
    for e in entries:
        if e["name"].startswith("MAT_") and e["t109"] == 0x0a:
            try:
                nh = int(e["name"][4:], 16)
                if e["name"] not in mat_by_nh:
                    mat_by_nh[e["name"]] = e
                mat_by_nh[nh] = e
                mat_defs.append(e)
            except: pass
    
    # Build MAT name -> TX entry (word0=60 after MAT def)
    mat_to_tx = {}
    for me in mat_defs:
        for j in range(me["idx"]+1, min(me["idx"]+5, len(entries))):
            ne = entries[j]
            if ne["name"].startswith("MAT_") and ne["t109"] == 0x0a:
                break
            if ne["name"].startswith("TX_") and ne["word0"] == 60:
                dds = extract_dds_hash(ne["name"])
                tex_base = extract_tex_base(ne["name"])
                mat_to_tx[me["name"]] = {
                    "tx_name": ne["name"],
                    "dds_hash": dds,
                    "tex_base": tex_base,
                    "tx_idx": ne["idx"]
                }
                break
    
    # Build TX base name -> all DDS hashes (from word0=29 data entries)
    tex_base_to_dds = {}
    for e in entries:
        if e["name"].startswith("TX_") and e["word0"] == 29:
            dds = extract_dds_hash(e["name"])
            base = extract_tex_base(e["name"])
            if base not in tex_base_to_dds:
                tex_base_to_dds[base] = []
            if dds and dds not in [x[0] for x in tex_base_to_dds[base]]:
                # Determine texture type from suffix
                tex_type = "unknown"
                lower_base = base.lower()
                if lower_base.endswith("_normal") or lower_base.endswith("_n"):
                    tex_type = "normal"
                elif lower_base.endswith("_gloss") or lower_base.endswith("_g"):
                    tex_type = "gloss"
                elif lower_base.endswith("_diffuse") or lower_base.endswith("_d") or lower_base.endswith("_0d"):
                    tex_type = "diffuse"
                elif lower_base.endswith("_alpha") or lower_base.endswith("_a"):
                    tex_type = "alpha"
                elif lower_base.endswith("_m1") or lower_base.endswith("_m2"):
                    tex_type = "mask"
                elif lower_base.endswith("_thick"):
                    tex_type = "thickness"
                tex_base_to_dds[base].append((dds, tex_type, e["name"]))
    
    # Build MESH -> MAT references
    mesh_entries = [e for e in entries if e["name"].startswith("MESH_") and e["t109"] == 0x0c]
    
    mesh_mappings = []
    for me in mesh_entries:
        mat_refs = set()
        
        # Method 1: Embedded MAT name hashes in mesh data
        edata = data[me["fo"]:me["fo"]+me["size"]]
        for off in range(0, len(edata)-7, 4):
            v = struct.unpack_from("<Q", edata, off)[0]
            if v in mat_by_nh:
                mat_refs.add(mat_by_nh[v]["name"])
        
        # Method 2: Adjacent MAT reference (t109=00)
        for j in range(me["idx"]+1, min(me["idx"]+5, len(entries))):
            ne = entries[j]
            if ne["name"].startswith("MAT_") and ne["t109"] == 0x00:
                mat_refs.add(ne["name"])
                break
            if ne["name"].startswith("MESH_") and ne["t109"] == 0x0c:
                break
        
        # For each MAT ref, get TX -> DDS hashes
        all_dds = []
        for mat_name in mat_refs:
            tx_info = mat_to_tx.get(mat_name)
            if tx_info:
                # Primary texture
                if tx_info["dds_hash"]:
                    all_dds.append({
                        "dds_hash": f"{tx_info['dds_hash']:016X}",
                        "tex_type": "primary",
                        "source": f"{mat_name} -> {tx_info['tx_name'][:40]}"
                    })
                
                # Find related textures by base name
                tex_base = tx_info["tex_base"]
                # Try exact base match
                if tex_base in tex_base_to_dds:
                    for dds, ttype, tname in tex_base_to_dds[tex_base]:
                        dds_str = f"{dds:016X}"
                        if dds_str not in [x["dds_hash"] for x in all_dds]:
                            all_dds.append({
                                "dds_hash": dds_str,
                                "tex_type": ttype,
                                "source": f"name_match:{tex_base}"
                            })
                
                # Try partial base match (strip suffix)
                # e.g., "alf_basket_open01_gen_0d" -> try "alf_basket_open01_gen"
                parts = tex_base.rsplit('_', 1)
                if len(parts) == 2:
                    partial = parts[0]
                    for b, dds_list in tex_base_to_dds.items():
                        if b.startswith(partial) and b != tex_base:
                            for dds, ttype, tname in dds_list:
                                dds_str = f"{dds:016X}"
                                if dds_str not in [x["dds_hash"] for x in all_dds]:
                                    all_dds.append({
                                        "dds_hash": dds_str,
                                        "tex_type": ttype,
                                        "source": f"partial:{partial}->{b}"
                                    })
        
        mesh_mappings.append({
            "mesh_name": me["name"],
            "mesh_idx": me["idx"],
            "mat_refs": list(mat_refs),
            "textures": all_dds
        })
    
    return mesh_mappings

# === Test on one WAD ===
wad_name = "alf_bluff100_entrance.wad"
wad_path = os.path.join(PC_LE, wad_name)
print(f"Processing: {wad_name}")
entries, data = parse_wad(wad_path)
mappings = build_wad_mapping(entries, data)

# Show results
mesh_with_tex = sum(1 for m in mappings if len(m["textures"]) > 0)
mesh_without_tex = sum(1 for m in mappings if len(m["textures"]) == 0)
total_tex = sum(len(m["textures"]) for m in mappings)

print(f"MESH entries: {len(mappings)}")
print(f"  with textures: {mesh_with_tex}")
print(f"  without textures: {mesh_without_tex}")
print(f"  total texture refs: {total_tex}")

print("\n=== Sample mappings (first 10 with textures) ===")
shown = 0
for m in mappings:
    if m["textures"] and shown < 10:
        print(f"\n  MESH: {m['mesh_name']} (idx={m['mesh_idx']})")
        print(f"    MATs: {m['mat_refs']}")
        for t in m["textures"]:
            print(f"    -> {t['dds_hash']} [{t['tex_type']}] ({t['source'][:50]})")
        shown += 1

# Save mapping
out_path = os.path.join(r"E:\gow_re_workspace\output", f"{wad_name}.mapping.json")
os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, "w") as f:
    json.dump({"wad": wad_name, "mappings": mappings}, f, indent=2)
print(f"\nMapping saved to: {out_path}")