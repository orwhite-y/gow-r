import os, subprocess, sys, time, shutil

MODELS_DIR = r"D:\God of War Ragnarok_extracted\models"
ARCHIVE_DIR = r"F:\gow_archives"
SEVEN_ZIP = r"F:\soft\7-Zip\7z.exe"
RELINK_SCRIPT = r"E:\gow_re_workspace\scripts\relink_textures.py"

os.makedirs(ARCHIVE_DIR, exist_ok=True)

# Copy relink script
shutil.copy2(RELINK_SCRIPT, os.path.join(ARCHIVE_DIR, "relink_textures.py"))

# === Phase 1: Per-region archives (GLB + MAT + TX + JSON, NO DDS) ===
print("=" * 60, flush=True)
print("PHASE 1: Per-region archives (no DDS)", flush=True)
print("=" * 60, flush=True)

regions = sorted([d for d in os.listdir(MODELS_DIR) 
                  if os.path.isdir(os.path.join(MODELS_DIR, d)) and d != "_unique_textures"])

for region in regions:
    src = os.path.join(MODELS_DIR, region)
    dst = os.path.join(ARCHIVE_DIR, f"{region}.7z")
    
    if os.path.exists(dst):
        print(f"[SKIP] {region}.7z already exists", flush=True)
        continue
    
    print(f"[COMPRESS] {region} ...", flush=True)
    t0 = time.time()
    
    # Use -x!textures to exclude ALL textures directories (both region-level and per-WAD)
    cmd = [SEVEN_ZIP, "a", "-t7z", "-mx=5", "-mmt=8", dst, 
           os.path.join(src, "*"), "-x!textures"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    elapsed = time.time() - t0
    if os.path.exists(dst):
        size_mb = os.path.getsize(dst) / 1e6
        print(f"  Done: {size_mb:.0f} MB in {elapsed:.0f}s", flush=True)
    else:
        print(f"  FAILED: {result.stderr[:200]}", flush=True)

# === Phase 2: Split unique DDS by hash prefix and compress ===
print("\n" + "=" * 60, flush=True)
print("PHASE 2: Texture archives (unique DDS, split by hash)", flush=True)
print("=" * 60, flush=True)

unique_tex_dir = os.path.join(MODELS_DIR, "_unique_textures")
if not os.path.isdir(unique_tex_dir):
    print("ERROR: _unique_textures dir not found!", flush=True)
    sys.exit(1)

# Split into 4 groups by first hex char
groups = {"0-3": [], "4-7": [], "8-b": [], "c-f": []}
for f in os.listdir(unique_tex_dir):
    if f.endswith('.dds'):
        h = f[0].lower()
        if h in '0123': groups["0-3"].append(f)
        elif h in '4567': groups["4-7"].append(f)
        elif h in '89ab': groups["8-b"].append(f)
        elif h in 'cdef': groups["c-f"].append(f)

for group_name, files in groups.items():
    print(f"\n[TEX] Group {group_name}: {len(files)} files", flush=True)
    dst = os.path.join(ARCHIVE_DIR, f"textures_{group_name}.7z")
    
    if os.path.exists(dst):
        print(f"  SKIP: already exists", flush=True)
        continue
    
    # Create staging dir with hard links
    stage = os.path.join(MODELS_DIR, f"_tex_{group_name}")
    os.makedirs(stage, exist_ok=True)
    
    linked = 0
    for f in files:
        src = os.path.join(unique_tex_dir, f)
        dst_link = os.path.join(stage, f)
        if not os.path.exists(dst_link):
            try:
                os.link(src, dst_link)
                linked += 1
            except:
                pass
    
    print(f"  Staged {linked} files, compressing...", flush=True)
    t0 = time.time()
    cmd = [SEVEN_ZIP, "a", "-t7z", "-mx=3", "-mmt=8", dst, os.path.join(stage, "*")]
    result = subprocess.run(cmd, capture_output=True, text=True)
    elapsed = time.time() - t0
    
    if os.path.exists(dst):
        size_mb = os.path.getsize(dst) / 1e6
        print(f"  Done: {size_mb:.0f} MB in {elapsed:.0f}s", flush=True)
    else:
        print(f"  FAILED: {result.stderr[:200]}", flush=True)
    
    # Clean up staging dir (remove hard links, they don't use extra space)
    for f in os.listdir(stage):
        try:
            os.remove(os.path.join(stage, f))
        except:
            pass
    try:
        os.rmdir(stage)
    except:
        pass

# === Summary ===
print("\n" + "=" * 60, flush=True)
print("SUMMARY", flush=True)
print("=" * 60, flush=True)
total_size = 0
for f in sorted(os.listdir(ARCHIVE_DIR)):
    fp = os.path.join(ARCHIVE_DIR, f)
    if os.path.isfile(fp):
        s = os.path.getsize(fp)
        total_size += s
        print(f"  {f:40s}: {s/1e6:.0f} MB")
print(f"\n  TOTAL: {total_size/1e9:.2f} GB")
print(f"\n  Extract instructions:")
print(f"  1. Extract all region .7z files into a 'models' directory")
print(f"  2. Extract all textures_*.7z files into a 'textures' directory")
print(f"  3. Run: python relink_textures.py models textures")