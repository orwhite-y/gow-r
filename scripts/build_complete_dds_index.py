import os, json, time

MODELS_DIR = r"D:\God of War Ragnarok_extracted\models"
OUT_DIR = r"E:\gow_re_workspace\output"

# Build complete DDS index from ALL DDS files under models dir
print("Building complete DDS index from all DDS files...")
t0 = time.time()

dds_index = {}  # hash_hex -> [list of paths]
dds_count = 0

for root, dirs, files in os.walk(MODELS_DIR):
    for f in files:
        if f.lower().endswith(".dds"):
            # Extract hash from filename (format: HASH.dds)
            name = f[:-4]  # remove .dds
            if len(name) == 16 and all(c in "0123456789ABCDEFabcdef" for c in name):
                h = name.upper()
                if h not in dds_index:
                    dds_index[h] = []
                dds_index[h].append(os.path.join(root, f))
                dds_count += 1

elapsed = time.time() - t0
print(f"Indexed {dds_count} DDS files in {elapsed:.1f}s")
print(f"Unique hashes: {len(dds_index)}")

# Save updated DDS index
with open(os.path.join(OUT_DIR, "dds_index_complete.json"), "w") as f:
    json.dump(dds_index, f)
print(f"Saved to dds_index_complete.json")

# Check which hashes have multiple locations (cross-region)
multi = {h: paths for h, paths in dds_index.items() if len(paths) > 1}
print(f"Hashes with multiple locations: {len(multi)}")