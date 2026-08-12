import struct, lz4.frame, os, re, json, time, sys

PC_LE = r"E:\God of War Ragnarok\exec\wad\pc_le"
OUT_DIR = r"E:\gow_re_workspace\output"
os.makedirs(OUT_DIR, exist_ok=True)

def parse_wad(wad_path):
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
                         "name": name, "t109": t109, "b111": b111, "fo": fo})
    return entries, data

def extract_dds_hash(name):
    m = re.search(r'([0-9A-Fa-f]{16})$', name)
    return int(m.group(1), 16) if m else None

def extract_tex_base(name):
    base = name[3:]
    m = re.search(r'_([0-9A-Fa-f]{16})$', base)
    if m: base = base[:m.start()]
    return base

def classify_tex_type(base):
    lb = base.lower()
    if lb.endswith("_normal") or lb.endswith("_0n") or lb.endswith("_n"): return "normal"
    if lb.endswith("_gloss") or lb.endswith("_0g") or lb.endswith("_g"): return "gloss"
    if lb.endswith("_diffuse") or lb.endswith("_0d") or lb.endswith("_d"): return "diffuse"
    if lb.endswith("_alpha") or lb.endswith("_0a") or lb.endswith("_a"): return "alpha"
    if lb.endswith("_m1") or lb.endswith("_m2"): return "mask"
    if lb.endswith("_thick"): return "thickness"
    if lb.endswith("_ao"): return "ao"
    if lb.endswith("_h") or lb.endswith("_height"): return "height"
    return "unknown"

def process_wad(wad_name, entries, data):
    # Build MAT name hash -> MAT name
    mat_by_nh = {}
    mat_defs = []
    mat_names = set()
    for e in entries:
        if e["name"].startswith("MAT_") and e["t109"] == 0x0a:
            mat_names.add(e["name"])
            try:
                nh = int(e["name"][4:], 16)
                mat_by_nh[nh] = e["name"]
            except: pass
            if e["name"] not in [m["name"] for m in mat_defs]:
                mat_defs.append(e)
    
    # Build MAT name -> TX info
    mat_to_tx = {}
    for me in mat_defs:
        for j in range(me["idx"]+1, min(me["idx"]+5, len(entries))):
            ne = entries[j]
            if ne["name"].startswith("MAT_") and ne["t109"] == 0x0a: break
            if ne["name"].startswith("TX_") and ne["word0"] == 60:
                dds = extract_dds_hash(ne["name"])
                tex_base = extract_tex_base(ne["name"])
                mat_to_tx[me["name"]] = {"dds": dds, "base": tex_base}
                break
    
    # Build TX base -> DDS list (from word0=29 data entries)
    tex_base_to_dds = {}
    for e in entries:
        if e["name"].startswith("TX_") and e["word0"] == 29:
            dds = extract_dds_hash(e["name"])
            base = extract_tex_base(e["name"])
            if base not in tex_base_to_dds: tex_base_to_dds[base] = []
            if dds and dds not in [x[0] for x in tex_base_to_dds[base]]:
                tex_base_to_dds[base].append((dds, classify_tex_type(base)))
    
    # Build MESH -> MAT -> TX mapping
    mesh_maps = []
    for e in entries:
        if not (e["name"].startswith("MESH_") and e["t109"] == 0x0c): continue
        
        mat_refs = set()
        # Embedded MAT hashes
        edata = data[e["fo"]:e["fo"]+e["size"]]
        for off in range(0, len(edata)-7, 4):
            v = struct.unpack_from("<Q", edata, off)[0]
            if v in mat_by_nh:
                mat_refs.add(mat_by_nh[v])
        # Adjacent MAT ref
        for j in range(e["idx"]+1, min(e["idx"]+5, len(entries))):
            ne = entries[j]
            if ne["name"].startswith("MAT_") and ne["t109"] == 0x00:
                mat_refs.add(ne["name"]); break
            if ne["name"].startswith("MESH_") and ne["t109"] == 0x0c: break
        
        # Collect textures
        textures = []
        seen_dds = set()
        for mat_name in mat_refs:
            tx_info = mat_to_tx.get(mat_name)
            if not tx_info or not tx_info["dds"]: continue
            dds_str = f"{tx_info['dds']:016X}"
            if dds_str not in seen_dds:
                seen_dds.add(dds_str)
                textures.append({"hash": dds_str, "type": "primary", "mat": mat_name})
            
            # Related textures by base name
            tb = tx_info["base"]
            # Exact match
            if tb in tex_base_to_dds:
                for dds, ttype in tex_base_to_dds[tb]:
                    ds = f"{dds:016X}"
                    if ds not in seen_dds:
                        seen_dds.add(ds)
                        textures.append({"hash": ds, "type": ttype, "mat": mat_name})
            # Partial match (strip last suffix)
            parts = tb.rsplit('_', 1)
            if len(parts) == 2:
                partial = parts[0]
                if len(partial) > 5:  # avoid too-short matches
                    for b, dds_list in tex_base_to_dds.items():
                        if b.startswith(partial) and b != tb:
                            for dds, ttype in dds_list:
                                ds = f"{dds:016X}"
                                if ds not in seen_dds:
                                    seen_dds.add(ds)
                                    textures.append({"hash": ds, "type": ttype, "mat": mat_name})
        
        mesh_maps.append({
            "mesh": e["name"], "idx": e["idx"],
            "mats": sorted(list(mat_refs)),
            "textures": textures
        })
    return mesh_maps

