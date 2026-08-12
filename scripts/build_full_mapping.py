import struct, lz4.frame, os, re, json

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

# Build MAT name hash -> MAT entry map
mat_by_name_hash = {}
mat_defs = []
for e in entries:
    if e["name"].startswith("MAT_") and e["t109"] == 0x0a:
        try:
            nh = int(e["name"][4:], 16)
            mat_by_name_hash[nh] = e
            mat_defs.append(e)
        except: pass

# Build TX DDS hash -> TX entries map (from name)
tx_by_dds_hash = {}
tx_entries_all = []
for e in entries:
    if e["name"].startswith("TX_"):
        m = re.search(r'([0-9A-Fa-f]{16})$', e["name"])
        if m:
            dds_h = int(m.group(1), 16)
            if dds_h not in tx_by_dds_hash:
                tx_by_dds_hash[dds_h] = []
            tx_by_dds_hash[dds_h].append(e)
        tx_entries_all.append(e)

# === Step 1: Extract embedded MAT hashes from MESH data ===
print("=== Step 1: Extract embedded MAT hashes from MESH data ===")
mesh_entries = [e for e in entries if e["name"].startswith("MESH_") and e["t109"] == 0x0c]

mesh_to_mats = {}  # mesh entry -> list of MAT name hashes
total_mat_refs = 0
meshes_with_mats = 0

for me in mesh_entries:
    edata = data[me["fo"]:me["fo"]+me["size"]]
    found = []
    for off in range(0, len(edata)-7, 4):
        v = struct.unpack_from("<Q", edata, off)[0]
        if v in mat_by_name_hash:
            found.append((off, v, mat_by_name_hash[v]["name"]))
    
    if found:
        meshes_with_mats += 1
        mesh_to_mats[me["idx"]] = found
        total_mat_refs += len(found)

print(f"MESH entries: {len(mesh_entries)}")
print(f"MESH with embedded MAT hashes: {meshes_with_mats}")
print(f"Total MAT references found: {total_mat_refs}")

# Show sample
for me in mesh_entries:
    if me["idx"] in mesh_to_mats:
        refs = mesh_to_mats[me["idx"]]
        print(f"\n  {me['name'][:40]} ({len(refs)} MATs):")
        for off, h, mname in refs:
            # Check if this MAT has TX entries
            mat_entry = mat_by_name_hash[h]
            # Find TX entries after this MAT definition
            tx_after = []
            for j in range(mat_entry["idx"]+1, min(mat_entry["idx"]+10, ec)):
                ne = entries[j]
                if ne["name"].startswith("MAT_") and ne["t109"] == 0x0a:
                    break
                if ne["name"].startswith("TX_"):
                    m = re.search(r'([0-9A-Fa-f]{16})$', ne["name"])
                    dds = m.group(1) if m else "?"
                    tx_after.append((ne["name"][:45], dds, ne["b111"]))
                else:
                    break
            tx_str = "; ".join(f"{tn}|{dds}" for tn, dds, b in tx_after) if tx_after else "NONE"
            print(f"    @{off:#06x} {mname} -> TX: {tx_str}")
        break  # Just show first mesh with MATs

# === Step 2: Analyze MAT -> TX linkage more carefully ===
print("\n\n=== Step 2: MAT -> TX linkage analysis ===")

# For each MAT def, check ALL following entries (not just TX_) until next MAT def
mat_to_all_entries = {}
for me in mat_defs:
    following = []
    for j in range(me["idx"]+1, min(me["idx"]+30, ec)):
        ne = entries[j]
        if ne["name"].startswith("MAT_") and ne["t109"] == 0x0a:
            break
        following.append(ne)
    mat_to_all_entries[me["name"]] = following

# Count entry types after MAT
type_counts = {}
for mname, following in mat_to_all_entries.items():
    for e in following:
        key = f"w{e['word0']}_t{e['t109']:02x}_b{e['b111']}"
        type_counts[key] = type_counts.get(key, 0) + 1

print("Entry types found after MAT definitions:")
for k, v in sorted(type_counts.items(), key=lambda x: -x[1]):
    print(f"  {k}: {v}")

# === Step 3: Check TX metadata data for MAT references ===
print("\n\n=== Step 3: TX metadata (b111=8) data analysis ===")
mat_name_hash_set = set(mat_by_name_hash.keys())

tx_meta_count = 0
tx_meta_with_mat = 0
for e in entries:
    if e["name"].startswith("TX_") and e["b111"] == 8 and e["size"] > 0:
        tx_meta_count += 1
        edata = data[e["fo"]:e["fo"]+e["size"]]
        for off in range(0, len(edata)-7, 4):
            v = struct.unpack_from("<Q", edata, off)[0]
            if v in mat_name_hash_set:
                tx_meta_with_mat += 1
                if tx_meta_with_mat <= 3:
                    print(f"  TX:{e['name'][:40]} contains MAT hash @{off:#06x}: {mat_by_name_hash[v]['name']}")
                break

print(f"TX metadata entries: {tx_meta_count}")
print(f"  with MAT hash in data: {tx_meta_with_mat}")

# === Step 4: Check if TX entries are grouped by texture name ===
print("\n\n=== Step 4: TX entry grouping by texture base name ===")
# Group TX entries by base name (without type suffix and hash)
tx_groups = {}
for e in tx_entries_all:
    # Remove TX_ prefix and hash suffix
    base = e["name"][3:]  # remove TX_
    m = re.search(r'_([0-9A-Fa-f]{16})$', base)
    if m:
        base = base[:m.start()]
    # Extract texture type (last part after _)
    parts = base.rsplit('_', 1)
    if len(parts) == 2 and parts[1] in ('normal', 'gloss', 'diffuse', 'alpha', 'm1', 'm2', 'n', 'd', 'thick'):
        tex_type = parts[1]
        tex_base = parts[0]
    else:
        tex_type = "?"
        tex_base = base
    
    if tex_base not in tx_groups:
        tx_groups[tex_base] = []
    m = re.search(r'([0-9A-Fa-f]{16})$', e["name"])
    dds = m.group(1) if m else "?"
    tx_groups[tex_base].append((tex_type, dds, e["idx"]))

# Show groups with multiple textures
multi_groups = {k: v for k, v in tx_groups.items() if len(v) > 1}
print(f"TX base names with multiple textures: {len(multi_groups)}")
for base, textures in list(multi_groups.items())[:10]:
    print(f"\n  {base}:")
    for ttype, dds, idx in textures:
        print(f"    {ttype:<10} {dds} (entry {idx})")

# === Step 5: Check if MAT data contains texture name hashes ===
print("\n\n=== Step 5: MAT data -> TX DDS hash check ===")
tx_dds_set = set(tx_by_dds_hash.keys())
mat_with_tx = 0
for me in mat_defs[:50]:
    edata = data[me["fo"]:me["fo"]+me["size"]]
    found_tx = []
    for off in range(0, len(edata)-7, 4):
        v = struct.unpack_from("<Q", edata, off)[0]
        if v in tx_dds_set:
            found_tx.append((off, v))
    if found_tx:
        mat_with_tx += 1
        if mat_with_tx <= 3:
            print(f"  {me['name']} -> TX DDS hashes: {[(hex(v)) for _, v in found_tx]}")

print(f"MAT defs with TX DDS hash in data (first 50): {mat_with_tx}")