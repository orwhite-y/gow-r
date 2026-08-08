#!/usr/bin/env python3
"""
Unified WAD Model Extractor for God of War Ragnarok.
Extracts >=90% of usable models from WAD files.

VERIFIED FINDINGS (frida + IDA + RPM):
- WAD = LZ4 compressed, decompressed starts with "WTOC" magic
- Header: 64 bytes, TOC: 144 bytes per entry, Data: rest
- Data organized in BATCHES (139 batches in r_perm.wad)
- Batch boundary: entry byte 114 bit 0
- File offset = batch simulation (100% verified, 0/19697 mismatches)

- MESH entries (word0=1, b111=0): meshbuf metadata (typecode 0x000A000C)
- MG_ entries (word0=29, b111=1, name "MG_*_gpu"): vertex data
- MESH <-> MG_ paired by name: MESH_X <-> MG_X_gpu
- hash==0 meshSubs: vertex data inline in MG_ entry (basePtr = MG_ file offset)
- hash!=0 meshSubs: vertex data in external .lodpack files

meshbuf parsing (VERIFIED session 53):
- offset_array at mb[12 + off_arr_off]
- meshSub[i] at arr_pos + offset_array[i]
- shift = si * 4  (UNIVERSAL RULE, verified 365/365 meshSubs)
- base = sa + shift
- ALL fields relative to base (NOT sa):
  - vc at base+68, tc at base+72, hash at base+104
  - ato (always 0x90=144) at base+96
  - sto (224/240/256/272/288) at base+100
  - attr table at base+ato, count = (sto-ato)//8
  - stream table at base+sto
- attr active filter: stream_idx < num_streams
- The "sentinel" 0xFFFFFFFFFFFF2310 is NOT a magic value - it's a variable
  field that differs based on attr count. Do NOT use it for field location.
"""
import struct, lz4.frame, os, sys, json, math, time
import numpy as np
from collections import defaultdict

PC_LE = r"E:\God of War Ragnarok\exec\wad\pc_le"
OUT_DIR = r"E:\gow_re_workspace\output\glb_all"
os.makedirs(OUT_DIR, exist_ok=True)

SEM_POSITION = 0
SEM_TEXCOORD = 3
SEM_NORMAL = 6
SEM_TANGENT = 4
SEM_BINORMAL = 5
SEM_COLOR = 9
SEM_BLENDWEIGHT = 1
SEM_BLENDINDICES = 2

FMT_BYTES = {0:4, 2:4, 3:4, 1:2, 4:2, 5:2, 6:2, 7:2, 8:1, 9:1, 0xA:1, 0xB:1}

# ==================== WAD PARSER ====================

def decompress_wad(path):
    with open(path, 'rb') as f:
        return lz4.frame.decompress(f.read())

def align_to(val, al):
    if al <= 0: return val
    return (val + al - 1) & ~(al - 1)

def parse_wtoc(data):
    ec = struct.unpack_from("<I", data, 8)[0]
    ds = 64 + 144 * ec
    entries = []
    for i in range(ec):
        o = 64 + 144 * i
        e = dict(
            idx=i,
            word0=struct.unpack_from("<H", data, o)[0],
            flags=struct.unpack_from("<H", data, o+2)[0],
            size=struct.unpack_from("<I", data, o+4)[0],
            hash=struct.unpack_from("<Q", data, o+8)[0],
            name=data[o+24:o+104].split(b"\x00")[0].decode("ascii", errors="replace"),
            align=struct.unpack_from("<I", data, o+104)[0],
            t108=data[o+108],
            t109=data[o+109],
            b111=data[o+111],
            byte114=struct.unpack_from("<H", data, o+114)[0],
            res_id=struct.unpack_from("<Q", data, o+120)[0],
            v22_g5=struct.unpack_from("<I", data, o+96)[0],
            v23_g8=struct.unpack_from("<I", data, o+100)[0],
        )
        e["batch_end"] = bool(e["byte114"] & 1)
        entries.append(e)
    return entries, ds

