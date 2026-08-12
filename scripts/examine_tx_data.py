import struct, lz4.frame, os

PC_LE = r"E:\God of War Ragnarok\exec\wad\pc_le"

def parse_wad(wad_path):
    with open(wad_path, "rb") as f:
        data = lz4.frame.decompress(f.read())
    ec = struct.unpack_from("<I", data, 8)[0]
    ds = 64 + 144 * ec
    cur = ds
    entries = []
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
                         "name": name, "t109": t109, "b111": b111, "fo": fo, "align": align})
    return entries, data

# Use alf075_lights which has smaller MAT entries with visible floats
wad_path = os.path.join(PC_LE, "alf075_lights.wad")
entries, data = parse_wad(wad_path)

# Show the full entry list around a MAT+TX pair
for i, e in enumerate(entries):
    if e["name"].startswith("MAT_") and e["t109"] == 0x0a:
        print(f"\n{'='*70}")
        print(f"MAT entry: idx={e['idx']} name={e['name']} size={e['size']} word0={e['word0']} t109=0x{e['t109']:02x} b111={e['b111']}")
        edata = data[e["fo"]:e["fo"]+e["size"]]
        # Hex dump
        for off in range(0, min(len(edata), 400), 16):
            hex_str = " ".join(f"{b:02x}" for b in edata[off:off+16])
            ascii_str = "".join(chr(b) if 32<=b<127 else "." for b in edata[off:off+16])
            print(f"  {off:04x}: {hex_str:<48} {ascii_str}")
        
        # Show next entry (should be TX with word0=60)
        if i+1 < len(entries):
            ne = entries[i+1]
            print(f"\n  Next: idx={ne['idx']} name={ne['name']} word0={ne['word0']} t109=0x{ne['t109']:02x} size={ne['size']}")
            nedata = data[ne["fo"]:ne["fo"]+ne["size"]]
            for off in range(0, min(len(nedata), 256), 16):
                hex_str = " ".join(f"{b:02x}" for b in nedata[off:off+16])
                ascii_str = "".join(chr(b) if 32<=b<127 else "." for b in nedata[off:off+16])
                print(f"    {off:04x}: {hex_str:<48} {ascii_str}")
        
        if i > 70: break  # just show first few