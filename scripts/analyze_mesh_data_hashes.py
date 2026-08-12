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

# Build all known hash sets
mat_name_hashes = {}  # name_hash -> mat_name
mat_entries = [e for e in entries if e["name"].startswith("MAT_") and e["t109"] == 0x0a]
for me in mat_entries:
    try:
        nh = int(me["name"][4:], 16)
        mat_name_hashes[nh] = me["name"]
    except: pass

mat_field_hashes = {e["hash"]: e["name"] for e in mat_entries}
mesh_entries = [e for e in entries if e["name"].startswith("MESH_") and e["t109"] == 0x0c]

# Also collect TX name hashes (DDS hashes from TX names)
tx_dds_hashes = {}
for e in entries:
    if e["name"].startswith("TX_"):
        m = re.search(r'([0-9A-Fa-f]{16})$', e["name"])
        if m:
            tx_dds_hashes[int(m.group(1), 16)] = e["name"]

# === Parse MESH data and search for embedded hashes ===
print("=== MESH data: searching for embedded material/texture hashes ===")

for me in mesh_entries[:5]:
    edata = data[me["fo"]:me["fo"]+me["size"]]
    print(f"\n{me['name']} size={me['size']} hash_field={me['hash']:#018x}")
    
    # Search for any 8-byte aligned values that match known hashes
    found_hashes = []
    for off in range(0, len(edata)-7, 4):
        v = struct.unpack_from("<Q", edata, off)[0]
        if v == 0: continue
        if v in mat_name_hashes:
            found_hashes.append((off, "MAT_NAME", mat_name_hashes[v]))
        elif v in mat_field_hashes:
            found_hashes.append((off, "MAT_FIELD", mat_field_hashes[v]))
        elif v in tx_dds_hashes:
            found_hashes.append((off, "TX_DDS", tx_dds_hashes[v]))
    
    if found_hashes:
        for off, typ, name in found_hashes:
            print(f"  @{off:#06x}: {typ} -> {name}")
    else:
        # Show all non-zero u64 values for inspection
        print(f"  No hash matches. Non-zero u64 values:")
        for off in range(0, min(len(edata), 256), 8):
            v = struct.unpack_from("<Q", edata, off)[0]
            if v != 0 and v != 0x3f80000000000000:  # skip 1.0f padding
                print(f"    @{off:#06x}: {v:#018x}")

# === Check if MAT reference entry (t109=00 after MESH) has data ===
print("\n\n=== MAT reference entries (t109=00, after MESH) ===")
for me in mesh_entries[:5]:
    # Find MAT ref after MESH
    for j in range(me["idx"]+1, min(me["idx"]+5, ec)):
        ne = entries[j]
        if ne["name"].startswith("MAT_") and ne["t109"] == 0x00:
            ref_data = data[ne["fo"]:ne["fo"]+min(ne["size"], 128)]
            print(f"\n  MESH:{me['name'][:30]} -> MAT_REF:{ne['name'][:30]} size={ne['size']}")
            for off in range(0, min(128, len(ref_data)), 16):
                hex_str = " ".join(f"{b:02x}" for b in ref_data[off:off+16])
                ascii_str = "".join(chr(b) if 32 <= b < 127 else "." for b in ref_data[off:off+16])
                print(f"    {off:04x}: {hex_str:<48} {ascii_str}")
            
            # Search for hashes in MAT ref data
            for off in range(0, len(ref_data)-7, 4):
                v = struct.unpack_from("<Q", ref_data, off)[0]
                if v in mat_name_hashes:
                    print(f"    *** MAT_NAME hash match @{off:#06x}: {mat_name_hashes[v]}")
                elif v in tx_dds_hashes:
                    print(f"    *** TX_DDS hash match @{off:#06x}: {tx_dds_hashes[v]}")
            break
        if ne["name"].startswith("MESH_") and ne["t109"] == 0x0c:
            break

# === Look at TX entries with word0=60 ===
print("\n\n=== TX entries with word0=60 ===")
for e in entries:
    if e["name"].startswith("TX_") and e["word0"] == 60:
        edata = data[e["fo"]:e["fo"]+min(e["size"], 128)]
        print(f"\n  {e['name'][:55]} size={e['size']} t109={e['t109']:02x} b111={e['b111']}")
        for off in range(0, min(128, len(edata)), 16):
            hex_str = " ".join(f"{b:02x}" for b in edata[off:off+16])
            ascii_str = "".join(chr(b) if 32 <= b < 127 else "." for b in edata[off:off+16])
            print(f"    {off:04x}: {hex_str:<48} {ascii_str}")
        if entries.index(e) > 20:
            print("  ... (showing first only)")
            break