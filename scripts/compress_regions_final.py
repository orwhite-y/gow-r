import os, subprocess, time, sys

MODELS_DIR = r"D:\God of War Ragnarok_extracted\models"
ARCHIVE_DIR = r"F:\gow_archives"
SEVEN_ZIP = r"F:\soft\7-Zip\7z.exe"

os.makedirs(ARCHIVE_DIR, exist_ok=True)

# Get regions sorted by size (smallest first for quick progress)
regions_info = []
for region in os.listdir(MODELS_DIR):
    rpath = os.path.join(MODELS_DIR, region)
    if not os.path.isdir(rpath) or region.startswith("_"):
        continue
    # Quick size estimate
    total = 0
    for root, dirs, files in os.walk(rpath):
        for f in files:
            try: total += os.path.getsize(os.path.join(root, f))
            except: pass
    regions_info.append((region, total))

regions_info.sort(key=lambda x: x[1])

print(f"Regions to compress ({len(regions_info)}):", flush=True)
for r, s in regions_info:
    print(f"  {r:20s}: {s/1e9:.2f}GB", flush=True)
print(flush=True)

grand_start = time.time()

for idx, (region, estimated_size) in enumerate(regions_info):
    rpath = os.path.join(MODELS_DIR, region)
    archive_path = os.path.join(ARCHIVE_DIR, f"{region}.7z")
    
    if os.path.exists(archive_path):
        print(f"[{idx+1}/{len(regions_info)}] SKIP {region} (already exists)", flush=True)
        continue
    
    # Build list file: include all subdirs except top-level "textures"
    list_file = os.path.join(ARCHIVE_DIR, f"_list_{region}.txt")
    entries = []
    for item in sorted(os.listdir(rpath)):
        item_path = os.path.join(rpath, item)
        if item == "textures":
            continue  # Skip region-level texpack textures (per-WAD copies already have what's needed)
        entries.append(item_path + "\\*")
    
    with open(list_file, 'w') as f:
        for e in entries:
            f.write(e + "\n")
    
    print(f"[{idx+1}/{len(regions_info)}] COMPRESS {region} ({estimated_size/1e9:.1f}GB est, {len(entries)} WAD dirs)...", flush=True)
    t0 = time.time()
    
    cmd = [SEVEN_ZIP, "a", "-t7z", "-mx=3", "-mmt=8", archive_path, f"@{list_file}"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
    
    elapsed = time.time() - t0
    if os.path.exists(archive_path):
        size_mb = os.path.getsize(archive_path) / 1e6
        print(f"  OK: {size_mb:.0f} MB in {elapsed:.0f}s ({elapsed/60:.1f}min)", flush=True)
    else:
        print(f"  FAILED!", flush=True)
        print(f"  stderr: {result.stderr[:300]}", flush=True)
    
    # Clean up list file
    try: os.remove(list_file)
    except: pass

total_elapsed = time.time() - grand_start
print(f"\n{'='*60}", flush=True)
print(f"All done in {total_elapsed/60:.1f} minutes", flush=True)

# Summary
print(f"\nArchives:", flush=True)
total_archive = 0
for f in sorted(os.listdir(ARCHIVE_DIR)):
    fp = os.path.join(ARCHIVE_DIR, f)
    if os.path.isfile(fp) and f.endswith('.7z'):
        s = os.path.getsize(fp)
        total_archive += s
        print(f"  {f:40s}: {s/1e9:.2f} GB", flush=True)
print(f"  {'TOTAL':40s}: {total_archive/1e9:.2f} GB", flush=True)