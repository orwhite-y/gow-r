import struct, lz4.frame, os, re, sys

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

# Examine a few WADs
for twad in ["midgard_zoo.wad", "alf075_lights.wad"]:
    wad_path = os.path.join(PC_LE, twad)
    if not os.path.exists(wad_path): continue
    entries, data = parse_wad(wad_path)
    
    mat_entries = [e for e in entries if e["name"].startswith("MAT_") and e["t109"] == 0x0a]
    print(f"\n{'='*60}")
    print(f"=== {twad}: {len(mat_entries)} MAT defs (t109=0x0a) ===")
    print(f"{'='*60}")
    for me in mat_entries[:3]:
        print(f"\n--- MAT idx={me['idx']} name={me['name']} size={me['size']} word0={me['word0']} b111={me['b111']} ---")
        edata = data[me["fo"]:me["fo"]+me["size"]]
        print(f"  Data length: {len(edata)}")
        # Hex dump first 512 bytes
        for off in range(0, min(512, len(edata)), 16):
            hex_str = " ".join(f"{b:02x}" for b in edata[off:off+16])
            ascii_str = "".join(chr(b) if 32<=b<127 else "." for b in edata[off:off+16])
            print(f"    {off:04x}: {hex_str:<48} {ascii_str}")
        # As floats
        print(f"  As floats (first 64):")
        floats = []
        for off in range(0, min(256, len(edata)-3), 4):
            f = struct.unpack_from("<f", edata, off)[0]
            if abs(f) < 1e10 and abs(f) > 1e-10 or f == 0.0:
                floats.append(f"{f:.4f}")
            else:
                floats.append(f"{f:.2e}")
        for i in range(0, len(floats), 8):
            print(f"    [{i:3d}] " + ", ".join(floats[i:i+8]))
        # Show entry after this MAT (TX entry?)
        if me["idx"]+1 < len(entries):
            ne = entries[me["idx"]+1]
            print(f"  Next entry: idx={ne['idx']} name={ne['name']} word0={ne['word0']} t109={ne['t109']} size={ne['size']}")