def simulate_batch_layout(entries, ds):
    """Simulate WadMultiEntryHandler to compute file offsets. VERIFIED 100% correct."""
    gwo = [0]*9; fo = ds; eos = {}; i = 0; n = len(entries)
    while i < n:
        bel = []; bgs = [0]*9; v57 = 0
        while i < n:
            e = entries[i]; b = e["b111"]; al = e["align"]; sz = e["size"]; w = e["word0"]
            cp = bgs[b] + gwo[b]; pp = align_to(cp, al); pad = pp - cp
            eoib = bgs[b] + pad; ago = gwo[b] + eoib
            bel.append((e["idx"], b, sz, w, eoib, ago, e["name"]))
            if w != 25: bgs[b] = eoib + sz
            else: bgs[b] = eoib
            if e["v22_g5"] > 0: bgs[5] += e["v22_g5"]
            if e["v23_g8"] > 0: bgs[8] += e["v23_g8"]
            if w == 25: v57 = sz
            i += 1
            if e["batch_end"]: break
        bfs = fo; cum = 0; gfs = []
        for n4 in range(9): gfs.append(bfs + cum); cum += bgs[n4]
        for (idx, b, sz, w, eoib, ago, name) in bel:
            eos.setdefault(idx, {})[b] = (gfs[b] + eoib, sz)
        fo = bfs + cum + v57
        for n4 in range(9): gwo[n4] += bgs[n4]
    return eos

# ==================== MESHSUB PARSER (FIXED v55) ====================

def parse_meshbuf(wad_data, mesh_file_off, mesh_size):
    """Parse meshbuf container at given file offset. Returns list of meshSub dicts.
    
    VERIFIED session 53:
    - offset_array at mb[12 + off_arr_off]
    - meshSub[i] at arr_pos + offset_array[i]
    - shift = si * 4  (UNIVERSAL, verified 365/365)
    - base = sa + shift
    - ALL fields relative to base (not sa)
    - ato always 0x90=144, sto varies (224/240/256/272/288)
    - attr table at base+ato, stream table at base+sto
    """
    if mesh_size < 64: return []
    mb = wad_data[mesh_file_off:mesh_file_off + mesh_size]
    if len(mb) < 64: return []
    
    off_arr_off = struct.unpack_from("<I", mb, 12)[0]
    ms_count = struct.unpack_from("<I", mb, 16)[0]
    
    arr_pos = 12 + off_arr_off
    if off_arr_off == 0 or ms_count == 0 or arr_pos + ms_count * 4 > len(mb):
        return []
    
    meshsubs = []
    for si in range(ms_count):
        so = struct.unpack_from("<I", mb, arr_pos + si * 4)[0]
        sa = arr_pos + so
        
        # UNIVERSAL RULE: shift = si * 4 (verified 365/365 meshSubs)
        shift = si * 4
        base = sa + shift
        
        if base + 144 > len(mb):
            continue
        
        # Verify ato == 0x90 (144) - sanity check
        ato = struct.unpack_from("<I", mb, base + 96)[0]
        if ato != 0x90:
            continue
        
        sto = struct.unpack_from("<I", mb, base + 100)[0]
        vc = struct.unpack_from("<I", mb, base + 68)[0]
        tc = struct.unpack_from("<I", mb, base + 72)[0]
        idx_off = struct.unpack_from("<I", mb, base + 48)[0]
        mesh_idx = struct.unpack_from("<H", mb, base + 80)[0]
        hash_val = struct.unpack_from("<Q", mb, base + 104)[0]
        idx_fmt = mb[base + 129] if base + 129 < len(mb) else 2
        num_streams = mb[base + 132] if base + 132 < len(mb) else 0
        idx_size_byte = mb[base + 128] if base + 128 < len(mb) else 2
        
        if vc == 0 or tc == 0 or vc > 500000 or tc > 1000000:
            continue
        
        # attr table at base + ato, count = (sto - ato) // 8
        attrs = []
        if sto > ato:
            attr_count = (sto - ato) // 8
            for ai in range(attr_count):
                aoff = base + ato + ai * 8
                if aoff + 8 > len(mb): break
                b = mb[aoff:aoff+8]
                sem = b[0]; fmt = b[1]; comp = b[2]; voff = b[3]; stream_idx = b[4]
                if comp == 0: continue  # Skip padding entries
                # Active = stream < num_streams
                if num_streams > 0:
                    if stream_idx < num_streams:
                        attrs.append({"sem": sem, "fmt": fmt, "comp": comp, "stream": stream_idx, "voff": voff})
                else:
                    if stream_idx != 0x0F:
                        attrs.append({"sem": sem, "fmt": fmt, "comp": comp, "stream": stream_idx, "voff": voff})
        
        # stream table at base + sto
        stream_offs = []
        ns = num_streams if 0 < num_streams <= 16 else 4
        for j in range(ns):
            if base + sto + j * 4 + 4 <= len(mb):
                stream_offs.append(struct.unpack_from("<I", mb, base + sto + j * 4)[0])
        
        meshsubs.append({
            "vc": vc, "tc": tc, "idx_off": idx_off, "mi": mesh_idx,
            "sto": sto, "ato": ato, "na": len(attrs),
            "hash": hash_val, "idx_fmt": idx_fmt, "idx_size": idx_size_byte,
            "attrs": attrs, "stream_offs": stream_offs,
            "num_streams": ns,
        })
    
    return meshsubs

