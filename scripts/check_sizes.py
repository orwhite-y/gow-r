import os

MODELS_DIR = r"D:\God of War Ragnarok_extracted\models"

print("=== Per-region sizes ===", flush=True)
grand_total = 0
region_data = []

for region in sorted(os.listdir(MODELS_DIR)):
    rpath = os.path.join(MODELS_DIR, region)
    if not os.path.isdir(rpath):
        continue
    total = 0
    glb_size = 0
    dds_size = 0
    mat_size = 0
    file_count = 0
    for root, dirs, files in os.walk(rpath):
        for f in files:
            fp = os.path.join(root, f)
            try:
                s = os.path.getsize(fp)
                # Note: hard links share data, getsize reports full size
                total += s
                if f.endswith('.glb'):
                    glb_size += s
                elif f.endswith('.dds'):
                    dds_size += s
                elif f.endswith('.mat') or f.endswith('.tx') or f.endswith('.json'):
                    mat_size += s
                file_count += 1
            except:
                pass
    grand_total += total
    region_data.append((region, total, glb_size, dds_size, mat_size, file_count))
    print(f"  {region:20s}: {total/1e9:8.2f} GB  (GLB={glb_size/1e9:.2f} DDS={dds_size/1e9:.2f} MAT={mat_size/1e6:.0f}MB files={file_count})")

print(f"\n  {'GRAND TOTAL':20s}: {grand_total/1e9:8.2f} GB")
print(f"\nNote: DDS sizes include hard-linked duplicates (actual disk usage is lower)")