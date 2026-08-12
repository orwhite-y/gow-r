import os, subprocess, time, sys

MODELS_DIR = r"D:\God of War Ragnarok_extracted\models"
ARCHIVE_DIR = r"F:\gow_archives"
SEVEN_ZIP = r"F:\soft\7-Zip\7z.exe"

os.makedirs(ARCHIVE_DIR, exist_ok=True)

# Regions sorted by size (smallest first)
regions_info = []
for region in os.listdir(MODELS_DIR):
    rpath = os.path.join(MODELS_DIR, region)
    if not os.path.isdir(rpath) or region.startswith("_"):
        continue
    total = 0
    for root, dirs, files in os.walk(rpath):
        for f in files:
            try: total += os.path.getsize(os.path.join(root, f))
            except: pass
    regions_info.append((region, total))

regions_info.sort(key=lambda x: x[1])

print(f"=== Compressing {len(regions_info)} regions ===", flush=True)
grand_start = time.time()
total_archive_size = 0

for idx, (region, est_size) in enumerate(regions_info):
    rpath = os.path.join(MODELS_DIR, region)
    archive_path = os.path.join(ARCHIVE_DIR, f"{region}.7z")
    
    if os.path.exists(archive_path):
        sz = os.path.getsize(archive_path)
        total_archive_size += sz
        print(f"[{idx+1}/{len(regions_info)}] SKIP {region} ({sz/1e9:.2f}GB exists)", flush=True)
        continue
    
    print(f"[{idx+1}/{len(regions_info)}] {region} ({est_size/1e9:.1f}GB)...", flush=True)
    t0 = time.time()
    
    # Simple: archive entire region dir. 7z preserves structure, converts hardlinks to regular files.
    cmd = [SEVEN_ZIP, "a", "-t7z", "-mx=3", "-mmt=8", archive_path, os.path.join(rpath, "*")]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
        elapsed = time.time() - t0
        
        if os.path.exists(archive_path):
            sz = os.path.getsize(archive_path)
            total_archive_size += sz
            print(f"  OK: {sz/1e9:.2f}GB in {elapsed/60:.1f}min", flush=True)
        else:
            print(f"  FAILED: {result.stderr[:200]}", flush=True)
    except subprocess.TimeoutExpired:
        print(f"  TIMEOUT after 2h!", flush=True)
    except Exception as e:
        print(f"  ERROR: {e}", flush=True)

total_elapsed = time.time() - grand_start
print(f"\n{'='*60}", flush=True)
print(f"Total time: {total_elapsed/60:.1f}min", flush=True)
print(f"Total archive size: {total_archive_size/1e9:.2f}GB", flush=True)

# List all archives
print(f"\nArchives in {ARCHIVE_DIR}:", flush=True)
for f in sorted(os.listdir(ARCHIVE_DIR)):
    fp = os.path.join(ARCHIVE_DIR, f)
    if os.path.isfile(fp):
        print(f"  {f:40s} {os.path.getsize(fp)/1e9:.2f}GB", flush=True)