import os, json

MODELS_DIR = r"D:\God of War Ragnarok_extracted\models"

print("=== POST-MERGE AUDIT ===", flush=True)
total_glb = 0
total_dirs = 0
dirs_no_glb = 0

for region in sorted(os.listdir(MODELS_DIR)):
    rpath = os.path.join(MODELS_DIR, region)
    if not os.path.isdir(rpath) or region.startswith("_"):
        continue
    
    glb_count = 0
    wad_count = 0
    no_glb_dirs = []
    
    for wad in os.listdir(rpath):
        wpath = os.path.join(rpath, wad)
        if not os.path.isdir(wpath) or wad == "textures":
            continue
        wad_count += 1
        glbs = [f for f in os.listdir(wpath) if f.endswith(".glb")]
        glb_count += len(glbs)
        if not glbs:
            no_glb_dirs.append(wad)
    
    total_glb += glb_count
    total_dirs += wad_count
    dirs_no_glb += len(no_glb_dirs)
    
    status = "OK" if not no_glb_dirs else f"{len(no_glb_dirs)} dirs without GLB"
    print(f"  {region:20s}: {wad_count:4d} dirs, {glb_count:6d} GLB  [{status}]")
    if no_glb_dirs and len(no_glb_dirs) <= 5:
        for d in no_glb_dirs:
            print(f"    - {d}")

print(f"\n  TOTAL: {total_dirs} dirs, {total_glb} GLB, {dirs_no_glb} dirs without GLB")

# Check MAT coverage for merged dirs
print("\n=== MAT coverage check (sample) ===", flush=True)
for wad in ["c_190_ironwoodarrival", "r_kratos00", "r_thor00"]:
    for region in ["cutscenes", "characters"]:
        wpath = os.path.join(MODELS_DIR, region, wad)
        if os.path.isdir(wpath):
            mat_dir = os.path.join(wpath, "materials")
            mc = len(os.listdir(mat_dir)) if os.path.isdir(mat_dir) else 0
            gc = len([f for f in os.listdir(wpath) if f.endswith(".glb")])
            print(f"  {region}/{wad}: {gc} GLB, {mc} mat files")
            break