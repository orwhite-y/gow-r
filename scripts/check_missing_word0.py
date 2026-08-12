import lz4.frame, struct, os, re, json

PC_LE = r"E:\God of War Ragnarok\exec\wad\pc_le"

with open(r"E:\gow_re_workspace\output\missing_tex_hashes.json","r") as f:
    missing = set(json.load(f))

# Parse WAD and find TX entries with missing hashes, check their word0 and data
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
                         "name": name, "t109": t109, "b111": b111, "fo": fo})
    return entries, data

# Check add_atreusplayable00.wad
wad_file = "add_atreusplayable00.wad"
entries, data = parse_wad(os.path.join(PC_LE, wad_file))

# Find TX entries with missing hashes
tx_missing = []
for e in entries:
    if e["name"].startswith("TX_"):
        m = re.search(r'([0-9A-Fa-f]{16})$', e["name"])
        if m and m.group(1).upper() in missing:
            tx_missing.append(e)

print(f"{wad_file}: {len(tx_missing)} TX entries with missing hashes")
word0_dist = {}
for e in tx_missing:
    word0_dist[e["word0"]] = word0_dist.get(e["word0"], 0) + 1
print(f"word0 distribution: {word0_dist}")

# Show samples
for e in tx_missing[:5]:
    edata = data[e["fo"]:e["fo"]+min(64, e["size"])]
    print(f"\n  name={e['name']} word0={e['word0']} t109=0x{e['t109']:02x} size={e['size']}")
    hex_str = " ".join(f"{b:02x}" for b in edata[:32])
    print(f"  hex: {hex_str}")
    # Check if it starts with GNF magic
    if len(edata) >= 4:
        magic = struct.unpack_from("<I", edata, 0)[0]
        print(f"  magic: 0x{magic:08x} ({'GNF' if magic == 0x20466E47 else 'not GNF'})")

# Also check which WADs contain the most missing hashes
wad_missing_count = {}
for wf in os.listdir(PC_LE):
    if not wf.endswith(".wad"): continue
    try:
        entries, _ = parse_wad(os.path.join(PC_LE, wf))
        cnt = 0
        for e in entries:
            if e["name"].startswith("TX_"):
                m = re.search(r'([0-9A-Fa-f]{16})$', e["name"])
                if m and m.group(1).upper() in missing:
                    cnt += 1
        if cnt > 0:
            wad_missing_count[wf] = cnt
    except:
        pass

print(f"\nWADs containing missing texture hashes: {len(wad_missing_count)}")
for w, c in sorted(wad_missing_count.items(), key=lambda x: -x[1])[:15]:
    print(f"  {w}: {c}")