import os

MODELS_DIR = r"D:\God of War Ragnarok_extracted\models"

print("=== Texture directory structure per region ===", flush=True)
for region in sorted(os.listdir(MODELS_DIR)):
    rpath = os.path.join(MODELS_DIR, region)
    if not os.path.isdir(rpath):
        continue
    
    # Check region-level textures dir
    rtex = os.path.join(rpath, "textures")
    rtex_count = 0
    rtex_size = 0
    if os.path.isdir(rtex):
        for root, dirs, files in os.walk(rtex):
            for f in files:
                if f.endswith('.dds'):
                    rtex_count += 1
                    try:
                        rtex_size += os.path.getsize(os.path.join(root, f))
                    except:
                        pass
    
    # Check per-WAD texture dirs
    wad_tex_count = 0
    wad_tex_size = 0
    wad_count = 0
    for wad in os.listdir(rpath):
        wpath = os.path.join(rpath, wad)
        if not os.path.isdir(wpath) or wad == "textures":
            continue
        wad_count += 1
        wtex = os.path.join(wpath, "textures")
        if os.path.isdir(wtex):
            for f in os.listdir(wtex):
                if f.endswith('.dds'):
                    wad_tex_count += 1
                    try:
                        wad_tex_size += os.path.getsize(os.path.join(wtex, f))
                    except:
                        pass
    
    print(f"  {region:20s}: WADs={wad_count:4d} | region_tex={rtex_count:6d}({rtex_size/1e9:.2f}GB) | wad_tex={wad_tex_count:6d}({wad_tex_size/1e9:.2f}GB)")