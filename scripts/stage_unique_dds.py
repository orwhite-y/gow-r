import os, sys

MODELS_DIR = r"D:\God of War Ragnarok_extracted\models"
STAGE_DIR = r"D:\God of War Ragnarok_extracted\models\_unique_textures"

os.makedirs(STAGE_DIR, exist_ok=True)

print("Creating hard links for unique DDS files...", flush=True)
seen = set()
linked = 0
skipped = 0
errors = 0

for region in sorted(os.listdir(MODELS_DIR)):
    if region == "_unique_textures":
        continue
    rpath = os.path.join(MODELS_DIR, region)
    if not os.path.isdir(rpath):
        continue
    for root, dirs, files in os.walk(rpath):
        for f in files:
            if f.endswith('.dds'):
                h = f[:-4]
                if h in seen:
                    continue
                seen.add(h)
                src = os.path.join(root, f)
                dst = os.path.join(STAGE_DIR, f)
                if os.path.exists(dst):
                    skipped += 1
                    continue
                try:
                    os.link(src, dst)  # Hard link, same D: volume, no extra space
                    linked += 1
                except Exception as e:
                    errors += 1
                    if errors <= 5:
                        print(f"  ERROR: {f}: {e}")
                if linked % 10000 == 0 and linked > 0:
                    print(f"  Linked {linked} files...", flush=True)

print(f"\nDone: linked={linked}, skipped={skipped}, errors={errors}, total_unique={len(seen)}")