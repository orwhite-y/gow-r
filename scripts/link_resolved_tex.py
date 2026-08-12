import json, os, time

MODELS_DIR = r"D:\God of War Ragnarok_extracted\models"

with open(r"E:\gow_re_workspace\output\tex_ref_resolution.json","r") as f:
    resolution = json.load(f)
with open(r"E:\gow_re_workspace\output\dds_index_complete.json","r") as f:
    dds_index = json.load(f)
with open(r"E:\gow_re_workspace\output\missing_tex_hashes.json","r") as f:
    missing = set(json.load(f))

# Verify resolution and count
resolved = 0
unresolved = set()
for mh in missing:
    if mh in resolution and resolution[mh] in dds_index:
        resolved += 1
    else:
        unresolved.add(mh)

print(f"Missing total: {len(missing)}")
print(f"Resolved (ref -> existing DDS): {resolved}")
print(f"Truly unresolved: {len(unresolved)}")

# For resolved textures, create hard links
# We need to link them in each WAD's textures dir that references them
# First, let's just save the resolution and handle linking in the main update script

# Check unresolved - are they in any texpack WAD as GNF data?
# The 666 failed DDS extractions might account for some
print(f"\nUnresolved hashes (first 20):")
for h in sorted(list(unresolved))[:20]:
    print(f"  {h}")

# Save final resolution
final_res = {k: v for k, v in resolution.items() if v in dds_index}
with open(r"E:\gow_re_workspace\output\tex_ref_final.json","w") as f:
    json.dump(final_res, f, indent=2)
print(f"\nFinal resolution map: {len(final_res)} entries saved")
print(f"Truly missing (no source): {len(missing) - len(final_res)}")