# === Process all WADs ===
wad_files = sorted([f for f in os.listdir(PC_LE) if f.endswith(".wad")])
print(f"Found {len(wad_files)} WAD files")

global_mapping = {}
stats = {"total_meshes": 0, "meshes_with_tex": 0, "meshes_without_tex": 0,
         "total_tex_refs": 0, "total_mats": 0, "wads_processed": 0, "errors": 0}

t0 = time.time()
for wi, wad_name in enumerate(wad_files):
    try:
        wad_path = os.path.join(PC_LE, wad_name)
        entries, data = parse_wad(wad_path)
        mesh_maps = process_wad(wad_name, entries, data)
        
        wad_base = os.path.splitext(wad_name)[0]
        global_mapping[wad_base] = mesh_maps
        
        for m in mesh_maps:
            stats["total_meshes"] += 1
            stats["total_mats"] += len(m["mats"])
            stats["total_tex_refs"] += len(m["textures"])
            if m["textures"]: stats["meshes_with_tex"] += 1
            else: stats["meshes_without_tex"] += 1
        stats["wads_processed"] += 1
        
        if (wi + 1) % 100 == 0 or wi == 0:
            elapsed = time.time() - t0
            rate = (wi + 1) / elapsed
            eta = (len(wad_files) - wi - 1) / rate if rate > 0 else 0
            print(f"  [{wi+1}/{len(wad_files)}] {wad_name[:35]:<35} meshes={len(mesh_maps):<4} "
                  f"({rate:.1f} wad/s, ETA {eta:.0f}s)")
    except Exception as ex:
        stats["errors"] += 1
        if stats["errors"] <= 3:
            print(f"  ERROR: {wad_name}: {ex}")

elapsed = time.time() - t0
print(f"\n=== DONE in {elapsed:.1f}s ===")
print(f"WADs processed: {stats['wads_processed']}/{len(wad_files)}")
print(f"Errors: {stats['errors']}")
print(f"Total MESH entries: {stats['total_meshes']}")
print(f"  with textures: {stats['meshes_with_tex']} ({100*stats['meshes_with_tex']/max(1,stats['total_meshes']):.1f}%)")
print(f"  without textures: {stats['meshes_without_tex']}")
print(f"  total MAT refs: {stats['total_mats']}")
print(f"  total texture refs: {stats['total_tex_refs']}")
print(f"  avg textures/mesh: {stats['total_tex_refs']/max(1,stats['total_meshes']):.1f}")

# Save global mapping
out_path = os.path.join(OUT_DIR, "model_texture_mapping.json")
with open(out_path, "w") as f:
    json.dump({"stats": stats, "mapping": global_mapping}, f, indent=1)
print(f"\nMapping saved to: {out_path}")
file_size = os.path.getsize(out_path) / 1024 / 1024
print(f"File size: {file_size:.1f} MB")