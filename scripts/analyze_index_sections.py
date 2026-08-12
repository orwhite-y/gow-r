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

# === Examine index section entries (TXRX_, MATX_, MDLX_) ===
print("=== Index section entries ===")
for e in entries[:30]:
    if e["size"] > 0 and any(e["name"].startswith(p) for p in ["TXRX_", "MATX_", "MDLX_", "LGTX_", "CXT_"]):
        edata = data[e["fo"]:e["fo"]+min(e["size"], 256)]
        print(f"\n{e['name']} idx={e['idx']} word0={e['word0']} t109={e['t109']:02x} size={e['size']}")
        for off in range(0, min(256, len(edata)), 16):
            hex_str = " ".join(f"{b:02x}" for b in edata[off:off+16])
            ascii_str = "".join(chr(b) if 32 <= b < 127 else "." for b in edata[off:off+16])
            print(f"  {off:04x}: {hex_str:<48} {ascii_str}")

# === Examine TX entry data (not just name) ===
print("\n\n=== TX entry data (first 5) ===")
tx_entries = [e for e in entries if e["name"].startswith("TX_") and e["size"] > 0]
for te in tx_entries[:5]:
    edata = data[te["fo"]:te["fo"]+min(te["size"], 128)]
    print(f"\n{te['name'][:60]} size={te['size']} t109={te['t109']:02x} b111={te['b111']}")
    for off in range(0, min(128, len(edata)), 16):
        hex_str = " ".join(f"{b:02x}" for b in edata[off:off+16])
        ascii_str = "".join(chr(b) if 32 <= b < 127 else "." for b in edata[off:off+16])
        print(f"  {off:04x}: {hex_str:<48} {ascii_str}")

# === Look at MESH entry data in detail ===
print("\n\n=== MESH entry data (first 3) ===")
mesh_entries = [e for e in entries if e["name"].startswith("MESH_") and e["t109"] == 0x0c]
for me in mesh_entries[:3]:
    edata = data[me["fo"]:me["fo"]+min(me["size"], 256)]
    print(f"\n{me['name'][:60]} size={me['size']} hash={me['hash']:#018x}")
    # Parse meshbuf header
    if len(edata) >= 4:
        type_code = struct.unpack_from("<I", edata, 0)[0]
        print(f"  typeCode={type_code:#010x}")
    for off in range(0, min(256, len(edata)), 16):
        hex_str = " ".join(f"{b:02x}" for b in edata[off:off+16])
        ascii_str = "".join(chr(b) if 32 <= b < 127 else "." for b in edata[off:off+16])
        print(f"  {off:04x}: {hex_str:<48} {ascii_str}")

# === Check naming patterns between MESH and MAT ===
print("\n\n=== Name pattern analysis ===")
mesh_names = set()
for me in mesh_entries:
    # Extract mesh name without MESH_ prefix
    mesh_names.add(me["name"][5:])

mat_names = set()
mat_entries = [e for e in entries if e["name"].startswith("MAT_")]
for me in mat_entries:
    mat_names.add(me["name"])

# Check if any MESH name substrings appear in MAT names or vice versa
print(f"MESH entries: {len(mesh_entries)}")
print(f"MAT entries: {len(mat_entries)}")

# Show some MESH names
print("\nSample MESH names:")
for me in mesh_entries[:10]:
    print(f"  {me['name']}")

# Show some MAT names
print("\nSample MAT names:")
for me in mat_entries[:10]:
    print(f"  {me['name']}")

# === Look for MAT entries that appear between MESH entries ===
print("\n\n=== Entry interleaving (MESH/MAT/TX around first MESH) ===")
first_mesh_idx = None
for i, e in enumerate(entries):
    if e["name"].startswith("MESH_"):
        first_mesh_idx = i
        break

if first_mesh_idx:
    start = max(0, first_mesh_idx - 5)
    end = min(ec, first_mesh_idx + 20)
    for i in range(start, end):
        e = entries[i]
        etype = "MESH" if e["name"].startswith("MESH_") else \
                "MAT" if e["name"].startswith("MAT_") else \
                "TX" if e["name"].startswith("TX_") else \
                "MG" if e["name"].startswith("MG_") else f"w{e['word0']}"
        print(f"  [{i:5d}] {etype:<6} t109={e['t109']:02x} b111={e['b111']} {e['name'][:55]}")