import struct, lz4.frame, os

PC_LE = r"E:\God of War Ragnarok\exec\wad\pc_le"
wad_name = "alf_bluff100_entrance.wad"
wad_path = os.path.join(PC_LE, wad_name)

with open(wad_path, "rb") as f:
    data = lz4.frame.decompress(f.read())

ec = struct.unpack_from("<I", data, 8)[0]
ds = 64 + 144 * ec  # data section start

# Collect all entries
entries = []
for i in range(ec):
    o = 64 + 144 * i
    word0 = struct.unpack_from("<H", data, o)[0]
    flags = struct.unpack_from("<H", data, o+2)[0]
    size = struct.unpack_from("<I", data, o+4)[0]
    hash_val = struct.unpack_from("<Q", data, o+8)[0]
    name = data[o+24:o+104].split(b"\x00")[0].decode("ascii", errors="replace")
    t108 = data[o+108]
    t109 = data[o+109]
    b111 = data[o+111]
    align = struct.unpack_from("<I", data, o+104)[0]
    byte114 = struct.unpack_from("<H", data, o+114)[0]
    
    # Calculate file offset (batch simulation)
    file_off = ds
    for j in range(i):
        oj = 64 + 144 * j
        sj = struct.unpack_from("<I", data, oj+4)[0]
        aj = struct.unpack_from("<I", data, oj+104)[0]
        if aj > 0:
            file_off = (file_off + aj - 1) & ~(aj - 1)
        file_off += sj
    
    entries.append({
        "idx": i, "word0": word0, "flags": flags, "size": size,
        "hash": hash_val, "name": name, "t108": t108, "t109": t109,
        "b111": b111, "align": align, "byte114": byte114,
        "file_off": file_off
    })

# Find MESH entries and MAT entries
mesh_entries = [e for e in entries if e["name"].startswith("MESH_") and e["t109"] == 0x0c]
mat_entries = [e for e in entries if e["name"].startswith("MAT_") and e["t109"] == 0x0a]
tx_entries = [e for e in entries if e["name"].startswith("TX_")]

print(f"MESH entries: {len(mesh_entries)}")
print(f"MAT entries: {len(mat_entries)}")
print(f"TX entries: {len(tx_entries)}")

# Parse a MAT entry to see what it contains
print("\n=== Sample MAT entries (first 5) ===")
for me in mat_entries[:5]:
    mat_data = data[me["file_off"]:me["file_off"]+me["size"]]
    print(f"\nMAT: {me['name']} hash={me['hash']:#018x} size={me['size']}")
    print(f"  Raw hex (first 128 bytes):")
    for off in range(0, min(128, len(mat_data)), 16):
        hex_str = " ".join(f"{b:02x}" for b in mat_data[off:off+16])
        ascii_str = "".join(chr(b) if 32 <= b < 127 else "." for b in mat_data[off:off+16])
        print(f"  {off:04x}: {hex_str:<48} {ascii_str}")

# Parse TX entries - extract the hash from the name
print("\n=== Sample TX entries (first 10) ===")
for te in tx_entries[:10]:
    # TX name format: TX_texturename_HASHHEX
    # The hash at the end is the texture file hash (DDS filename)
    name = te["name"]
    # Extract hash from name (last 16 hex chars before any extension)
    parts = name.split("_")
    hash_part = parts[-1] if len(parts[-1]) >= 16 else ""
    print(f"  {name[:60]:<60} b111={te['b111']} hash_field={te['hash']:#018x} size={te['size']}")