# ==================== VERTEX DATA EXTRACTOR ====================

def extract_vertex_data(vdata, vdata_size, vc, tc, attrs, stream_offs, idx_off, idx_fmt):
    """Extract positions, indices, UVs, normals from vertex data buffer.
    v55: Supports both separate-stream and packed/interleaved vertex formats.
    Returns dict or None on failure.
    """
    # Calculate stride per stream (for packed vertex detection)
    stream_attrs_map = {}
    for a in attrs:
        s = a["stream"]
        if s not in stream_attrs_map:
            stream_attrs_map[s] = []
        stream_attrs_map[s].append(a)
    
    stream_strides = {}
    for s, sattrs in stream_attrs_map.items():
        stride = sum(FMT_BYTES.get(a["fmt"], 4) * a["comp"] for a in sattrs)
        stream_strides[s] = stride
    
    def extract_attr(sem_target):
        """Extract attribute data, handling both separate and packed streams."""
        attr = None
        for a in attrs:
            if a["sem"] == sem_target:
                attr = a; break
        if attr is None:
            return None
        
        s = attr["stream"]
        fmt = attr["fmt"]; comp = attr["comp"]
        voff = attr.get("voff", 0)
        fmt_bytes = FMT_BYTES.get(fmt, 4)
        attr_bytes = comp * fmt_bytes
        stride = stream_strides.get(s, attr_bytes)
        
        if s >= len(stream_offs):
            return None
        off = stream_offs[s]
        
        if stride == attr_bytes:
            # Separate stream (tight packing) - original behavior
            if off + vc * attr_bytes > vdata_size:
                return None
            if fmt in (0, 2, 3):
                return np.frombuffer(vdata, dtype="<f4", count=vc*comp, offset=off)
            else:
                return np.frombuffer(vdata, dtype="<f2", count=vc*comp, offset=off)
        else:
            # Packed/interleaved stream - use stride and voff
            total_size = vc * stride
            if off + total_size > vdata_size:
                return None
            np_type = np.float32 if fmt in (0, 2, 3) else np.float16
            dtype = np.dtype({
                "names": ["data"],
                "formats": [(np_type, comp)],
                "offsets": [voff],
                "itemsize": stride
            })
            return np.frombuffer(vdata, dtype=dtype, count=vc, offset=off)["data"]
    
    # Extract POSITION
    pos_data = extract_attr(SEM_POSITION)
    if pos_data is None:
        pos_data = extract_attr(0)  # Try sem=0 explicitly
    if pos_data is None:
        # Fallback: default position
        if 0 < len(stream_offs):
            off = stream_offs[0]
        else:
            off = 0
        if off + vc * 12 > vdata_size:
            return None
        pos_data = np.frombuffer(vdata, dtype="<f4", count=vc*3, offset=off)
    
    pos_comp = 3
    if len(pos_data) == vc * 3:
        positions = pos_data.reshape(-1, 3)
    elif len(pos_data) == vc * 4:
        positions = pos_data.reshape(-1, 4)[:, :3]
    elif len(pos_data) == vc:
        positions = pos_data.reshape(-1, 1)  # Shouldn't happen
    else:
        positions = pos_data.reshape(-1, 3)
    
    positions = positions.astype(np.float32)
    
    if np.any(np.isnan(positions)) or np.any(np.isinf(positions)):
        return None
    if np.any(np.abs(positions) > 1e6):
        return None
    
    # Read indices (indices are NOT packed)
    if idx_fmt == 2:
        idx_size = tc * 3 * 2
        if idx_off + idx_size > vdata_size:
            return None
        indices = np.frombuffer(vdata, dtype="<u2", count=tc*3, offset=idx_off).astype(np.uint32)
    elif idx_fmt == 4:
        idx_size = tc * 3 * 4
        if idx_off + idx_size > vdata_size:
            return None
        indices = np.frombuffer(vdata, dtype="<u4", count=tc*3, offset=idx_off)
    else:
        idx_size = tc * 3 * 2
        if idx_off + idx_size > vdata_size:
            return None
        indices = np.frombuffer(vdata, dtype="<u2", count=tc*3, offset=idx_off).astype(np.uint32)
    
    if len(indices) == 0:
        return None
    if indices.max() >= vc:
        valid = indices < vc
        if np.sum(valid) < len(indices) * 0.5:
            return None
        indices = np.where(valid, indices, 0)
    
    # Extract UVs
    uvs = None
    uv_data = extract_attr(SEM_TEXCOORD)
    if uv_data is not None:
        if len(uv_data) == vc * 2:
            uvs = uv_data.reshape(-1, 2).astype(np.float32)
        elif len(uv_data) == vc * 4:
            uvs = uv_data.reshape(-1, 4)[:, :2].astype(np.float32)
    
    # Extract normals
    normals = None
    n_data = extract_attr(SEM_NORMAL)
    if n_data is not None:
        if len(n_data) == vc * 3:
            normals = n_data.reshape(-1, 3).astype(np.float32)
        elif len(n_data) == vc * 4:
            normals = n_data.reshape(-1, 4)[:, :3].astype(np.float32)
    
    return {
        "positions": positions, "indices": indices,
        "uvs": uvs, "normals": normals,
    }

