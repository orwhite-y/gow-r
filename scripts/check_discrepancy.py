import json, os

MODELS_DIR = r"D:\God of War Ragnarok_extracted\models"

# Load global mapping to see which WADs it covers
with open(r"E:\gow_re_workspace\output\model_texture_mapping.json","r") as f:
    data = json.load(f)
global_wads = set(data["mapping"].keys())
print(f"Global mapping WADs: {len(global_wads)}")
print(f"Global mapping total meshes: {data['stats']['total_meshes']}")

# Count meshes in material_mapping.json files that are NOT in global mapping
extra_meshes = 0
extra_files = 0
for root, dirs, files in os.walk(MODELS_DIR):
    for f in files:
        if f == "material_mapping.json":
            map_path = os.path.join(root, f)
            try:
                with open(map_path, "r") as fh:
                    mdata = json.load(fh)
                wad = mdata.get("wad", "")
                mesh_count = len(mdata.get("meshes", []))
                if wad not in global_wads:
                    extra_meshes += mesh_count
                    extra_files += 1
            except:
                pass

print(f"\nExtra mapping files (not in global mapping): {extra_files}")
print(f"Extra meshes: {extra_meshes}")
print(f"Global meshes: {data['stats']['total_meshes']}")
print(f"Total (global + extra): {data['stats']['total_meshes'] + extra_meshes}")