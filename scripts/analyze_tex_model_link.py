import struct, lz4.frame, os, re

PC_LE = r"E:\God of War Ragnarok\exec\wad\pc_le"
wad_name = "alf_bluff100_entrance.wad"

# === Parse WAD ===
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
    if align > 0:
        fo = (fo + align - 1) & ~(align - 1)
    cur = fo + size
    
    entries.append({"idx": i, "word0": word0, "size": size, "hash": hash_val,
                     "name": name, "t109": t109, "b111": b111, "fo": fo})

mesh_entries = [e for e in entries if e["name"].startswith("MESH_")]
mat_entries = [e for e in entries if e["name"].startswith("MAT_")]
tx_entries = [e for e in entries if e["name"].startswith("TX_")]
print(f"Total: {ec}, MESH: {len(mesh_entries)}, MAT: {len(mat_entries)}, TX: {len(tx_entries)}")

# === MAT hash field vs name hash ===
print("\n=== MAT: hash field vs name hash ===")
for me in mat_entries[:5]:
    name_hash_str = me["name"][4:]
    try: name_hash = int(name_hash_str, 16)
    except: name_hash = 0
    m = "MATCH" if name_hash == me["hash"] else "MISMATCH"
    print(f"  {me['name'][:40]:<40} field={me['hash']:#018x} name={name_hash:#018x} {m}")

# === TX: hash field vs DDS hash in name ===
print("\n=== TX: hash field vs DDS hash in name ===")
for te in tx_entries[:5]:
    m = re.search(r'([0-9A-Fa-f]{16})$', te["name"])
    dds_hash = int(m.group(1), 16) if m else 0
    match = "MATCH" if dds_hash == te["hash"] else "MISMATCH"
    print(f"  {te['name'][:50]:<50} field={te['hash']:#018x} dds={dds_hash:#018x} {match}")

# === Entry ordering ===
print("\n=== Entry ordering (first 30) ===")
for e in entries[:30]:
    etype = "MESH" if e["name"].startswith("MESH_") else \
            "MAT" if e["name"].startswith("MAT_") else \
            "TX" if e["name"].startswith("TX_") else \
            "MG" if e["name"].startswith("MG_") else f"w{e['word0']}"
    print(f"  [{e['idx']:5d}] {etype:<6} {e['name'][:55]}")

# === Parse texpack TOC (only read header + TOC, not full file) ===
print("\n=== Texpack TOC cross-reference ===")
texpack_name = "050_alfheim1_alfxpl1.texpack"
tp_path = os.path.join(PC_LE, texpack_name)

with open(tp_path, "rb") as f:
    # Read header (first 0x38 bytes)
    hdr = f.read(0x38)
    texSectionOff, blocksCount, blocksInfoOff, TexsCount = struct.unpack_from("<IIII", hdr, 0x20)
    print(f"  TexsCount={TexsCount}, texSectionOff={texSectionOff:#x}")
    
    # Read TOC (24 bytes per entry starting at 0x38)
    toc_data = f.read(24 * TexsCount)

tex_infos = []
for i in range(TexsCount):
    o = i * 24
    fh, uh, bo = struct.unpack_from("<QQQ", toc_data, o)
    tex_infos.append((fh, uh, bo))

# Build hash sets
all_wad_hashes = {e["hash"]: e for e in entries}
mat_hashes = {e["hash"]: e for e in mat_entries}
mesh_hashes = {e["hash"]: e for e in mesh_entries}
tx_hashes = {e["hash"]: e for e in tx_entries}
tp_uh_set = {uh for fh, uh, bo in tex_infos}
tp_fh_set = {fh for fh, uh, bo in tex_infos}

# Cross-reference uh
uh_mat = sum(1 for _, uh, _ in tex_infos if uh in mat_hashes)
uh_mesh = sum(1 for _, uh, _ in tex_infos if uh in mesh_hashes)
uh_tx = sum(1 for _, uh, _ in tex_infos if uh in tx_hashes)
uh_any = sum(1 for _, uh, _ in tex_infos if uh in all_wad_hashes)

# Cross-reference fh with TX hash
fh_tx = sum(1 for fh, _, _ in tex_infos if fh in tx_hashes)

# TX hash matches uh/fh
tx_hash_uh = sum(1 for te in tx_entries if te["hash"] in tp_uh_set)
tx_hash_fh = sum(1 for te in tx_entries if te["hash"] in tp_fh_set)

# MAT hash matches uh
mat_hash_uh = sum(1 for me in mat_entries if me["hash"] in tp_uh_set)
mat_name_uh = 0
for me in mat_entries:
    try:
        nh = int(me["name"][4:], 16)
        if nh in tp_uh_set: mat_name_uh += 1
    except: pass

print(f"  uh matches MAT field: {uh_mat}/{TexsCount}")
print(f"  uh matches MESH field: {uh_mesh}/{TexsCount}")
print(f"  uh matches TX field: {uh_tx}/{TexsCount}")
print(f"  uh matches ANY WAD: {uh_any}/{TexsCount}")
print(f"  fh matches TX field: {fh_tx}/{TexsCount}")
print(f"  TX hash matches texpack uh: {tx_hash_uh}/{len(tx_entries)}")
print(f"  TX hash matches texpack fh: {tx_hash_fh}/{len(tx_entries)}")
print(f"  MAT hash field matches texpack uh: {mat_hash_uh}/{len(mat_entries)}")
print(f"  MAT name hash matches texpack uh: {mat_name_uh}/{len(mat_entries)}")

# === Check MAT data for embedded hash references ===
print("\n=== MAT entry data analysis (looking for hash refs) ===")
# Collect all known hashes to search for in MAT data
known_hashes = set()
for e in entries:
    known_hashes.add(e["hash"])
for fh, uh, bo in tex_infos:
    known_hashes.add(fh)
    known_hashes.add(uh)

for me in mat_entries[:3]:
    mat_data = data[me["fo"]:me["fo"]+me["size"]]
    print(f"\n  {me['name']} size={me['size']}")
    # Search for any 8-byte value that matches a known hash
    found = []
    for off in range(0, len(mat_data)-7, 4):
        v = struct.unpack_from("<Q", mat_data, off)[0]
        if v in known_hashes and v != 0:
            # Find what it matches
            if v in tx_hashes:
                found.append((off, "TX", tx_hashes[v]["name"][:40]))
            elif v in mat_hashes:
                found.append((off, "MAT", mat_hashes[v]["name"][:40]))
            elif v in mesh_hashes:
                found.append((off, "MESH", mesh_hashes[v]["name"][:40]))
            elif v in tp_fh_set:
                found.append((off, "TEXPACK_FH", f"{v:016X}"))
            elif v in tp_uh_set:
                found.append((off, "TEXPACK_UH", f"{v:016X}"))
    if found:
        for off, typ, name in found[:10]:
            print(f"    @{off:#06x}: {typ} -> {name}")
    else:
        # Show first 128 bytes as hex
        print(f"    No hash matches found. First 128 bytes:")
        for off in range(0, min(128, len(mat_data)), 16):
            hex_str = " ".join(f"{b:02x}" for b in mat_data[off:off+16])
            print(f"      {off:04x}: {hex_str}")