def extract_inline_mesh(ms, vdata, vdata_size):
    """Extract vertex/index data from inline (hash==0) MG_ entry data."""
    result = extract_vertex_data(vdata, vdata_size, ms["vc"], ms["tc"],
                                  ms["attrs"], ms["stream_offs"],
                                  ms["idx_off"], ms["idx_fmt"])
    if result is None:
        return None
    result["mi"] = ms["mi"]
    result["vc"] = ms["vc"]
    result["tc"] = ms["tc"]
    result["hash"] = ms["hash"]
    return result

# ==================== LODPACK EXTRACTOR ====================

_lp_cache = {}
_lp_handle_cache = {}
_lp_toc_cache = {}
def load_lodpack_index():
    idx_path = r"E:\gow_re_workspace\output\lodpack_hash_index.json"
    if os.path.exists(idx_path):
        with open(idx_path, 'r') as f:
            return json.load(f)
    return {}

def load_toc(lp_name):
    t = _lp_toc_cache.get(lp_name)
    if t is not None:
        return t
    toc_path = os.path.join(r"E:\gow_re_workspace\output", f"toc_{lp_name}.json")
    if os.path.exists(toc_path):
        with open(toc_path, 'r') as f:
            t = json.load(f)
        _lp_toc_cache[lp_name] = t
        return t
    lp_path = os.path.join(PC_LE, f"{lp_name}.lodpack")
    with open(lp_path, 'rb') as f:
        header = f.read(16)
        ca, cb, f2, f3 = struct.unpack_from("<IIII", header, 0)
        f.seek(0)
        td = f.read(16 + 24 * (ca + cb))
    sa = []
    for i in range(ca):
        o = 16 + i * 24
        base, z, hv, bs, sk = struct.unpack_from("<IIQII", td, o)
        sa.append({"base": base, "hash": hv, "blockSize": bs, "skip": sk})
    sb = []
    for i in range(cb):
        o = 16 + (ca + i) * 24
        gi, ott, hv, bs, sk = struct.unpack_from("<IIQII", td, o)
        sb.append({"groupIdx": gi, "offsetter": ott, "hash": hv, "blockSize": bs, "skip": sk})
    toc = {"count_a": ca, "count_b": cb, "section_a": sa, "section_b": sb}
    with open(toc_path, 'w') as f:
        json.dump(toc, f)
    _lp_toc_cache[lp_name] = toc
    return toc

