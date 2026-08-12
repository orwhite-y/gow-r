import lz4.frame, struct, os, re, json

PC_LE = r"E:\God of War Ragnarok\exec\wad\pc_le"

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

GNF_MAGIC = b"GNF "

# Check a few word0=29 entries for GNF data location
wad_file = "add_atreusplayable00.wad"
entries, data = parse_wad(os.path.join(PC_LE, wad_file))

print(f"=== {wad_file} - word0=29 TX entries with missing hashes ===")
for e in entries:
    if e["name"].startswith("TX_") and e["word0"] == 29:
        m = re.search(r'([0-9A-Fa-f]{16})$', e["name"])
        if m and m.group(1).upper() in missing:
            edata = data[e["fo"]:e["fo"]+e["size"]]
            gnf_off = edata.find(GNF_MAGIC)
            print(f"\n  name={e['name']}")
            print(f"  size={e['size']} t109=0x{e['t109']:02x} b111={e['b111']}")
            print(f"  GNF offset: {gnf_off}")
            if gnf_off >= 0:
                # Check GNF header
                gnf_data = edata[gnf_off:]
                print(f"  GNF data size: {len(gnf_data)}")
                # Parse GNF header
                if len(gnf_data) >= 0x20:
                    magic = struct.unpack_from("<I", gnf_data, 0)[0]
                    img_offset = struct.unpack_from("<I", gnf_data, 4)[0]
                    print(f"  magic=0x{magic:08x} imgOffset=0x{img_offset:x}")
                    # Check format fields
                    fmt_field = struct.unpack_from("<I", gnf_data, 0x14)[0] if len(gnf_data) > 0x18 else 0
                    dim_field = struct.unpack_from("<I", gnf_data, 0x18)[0] if len(gnf_data) > 0x1c else 0
                    print(f"  fmtField=0x{fmt_field:08x} dimField=0x{dim_field:08x}")
            else:
                print(f"  No GNF magic found. First 32 bytes:")
                print(f"  {' '.join(f'{b:02x}' for b in edata[:32])}")

# Now check across all WADs - how many word0=29 entries with missing hashes have GNF data?
print(f"\n\n=== Scanning all WADs for extractable GNF textures ===")
extractable = 0
not_extractable = 0
gnf_offsets = {}

wads = [f for f in os.listdir(PC_LE) if f.endswith(".wad")]
for wf in wads:
    try:
        entries, data = parse_wad(os.path.join(PC_LE, wf))
        for e in entries:
            if e["name"].startswith("TX_") and e["word0"] == 29:
                m = re.search(r'([0-9A-Fa-f]{16})$', e["name"])
                if m and m.group(1).upper() in missing:
                    edata = data[e["fo"]:e["fo"]+e["size"]]
                    gnf_off = edata.find(GNF_MAGIC)
                    if gnf_off >= 0:
                        extractable += 1
                        gnf_offsets.setdefault(gnf_off, 0)
                        gnf_offsets[gnf_off] += 1
                    else:
                        not_extractable += 1
    except:
        pass

print(f"Extractable (has GNF magic): {extractable}")
print(f"Not extractable (no GNF magic): {not_extractable}")
print(f"GNF offset distribution: {gnf_offsets}")