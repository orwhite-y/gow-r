import lz4.frame, struct, os, re, json

PC_LE = r"E:\God of War Ragnarok\exec\wad\pc_le"
GNF_MAGIC = b"GNF "

with open(r"E:\gow_re_workspace\output\missing_tex_hashes.json","r") as f:
    missing = set(json.load(f))

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
        name = data[o+24:o+104].split(b"\x00")[0].decode("ascii", errors="replace")
        t109 = data[o+109]
        b111 = data[o+111]
        align = struct.unpack_from("<I", data, o+104)[0]
        fo = cur
        if align > 0: fo = (fo + align - 1) & ~(align - 1)
        cur = fo + size
        entries.append({"idx": i, "word0": word0, "size": size,
                         "name": name, "t109": t109, "b111": b111, "fo": fo})
    return entries, data

# Find several GNF textures with different sizes and examine their headers
wad_file = "van_vanvil130_eastmiddlebank.wad"  # has 443 missing
entries, data = parse_wad(os.path.join(PC_LE, wad_file))

gnf_samples = []
for e in entries:
    if e["name"].startswith("TX_") and e["word0"] == 29:
        m = re.search(r'([0-9A-Fa-f]{16})$', e["name"])
        if m and m.group(1).upper() in missing:
            edata = data[e["fo"]:e["fo"]+e["size"]]
            gnf_off = edata.find(GNF_MAGIC)
            if gnf_off >= 0:
                gnf_samples.append((e, edata, gnf_off))
                if len(gnf_samples) >= 3: break

for e, edata, gnf_off in gnf_samples:
    gnf = edata[gnf_off:]
    print(f"\n{'='*60}")
    print(f"name={e['name']}")
    print(f"TX entry size={e['size']} b111={e['b111']} t109=0x{e['t109']:02x}")
    print(f"GNF offset in TX data: {gnf_off}")
    print(f"GNF blob size: {len(gnf)}")
    
    # Parse GNF header
    magic = struct.unpack_from("<I", gnf, 0)[0]
    img_offset = struct.unpack_from("<I", gnf, 4)[0]
    fmt_field = struct.unpack_from("<I", gnf, 20)[0]
    dim_field = struct.unpack_from("<I", gnf, 24)[0]
    mip_field = struct.unpack_from("<I", gnf, 28)[0]
    dp_field = struct.unpack_from("<I", gnf, 32)[0]
    data_size = struct.unpack_from("<I", gnf, 44)[0]
    
    fmt = (fmt_field >> 20) & 0x3F
    width = (dim_field & 0x3FFF) + 1
    height = ((dim_field >> 14) & 0x3FFF) + 1
    mips = ((mip_field >> 16) & 0xF) + 1
    depth = (dp_field & 0x1FFF) + 1
    
    print(f"magic=0x{magic:08x} imgOffset=0x{img_offset:x}")
    print(f"fmt=0x{fmt:02x} W={width} H={height} mips={mips} depth={depth} dataSize={data_size}")
    
    # Check if imgOffset is within bounds
    if img_offset < len(gnf):
        print(f"Image data starts at {img_offset}, available: {len(gnf) - img_offset} bytes")
        # Check data at imgOffset
        img_data = gnf[img_offset:]
        print(f"First 32 bytes of image data: {' '.join(f'{b:02x}' for b in img_data[:32])}")
    else:
        print(f"WARNING: imgOffset {img_offset} > GNF blob size {len(gnf)}")
        # The image data might start right after the actual header, not at imgOffset
        # Let's check if data_size makes sense
        print(f"data_size field: {data_size}")
        # Check what's at offset 0x100 (256) - typical GNF header end for small textures
        if len(gnf) > 0x100:
            print(f"Data at 0x100: {' '.join(f'{b:02x}' for b in gnf[0x100:0x120])}")
    
    # Dump first 256 bytes of GNF header
    print(f"\nGNF header hex dump (first 256 bytes):")
    for off in range(0, min(256, len(gnf)), 16):
        hex_str = " ".join(f"{b:02x}" for b in gnf[off:off+16])
        ascii_str = "".join(chr(b) if 32<=b<127 else "." for b in gnf[off:off+16])
        print(f"  {off:04x}: {hex_str:<48} {ascii_str}")