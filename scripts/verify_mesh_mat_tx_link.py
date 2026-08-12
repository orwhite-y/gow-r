import struct, lz4.frame, os, re

PC_LE = r"E:\God of War Ragnarok\exec\wad\pc_le"
wad_name = "alf_bluff100_entrance.wad"

with open(os.path.join(PC_LE, wad_name), "rb") as f:
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

# === Build MAT definition -> TX entries mapping ===
# MAT def: t109=0x0a, name starts with MAT_
# TX metadata: word0=1, t109=0x00, b111=8, name starts with TX_
# TX streaming: word0=29, t109=0x19, b111=1, name starts with TX_
# TX inline: word0=29, t109=0x19, b111=2, name starts with TX_

mat_defs = {}  # name -> {idx, tx_entries: []}
for i, e in enumerate(entries):
    if e["name"].startswith("MAT_") and e["t109"] == 0x0a:
        if e["name"] not in mat_defs:
            mat_defs[e["name"]] = {"idx": i, "tx_entries": [], "mat_ref_entries": []}
        # Look at following entries until next MAT_ or non-TX/non-MAT entry
        for j in range(i+1, min(i+20, ec)):
            ne = entries[j]
            if ne["name"].startswith("MAT_") and ne["t109"] == 0x0a:
                break
            if ne["name"].startswith("TX_"):
                mat_defs[e["name"]]["tx_entries"].append(j)
            elif ne["name"].startswith("MAT_"):
                # MAT reference (t109=00) - also belongs to this group?
                mat_defs[e["name"]]["mat_ref_entries"].append(j)
            else:
                break  # Different type, stop

# === Show MAT -> TX mapping ===
print("=== MAT definition -> TX entries mapping ===")
multi_tx = 0
single_tx = 0
zero_tx = 0
for mname, info in list(mat_defs.items())[:20]:
    tx_count = len(info["tx_entries"])
    if tx_count > 1: multi_tx += 1
    elif tx_count == 1: single_tx += 1
    else: zero_tx += 1
    
    tx_names = [entries[j]["name"][:50] for j in info["tx_entries"][:5]]
    mat_refs = len(info["mat_ref_entries"])
    print(f"  {mname[:35]:<35} tx_count={tx_count} mat_refs={mat_refs}")
    for tn in tx_names:
        print(f"    -> {tn}")

print(f"\nSummary: multi_tx={multi_tx}, single_tx={single_tx}, zero_tx={zero_tx}, total_mats={len(mat_defs)}")

# === Build MESH -> MAT reference mapping ===
print("\n\n=== MESH -> MAT reference mapping ===")
mesh_to_mat = {}
mesh_entries = [e for e in entries if e["name"].startswith("MESH_") and e["t109"] == 0x0c]
for me in mesh_entries:
    # Look at following entries for MAT reference (t109=00, name starts with MAT_)
    mat_ref = None
    for j in range(me["idx"]+1, min(me["idx"]+5, ec)):
        ne = entries[j]
        if ne["name"].startswith("MAT_") and ne["t109"] == 0x00:
            mat_ref = ne["name"]
            break
        if ne["name"].startswith("MESH_") and ne["t109"] == 0x0c:
            break  # Next mesh, no MAT ref
    mesh_to_mat[me["name"]] = mat_ref

# Show sample mappings
for me in mesh_entries[:15]:
    mat_ref = mesh_to_mat.get(me["name"])
    # Find TX entries for this MAT
    tx_hashes = []
    if mat_ref and mat_ref in mat_defs:
        for tx_idx in mat_defs[mat_ref]["tx_entries"]:
            tx_name = entries[tx_idx]["name"]
            m = re.search(r'([0-9A-Fa-f]{16})$', tx_name)
            if m:
                tx_hashes.append(m.group(1))
    print(f"  {me['name'][:35]:<35} -> {mat_ref or 'NONE':<35} -> {', '.join(tx_hashes[:3]) if tx_hashes else 'NONE'}")

# === Check wraplod_rkyrock_med_06 texture set ===
print("\n\n=== wraplod_rkyrock_med_06 texture set ===")
for i, e in enumerate(entries):
    if "rkyrock_med_06" in e["name"]:
        print(f"  [{i:5d}] w{e['word0']:<3} t109={e['t109']:02x} b111={e['b111']} {e['name'][:60]}")

# === Count how many MESH have MAT refs and how many MAT refs have TX entries ===
print("\n\n=== Coverage statistics ===")
mesh_with_mat = sum(1 for v in mesh_to_mat.values() if v is not None)
mesh_without_mat = sum(1 for v in mesh_to_mat.values() if v is None)
mat_with_tx = sum(1 for info in mat_defs.values() if len(info["tx_entries"]) > 0)
mat_without_tx = sum(1 for info in mat_defs.values() if len(info["tx_entries"]) == 0)
print(f"MESH entries: {len(mesh_entries)}")
print(f"  with MAT ref: {mesh_with_mat}")
print(f"  without MAT ref: {mesh_without_mat}")
print(f"MAT definitions: {len(mat_defs)}")
print(f"  with TX entries: {mat_with_tx}")
print(f"  without TX entries: {mat_without_tx}")