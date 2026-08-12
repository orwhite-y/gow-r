import json, os

# Load missing hashes
with open(r"E:\gow_re_workspace\output\missing_tex_hashes.json","r") as f:
    missing = json.load(f)

# Check the GNF source files - are the missing hashes present as .gnf files?
PC_LE = r"E:\God of War Ragnarok\exec\wad\pc_le"

# Build a set of all GNF file names (without extension) across all texpacks
# GNF files should be in texpack WADs
# Let's check the extracted textures directory for failed extractions
MODELS_DIR = r"D:\God of War Ragnarok_extracted\models"

# Check if there are .gnf files anywhere
gnf_files = set()
for root, dirs, files in os.walk(MODELS_DIR):
    for f in files:
        if f.lower().endswith(".gnf"):
            gnf_files.add(f[:-4].upper())

print(f"GNF files found in models dir: {len(gnf_files)}")

# Check if missing hashes have corresponding GNF files
matching_gnf = 0
for h in missing:
    if h in gnf_files:
        matching_gnf += 1
print(f"Missing hashes with GNF source: {matching_gnf}/{len(missing)}")

# Let's also check the texpack WADs for texture entries
# Texpacks are WADs that contain TX_ entries with word0=29 (texture data)
import lz4.frame, struct

def parse_wad_quick(wad_path):
    with open(wad_path, "rb") as f:
        data = lz4.frame.decompress(f.read())
    ec = struct.unpack_from("<I", data, 8)[0]
    entries = []
    for i in range(ec):
        o = 64 + 144 * i
        word0 = struct.unpack_from("<H", data, o)[0]
        name = data[o+24:o+104].split(b"\x00")[0].decode("ascii", errors="replace")
        entries.append({"word0": word0, "name": name})
    return entries

import re
# Find texpack WADs (they usually have "texpack" in the name or contain many TX_ entries)
wads = [f for f in os.listdir(PC_LE) if f.endswith(".wad")]
texpack_wads = [w for w in wads if "texpack" in w.lower() or "tex" in w.lower()]
print(f"\nTexpack-like WADs: {len(texpack_wads)}")
for tw in texpack_wads[:10]:
    print(f"  {tw}")

# Check all WADs for TX entries with missing hashes
missing_set = set(missing)
found_in_wad = {}
for wad_file in wads:
    try:
        entries = parse_wad_quick(os.path.join(PC_LE, wad_file))
        for e in entries:
            if e["name"].startswith("TX_"):
                m = re.search(r'([0-9A-Fa-f]{16})$', e["name"])
                if m:
                    h = m.group(1).upper()
                    if h in missing_set:
                        found_in_wad.setdefault(h, []).append(wad_file)
    except:
        pass

print(f"\nMissing hashes found in WAD TX entries: {len(found_in_wad)}/{len(missing)}")
for h, wads in list(found_in_wad.items())[:10]:
    print(f"  {h} -> {wads[0]}")