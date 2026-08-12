import os

models_dir = r"D:\God of War Ragnarok_extracted\models"
regions = sorted(os.listdir(models_dir))
total_all = 0
print("=== Final GLB count per region ===")
for r in regions:
    rpath = os.path.join(models_dir, r)
    if not os.path.isdir(rpath):
        continue
    glb_count = 0
    for root, dirs, files in os.walk(rpath):
        for f in files:
            if f.endswith('.glb'):
                glb_count += 1
    total_all += glb_count
    print(f"  {r}: {glb_count} GLB")
print(f"  ----------")
print(f"  TOTAL: {total_all} GLB")

# Check valhalla materials
print("\n=== Valhalla materials check (sample 3) ===")
val_dir = os.path.join(models_dir, "valhalla")
val_dirs = sorted([d for d in os.listdir(val_dir) if d.startswith("val_") and os.path.isdir(os.path.join(val_dir, d))])
for d in val_dirs[:3]:
    dpath = os.path.join(val_dir, d)
    glb = len([f for f in os.listdir(dpath) if f.endswith('.glb')])
    mat_dir = os.path.join(dpath, "materials")
    mat_count = len(os.listdir(mat_dir)) if os.path.isdir(mat_dir) else 0
    has_mi = os.path.isfile(os.path.join(dpath, "mat_index.json"))
    has_map = os.path.isfile(os.path.join(dpath, "material_mapping.json"))
    print(f"  {d}: {glb} GLB, {mat_count} mat files, mat_index={has_mi}, mapping={has_map}")

# Check base has no val_* dirs left
base_dir = os.path.join(models_dir, "base")
base_val = [d for d in os.listdir(base_dir) if d.startswith("val_") and os.path.isdir(os.path.join(base_dir, d))] if os.path.isdir(base_dir) else []
print(f"\nRemaining val_* dirs in base: {len(base_val)}")

# Check vanaheim has no val_* dirs left
van_dir = os.path.join(models_dir, "vanaheim")
van_val = [d for d in os.listdir(van_dir) if d.startswith("val_") and os.path.isdir(os.path.join(van_dir, d))] if os.path.isdir(van_dir) else []
print(f"Remaining val_* dirs in vanaheim: {len(van_val)}")