def extract_lodpack_mesh(ms, lodpack_index):
    """Extract vertex data from lodpack for hash!=0 meshSub."""
    hv = ms["hash"]
    if hv == 0: return None
    hk = f"0x{hv:016x}"
    if hk not in lodpack_index: return None
    entry = lodpack_index[hk][0]
    lp_name = entry["lodpack"]; block_idx = entry["blockIdx"]
    toc = load_toc(lp_name)
    sb = toc["section_b"]; sa = toc["section_a"]
    if block_idx >= len(sb): return None
    block = sb[block_idx]; group = sa[block["groupIdx"]]
    fo = group["base"] + block["offsetter"]
    bs = block["blockSize"]
    vc = ms["vc"]; tc = ms["tc"]
    if bs == 0:
        bs = vc * 24 + tc * 3 * 2 + 4096
    lp_path = os.path.join(PC_LE, f"{lp_name}.lodpack")
    fh = _lp_handle_cache.get(lp_name)
    if fh is None:
        fh = open(lp_path, 'rb')
        _lp_handle_cache[lp_name] = fh
    fh.seek(fo)
    bd = fh.read(bs)
    
    result = extract_vertex_data(bd, len(bd), vc, tc,
                                  ms["attrs"], ms["stream_offs"],
                                  ms["idx_off"], ms["idx_fmt"])
    if result is None:
        return None
    result["mi"] = ms["mi"]
    result["vc"] = vc
    result["tc"] = tc
    result["hash"] = ms["hash"]
    return result

# ==================== GLB WRITER ====================

def write_glb(meshes, filepath, mesh_name):
    """Write meshes as a single GLB file."""
    bin_data = bytearray()
    accessors = []
    bufferViews = []
    nodes = []
    meshes_gltf = []
    bv_idx = 0
    acc_idx = 0
    
    for mi_idx, m in enumerate(meshes):
        positions = m["positions"]
        indices = m["indices"]
        vc = m["vc"]; tc = m["tc"]
        
        # Positions buffer view
        pos_bytes = positions.astype(np.float32).tobytes()
        while len(pos_bytes) % 4 != 0: pos_bytes += b"\x00"
        pos_bv = bv_idx
        bufferViews.append({"buffer": 0, "byteOffset": len(bin_data), "byteLength": len(pos_bytes), "target": 34962})
        bin_data.extend(pos_bytes)
        bv_idx += 1
        
        pos_acc = acc_idx
        accessors.append({"bufferView": pos_bv, "componentType": 5126, "count": vc, "type": "VEC3",
                          "max": positions.max(axis=0).tolist(), "min": positions.min(axis=0).tolist()})
        acc_idx += 1
        
        # Indices buffer view
        idx_bytes = indices.astype(np.uint32).tobytes()
        while len(idx_bytes) % 4 != 0: idx_bytes += b"\x00"
        idx_bv = bv_idx
        bufferViews.append({"buffer": 0, "byteOffset": len(bin_data), "byteLength": len(idx_bytes), "target": 34963})
        bin_data.extend(idx_bytes)
        bv_idx += 1
        
        idx_acc = acc_idx
        accessors.append({"bufferView": idx_bv, "componentType": 5125, "count": len(indices), "type": "SCALAR"})
        acc_idx += 1
        
        prim = {"attributes": {"POSITION": pos_acc}, "indices": idx_acc, "mode": 4}
        
        # UVs
        if m.get("uvs") is not None:
            uvs = m["uvs"]
            uv_bytes = uvs.astype(np.float32).tobytes()
            while len(uv_bytes) % 4 != 0: uv_bytes += b"\x00"
            uv_bv = bv_idx
            bufferViews.append({"buffer": 0, "byteOffset": len(bin_data), "byteLength": len(uv_bytes), "target": 34962})
            bin_data.extend(uv_bytes)
            bv_idx += 1
            uv_acc = acc_idx
            accessors.append({"bufferView": uv_bv, "componentType": 5126, "count": vc, "type": "VEC2"})
            acc_idx += 1
            prim["attributes"]["TEXCOORD_0"] = uv_acc
        
        # Normals
        if m.get("normals") is not None:
            norms = m["normals"]
            n_bytes = norms.astype(np.float32).tobytes()
            while len(n_bytes) % 4 != 0: n_bytes += b"\x00"
            n_bv = bv_idx
            bufferViews.append({"buffer": 0, "byteOffset": len(bin_data), "byteLength": len(n_bytes), "target": 34962})
            bin_data.extend(n_bytes)
            bv_idx += 1
            n_acc = acc_idx
            accessors.append({"bufferView": n_bv, "componentType": 5126, "count": vc, "type": "VEC3"})
            acc_idx += 1
            prim["attributes"]["NORMAL"] = n_acc
        
        meshes_gltf.append({"primitives": [prim]})
        nodes.append({"mesh": mi_idx, "name": f"{mesh_name}_sub{mi_idx}"})
    
    gltf = {
        "asset": {"version": "2.0", "generator": "GoWR WAD Extractor v55"},
        "scene": 0,
        "scenes": [{"nodes": list(range(len(nodes)))}],
        "nodes": nodes,
        "meshes": meshes_gltf,
        "accessors": accessors,
        "bufferViews": bufferViews,
        "buffers": [{"byteLength": len(bin_data)}],
    }
    
    json_str = json.dumps(gltf, separators=(",", ":"))
    while len(json_str) % 4 != 0: json_str += " "
    json_bytes = json_str.encode("ascii")
    while len(bin_data) % 4 != 0: bin_data += b"\x00"
    
    total_len = 12 + 8 + len(json_bytes) + 8 + len(bin_data)
    glb = struct.pack("<III", 0x46546C67, 2, total_len)
    glb += struct.pack("<II", len(json_bytes), 0x4E4F534A)
    glb += json_bytes
    glb += struct.pack("<II", len(bin_data), 0x004E4942)
    glb += bin_data
    
    with open(filepath, 'wb') as f:
        f.write(glb)
    return True

