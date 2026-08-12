import os, json

MODELS_DIR = r"D:\God of War Ragnarok_extracted\models"

print("=== Compression plan per region ===", flush=True)
total_archive_size = 0

for region in sorted(os.listdir(MODELS_DIR)):
    rpath = os.path.join(MODELS_DIR, region)
    if not os.path.isdir(rpath):
        continue
    
    rtex = os.path.join(rpath, "textures")
    has_region_tex = os.path.isdir(rtex)
    
    # Calculate sizes
    glb_size = 0
    mat_tx_json_size = 0
    region_tex_size = 0
    wad_tex_size = 0  # hard-linked copies to exclude
    wad_count = 0
    
    for wad in os.listdir(rpath):
        wpath = os.path.join(rpath, wad)
        if not os.path.isdir(wpath):
            continue
        if wad == "textures":
            # Region-level textures
            for root, dirs, files in os.walk(wpath):
                for f in files:
                    try:
                        region_tex_size += os.path.getsize(os.path.join(root, f))
                    except:
                        pass
            continue
        wad_count += 1
        for f in os.listdir(wpath):
            fp = os.path.join(wpath, f)
            if os.path.isfile(f):
                try:
                    s = os.path.getsize(fp)
                    if f.endswith('.glb'):
                        glb_size += s
                    elif f.endswith('.mat') or f.endswith('.tx') or f.endswith('.json'):
                        mat_tx_json_size += s
                except:
                    pass
            elif os.path.isdir(f) and f == "textures":
                # Per-WAD textures (hard-linked copies)
                for root, dirs, files in os.walk(fp):
                    for ff in files:
                        try:
                            wad_tex_size += os.path.getsize(os.path.join(root, ff))
                        except:
                            pass
    
    # What to include in archive:
    if has_region_tex:
        # Include: GLB + MAT/TX/JSON + region_tex (unique DDS)
        # Exclude: per-WAD textures (hard-linked copies)
        archive_content_size = glb_size + mat_tx_json_size + region_tex_size
        excluded = wad_tex_size
        strategy = "GLB+MAT+TX+JSON+region_tex (exclude wad_tex hardlinks)"
    else:
        # No region-level textures - include per-WAD DDS (likely unique)
        archive_content_size = glb_size + mat_tx_json_size + wad_tex_size
        excluded = 0
        strategy = "GLB+MAT+TX+JSON+wad_tex (no region_tex, include all)"
    
    total_archive_size += archive_content_size
    print(f"  {region:20s}: WADs={wad_count:4d} | include={archive_content_size/1e9:7.2f}GB exclude={excluded/1e9:7.2f}GB | {strategy}")

print(f"\n  {'TOTAL TO ARCHIVE':20s}: {total_archive_size/1e9:7.2f}GB")
print(f"  (vs 360GB with all hard-linked copies)")
print(f"  Savings: {(360.74 - total_archive_size/1e9):.2f}GB excluded")