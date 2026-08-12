import struct, lz4.frame, os

PC_LE = r"E:\God of War Ragnarok\exec\wad\pc_le"
wad_name = "alf_bluff100_entrance.wad"

with open(os.path.join(PC_LE, wad_name), "rb") as f:
    data = lz4.frame.decompress(f.read())

ec = struct.unpack_from("<I", data, 8)[0]
ds = 64 + 144 * ec

# Fast offset calculation
offsets = []
cur = ds
for i in range(ec):
    o = 64 + 144 * i
    sz = struct.unpack_from("<I", data, o+4)[0]
    al = struct.unpack_from("<I", data, o+104)[0]
    if al > 0:
        cur = (cur + al - 1) & ~(al - 1)
    offsets.append(cur)
    cur += sz

# Look at t109=0x04 entries (the "0_0_1" type)
print("=== t109=0x04 entries (mesh-material bindings?) ===")
count = 0
for i in range(ec):
    o = 64 + 144 * i
    t109 = data[o+109]
    if t109 == 0x04:
        name = data[o+24:o+104].split(b"\x00")[0].decode("ascii", errors="replace")
        sz = struct.unpack_from("<I", data, o+4)[0]
        hash_val = struct.unpack_from("<Q", data, o+8)[0]
        fo = offsets[i]
        edata = data[fo:fo+min(sz, 128)]
        
        if count < 5:
            print(f"\n{name} hash={hash_val:#018x} size={sz}")
            for off in range(0, min(128, len(edata)), 16):
                hex_str = " ".join(f"{b:02x}" for b in edata[off:off+16])
                ascii_str = "".join(chr(b) if 32 <= b < 127 else "." for b in edata[off:off+16])
                print(f"  {off:04x}: {hex_str:<48} {ascii_str}")
        count += 1

print(f"\nTotal t109=0x04: {count}")

# Also look at MESH entry data more carefully - it might contain material references
print("\n\n=== MESH entry data (looking for material references) ===")
mesh_count = 0
for i in range(ec):
    o = 64 + 144 * i
    name = data[o+24:o+104].split(b"\x00")[0].decode("ascii", errors="replace")
    t109 = data[o+109]
    if name.startswith("MESH_") and t109 == 0x0c:
        sz = struct.unpack_from("<I", data, o+4)[0]
        hash_val = struct.unpack_from("<Q", data, o+8)[0]
        fo = offsets[i]
        edata = data[fo:fo+min(sz, 256)]
        
        if mesh_count < 3:
            print(f"\n{name} hash={hash_val:#018x} size={sz}")
            # The meshbuf starts with 0c 00 0a 00 (typeCode=0xa000c)
            # Look for any u64 values that look like MAT_ hashes
            print(f"  Raw hex (first 256 bytes):")
            for off in range(0, min(256, len(edata)), 16):
                hex_str = " ".join(f"{b:02x}" for b in edata[off:off+16])
                ascii_str = "".join(chr(b) if 32 <= b < 127 else "." for b in edata[off:off+16])
                print(f"  {off:04x}: {hex_str:<48} {ascii_str}")
            
            # Also check if any 8-byte values match known MAT_ entry hashes
            mat_hashes = set()
            for j in range(ec):
                oj = 64 + 144 * j
                nj = data[oj+24:oj+104].split(b"\x00")[0].decode("ascii", errors="replace")
                tj = data[oj+109]
                if nj.startswith("MAT_") and tj == 0x0a:
                    hj = struct.unpack_from("<Q", data, oj+8)[0]
                    mat_hashes.add(hj)
            
            for off in range(0, len(edata)-7, 4):
                v = struct.unpack_from("<Q", edata, off)[0]
                if v in mat_hashes:
                    print(f"  *** Found MAT hash match at offset {off}: {v:#018x}")
        mesh_count += 1
        if mesh_count > 3:
            break