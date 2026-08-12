import json, os, time

# Load mappings and DDS index
with open(r"E:\gow_re_workspace\output\model_texture_mapping.json","r") as f:
    mapping_data = json.load(f)
with open(r"E:\gow_re_workspace\output\dds_index_complete.json","r") as f:
    dds_index = json.load(f)

mapping = mapping_data["mapping"]

# Collect all unique texture hashes referenced in mapping
all_tex_hashes = set()
for wad, meshes in mapping.items():
    for m in meshes:
        for t in m.get("textures", []):
            h = t.get("hash","").upper()
            if h: all_tex_hashes.add(h)

print(f"Total unique texture hashes referenced: {len(all_tex_hashes)}")
print(f"Total unique DDS files available: {len(dds_index)}")

# Find which are missing
missing = set()
found = set()
for h in all_tex_hashes:
    if h in dds_index:
        found.add(h)
    else:
        missing.add(h)

print(f"Found in index: {len(found)}")
print(f"Missing from index: {len(missing)}")

# Show some missing hashes
missing_list = sorted(list(missing))[:20]
print(f"\nSample missing hashes:")
for h in missing_list:
    print(f"  {h}")

# Check if missing hashes might be lowercase/uppercase mismatch
if missing_list:
    lower_index = {k.lower(): v for k, v in dds_index.items()}
    case_fixed = 0
    for h in missing:
        if h.lower() in lower_index:
            case_fixed += 1
    print(f"\nCase-insensitive matches: {case_fixed}")

# Save missing hashes for later analysis
with open(r"E:\gow_re_workspace\output\missing_tex_hashes.json","w") as f:
    json.dump(sorted(list(missing)), f)
print(f"\nMissing hashes saved to missing_tex_hashes.json")