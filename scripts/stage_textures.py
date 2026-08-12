import os, sys

MODELS_DIR = r"D:\God of War Ragnarok_extracted\models"
STAGE_DIR = r"F:\gow_archives\textures_staging"

os.makedirs(STAGE_DIR, exist_ok=True)

print("Collecting unique DDS files to staging dir...", flush=True)
seen = set()
count = 0
total_size = 0

for region in sorted(os.listdir(MODELS_DIR)):
    rpath = os.path.join(MODELS_DIR, region)
    if not os.path.isdir(rpath):
        continue
    for root, dirs, files in os.walk(rpath):
        for f in files:
            if f.endswith('.dds'):
                h = f[:-4]
                if h not in seen:
                    seen.add(h)
                    src = os.path.join(root, f)
                    dst = os.path.join(STAGE_DIR, f)
                    try:
                        size = os.path.getsize(src)
                        total_size += size
                        # Hard link to staging (same D: volume... wait, F: is different volume!)
                        # Can't hard link across volumes, must copy
                        if not os.path.exists(dst):
                            # Use os.link for same volume, copy for cross-volume
                            try:
                                os.link(src, dst)
                            except OSError:
                                # Cross-volume, must copy
                                import shutil
                                shutil.copy2(src, dst)
                        count += 1
                        if count % 5000 == 0:
                            print(f"  {count} files staged ({total_size/1e9:.1f}GB)...", flush=True)
                    except Exception as e:
                        print(f"  ERROR: {f}: {e}")

print(f"\nTotal unique DDS staged: {count} ({total_size/1e9:.2f}GB)")