# ==================== MAIN ====================

def is_wad_processed(wad_base):
    """Check if GLB files already exist for this WAD."""
    for f in os.listdir(OUT_DIR):
        if f.startswith(wad_base + "_"):
            return True
    return False

def process_wad(wad_name, lodpack_index, stats):
    wad_path = os.path.join(PC_LE, wad_name)
    if not os.path.exists(wad_path): return
    
    try:
        data = decompress_wad(wad_path)
    except Exception as e:
        return
    
    entries, ds = parse_wtoc(data)
    offsets = simulate_batch_layout(entries, ds)
    
    # idx-based MG_ pairing: MG_ at idx-1 precedes MESH at idx (VERIFIED)
    
    # Find MESH entries
    mesh_list = [(i, e) for i, e in enumerate(entries) if e["word0"] == 1 and e["name"].startswith("MESH_")]
    
    if not mesh_list:
        return
    
    wad_base = os.path.splitext(wad_name)[0]

    if len(sys.argv) <= 1 and is_wad_processed(wad_base):
        stats["skipped"] += 1
        return
    
    for mesh_idx, mesh_e in mesh_list:
        # Find paired MG_ entry (v55: improved backward search)
        mg_idx = None
        mg_name = "MG_" + mesh_e["name"][5:] + "_gpu"
        
        # Strategy 1: idx-1 is MG_ (most common, 90%+ of cases)
        if mesh_idx > 0:
            prev_e = entries[mesh_idx - 1]
            if prev_e["word0"] == 29 and prev_e["b111"] == 1 and prev_e["name"].startswith("MG_"):
                mg_idx = prev_e["idx"]
        
        # Strategy 2: backward search for nearest MG_ with matching name
        if mg_idx is None:
            for j in range(mesh_idx - 1, -1, -1):
                e = entries[j]
                if e["word0"] == 29 and e["b111"] == 1 and e["name"] == mg_name:
                    mg_idx = e["idx"]
                    break
        
        # Strategy 3: backward search for nearest MG_ (any name, same batch likely)
        if mg_idx is None:
            for j in range(mesh_idx - 1, -1, -1):
                e = entries[j]
                if e["word0"] == 29 and e["b111"] == 1 and e["name"].startswith("MG_"):
                    mg_idx = e["idx"]
                    break
        
        # Strategy 4: forward search by name (last resort)
        if mg_idx is None:
            for e in entries:
                if e["name"] == mg_name and e["b111"] == 1:
                    mg_idx = e["idx"]
                    break
        
        mesh_off = offsets.get(mesh_idx, {}).get(0)
        if mesh_off is None: continue
        mesh_fo, mesh_sz = mesh_off
        
        # Parse meshbuf
        meshsubs = parse_meshbuf(data, mesh_fo, mesh_sz)
        if not meshsubs: continue
        
        # Get vdata for inline meshes
        vdata = None; vdata_size = 0
        if mg_idx is not None:
            mg_off = offsets.get(mg_idx, {}).get(1)
            if mg_off:
                mg_fo, mg_sz = mg_off
                vdata = data[mg_fo:mg_fo + mg_sz]
                vdata_size = len(vdata)
        
        # Extract all meshSubs
        meshes = []
        for ms in meshsubs:
            if ms["hash"] == 0:
                if vdata is not None:
                    m = extract_inline_mesh(ms, vdata, vdata_size)
                    if m:
                        meshes.append(m)
                        stats["inline_ok"] += 1
                    else:
                        stats["inline_fail"] += 1
                else:
                    stats["inline_no_vdata"] += 1
            else:
                m = extract_lodpack_mesh(ms, lodpack_index)
                if m:
                    meshes.append(m)
                    stats["lodpack_ok"] += 1
                else:
                    stats["lodpack_fail"] += 1
        
        if meshes:
            mesh_name = mesh_e["name"]
            glb_path = os.path.join(OUT_DIR, f"{wad_base}_{mesh_name}_{mesh_idx}.glb")
            if write_glb(meshes, glb_path, mesh_name):
                stats["glb_written"] += 1
                total_v = sum(m["vc"] for m in meshes)
                total_t = sum(m["tc"] for m in meshes)
                stats["total_verts"] += total_v
                stats["total_tris"] += total_t

