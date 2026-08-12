import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r"E:\gow_re_workspace\output\model_texture_mapping.json","r") as f:
    data = json.load(f)

mapping = data["mapping"]
# Find WADs with valhalla in name
val_wads = {k: len(v) for k,v in mapping.items() if "valhalla" in k.lower() or "val_" in k.lower()}
print(f"Valhalla-related WADs in mapping: {len(val_wads)}")
for k, v in sorted(val_wads.items()):
    print(f"  {k}: {v} meshes")

# Check the wad_to_region function - what region do these map to?
def wad_to_region(wad_name):
    w = wad_name.lower()
    if w.startswith("alf"): return "alfheim"
    if w.startswith("asg"): return "asgard"
    if w.startswith("hel") or w.startswith("nif_hel"): return "helheim"
    if w.startswith("jot"): return "jotunheim"
    if w.startswith("mid"): return "midgard"
    if w.startswith("mus"): return "muspelheim"
    if w.startswith("nif"): return "niflheim"
    if w.startswith("sva"): return "svartalfheim"
    if w.startswith("van"): return "vanaheim"
    if w.startswith("r_") or w.startswith("ui"): return "base"
    if "cutscene" in w or "cs_" in w: return "cutscenes"
    if "atreus" in w or "companion" in w or "kratos" in w: return "characters"
    return "base"

print("\nRegion mapping for valhalla WADs:")
for k in sorted(val_wads.keys()):
    r = wad_to_region(k)
    print(f"  {k} -> {r}")