import os, json

MODELS_DIR = r"D:\God of War Ragnarok_extracted\models"

# === 1. Collect all unique DDS files globally ===
print("=== Collecting unique DDS files globally ===", flush=True)
unique_dds = {}  # hash -> first path found
duplicate_dds = 0

for region in sorted(os.listdir(MODELS_DIR)):
    rpath = os.path.join(MODELS_DIR, region)
    if not os.path.isdir(rpath):
        continue
    for root, dirs, files in os.walk(rpath):
        for f in files:
            if f.endswith('.dds'):
                h = f[:-4]
                fp = os.path.join(root, f)
                if h not in unique_dds:
                    unique_dds[h] = fp
                else:
                    duplicate_dds += 1

total_unique_dds_size = sum(os.path.getsize(v) for v in unique_dds.values())
print(f"Unique DDS: {len(unique_dds)} files, {total_unique_dds_size/1e9:.2f}GB")
print(f"Duplicate DDS (hard-linked copies): {duplicate_dds}")

# === 2. Calculate per-region GLB+MAT+TX+JSON sizes ===
print("\n=== Per-region GLB+MAT+TX+JSON sizes ===", flush=True)
total_glb = 0
total_mat = 0

for region in sorted(os.listdir(MODELS_DIR)):
    rpath = os.path.join(MODELS_DIR, region)
    if not os.path.isdir(rpath):
        continue
    
    glb_size = 0
    mat_size = 0
    glb_count = 0
    
    for wad in os.listdir(rpath):
        wpath = os.path.join(rpath, wad)
        if not os.path.isdir(wpath):
            continue
        if wad == "textures":
            continue
        for f in os.listdir(wpath):
            fp = os.path.join(wpath, f)
            if os.path.isfile(fp):
                try:
                    s = os.path.getsize(fp)
                    if f.endswith('.glb'):
                        glb_size += s
                        glb_count += 1
                    elif f.endswith('.mat') or f.endswith('.tx') or f.endswith('.json'):
                        mat_size += s
                except:
                    pass
    
    total_glb += glb_size
    total_mat += mat_size
    print(f"  {region:20s}: {glb_count:6d} GLB ({glb_size/1e9:.2f}GB) + MAT/TX/JSON ({mat_size/1e6:.0f}MB)")

print(f"\n  {'TOTAL GLB':20s}: {total_glb/1e9:.2f}GB")
print(f"  {'TOTAL MAT/TX/JSON':20s}: {total_mat/1e9:.2f}GB")
print(f"  {'TOTAL UNIQUE DDS':20s}: {total_unique_dds_size/1e9:.2f}GB")
print(f"  {'GRAND TOTAL':20s}: {(total_glb + total_mat + total_unique_dds_size)/1e9:.2f}GB")
print(f"\n  vs 360.74GB with all hard-linked copies")
print(f"  Savings: {360.74 - (total_glb + total_mat + total_unique_dds_size)/1e9:.2f}GB")