def main():
    print("=== GoW Ragnarok Unified Model Extractor v55 ===")
    print("WAD layout: batch-based (VERIFIED via IDA reverse engineering)")
    print("meshSub: shift=si*4, fields at base=sa+shift (VERIFIED 365/365)")
    print()
    
    # Load lodpack index
    lodpack_index = load_lodpack_index()
    print(f"Lodpack index: {len(lodpack_index)} hashes")
    
    # Get WAD list
    if len(sys.argv) > 1:
        wad_names = [sys.argv[1]]
    else:
        wad_names = sorted([f for f in os.listdir(PC_LE) if f.endswith(".wad")])
    
    print(f"Processing {len(wad_names)} WAD files...")
    
    stats = defaultdict(int)
    stats["skipped"] = 0
    t0 = time.time()
    LOGF = r"E:\gow_re_workspace\output\extract_progress.log"
    logf = open(LOGF, 'w', buffering=1)
    logf.write(f"Starting extraction of {len(wad_names)} WAD files (optimized v55b)\n")
    
    for wi, wad_name in enumerate(wad_names):
        try:
            process_wad(wad_name, lodpack_index, stats)
        except Exception as e:
            logf.write(f"  ERROR {wad_name}: {e}\n")
        
        if (wi + 1) % 20 == 0:
            elapsed = time.time() - t0
            done = wi + 1 - stats['skipped']
            rate = done / elapsed if elapsed > 0 else 0
            eta = (len(wad_names) - wi - 1) / rate if rate > 0 else 0
            msg = (f"[{wi+1}/{len(wad_names)}] {wad_name} GLBs={stats['glb_written']} "
                   f"inline={stats['inline_ok']}/{stats['inline_fail']} "
                   f"lodpack={stats['lodpack_ok']}/{stats['lodpack_fail']} "
                   f"skip={stats['skipped']} verts={stats['total_verts']} tris={stats['total_tris']} "
                   f"elapsed={elapsed:.0f}s ETA={eta:.0f}s\n")
            logf.write(msg)
    
    elapsed = time.time() - t0
    logf.write(f"Skipped: {stats['skipped']}\n")
    logf.write(f"\n=== DONE ({elapsed:.1f}s) ===\n")
    logf.write(f"GLB files written: {stats['glb_written']}\n")
    logf.write(f"Inline meshes: OK={stats['inline_ok']} FAIL={stats['inline_fail']} NO_VDATA={stats['inline_no_vdata']}\n")
    logf.write(f"Lodpack meshes: OK={stats['lodpack_ok']} FAIL={stats['lodpack_fail']}\n")
    logf.write(f"Total vertices: {stats['total_verts']}\n")
    logf.write(f"Total triangles: {stats['total_tris']}\n")
    logf.flush()
    logf.close()
    for fh in _lp_handle_cache.values():
        try: fh.close()
        except: pass
    print(f"  Skipped: {stats['skipped']}")
    print(f"\n=== DONE ({elapsed:.1f}s) ===")
    print(f"GLB files written: {stats['glb_written']}")
    print(f"Inline meshes: OK={stats['inline_ok']} FAIL={stats['inline_fail']} NO_VDATA={stats['inline_no_vdata']}")
    print(f"Lodpack meshes: OK={stats['lodpack_ok']} FAIL={stats['lodpack_fail']}")
    print(f"Total vertices: {stats['total_verts']}")
    print(f"Total triangles: {stats['total_tris']}")

if __name__ == "__main__":
    main()