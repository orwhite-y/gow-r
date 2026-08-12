import os, sys, subprocess, time
sys.stdout.reconfigure(encoding='utf-8')

MODELS_DIR = r"D:\God of War Ragnarok_extracted\models"
ARCHIVE_DIR = r"F:\gow_archives"
SEVEN_ZIP = r"F:\soft\7-Zip\7z.exe"

os.makedirs(ARCHIVE_DIR, exist_ok=True)

# Build file lists per region, excluding hard-linked DDS copies in WAD texture dirs
regions = sorted([d for d in os.listdir(MODELS_DIR) if os.path.isdir(os.path.join(MODELS_DIR, d))])

for region in regions:
    region_path = os.path.join(MODELS_DIR, region)
    file_list_path = os.path.join(ARCHIVE_DIR, f"{region}_filelist.txt")
    
    # Build file list
    files_to_include = []
    for root, dirs, files in os.walk(region_path):
        rel = os.path.relpath(root, region_path).replace("\\", "/")
        parts = rel.split("/")
        
        # Skip WAD-level texture dirs (hard-linked DDS copies)
        # WAD texture dir: {wad_name}/textures (2 parts, parts[1] == "textures")
        is_wad_tex = len(parts) == 2 and parts[1] == "textures"
        
        for f in files:
            if is_wad_tex and f.lower().endswith(".dds"):
                continue  # Skip hard-linked copy
            fp = os.path.join(root, f)
            files_to_include.append(fp)
    
    if not files_to_include:
        print(f"  {region}: no files, skipping")
        continue
    
    # Write file list
    with open(file_list_path, "w", encoding="utf-8") as flf:
        for fp in files_to_include:
            flf.write(fp + "\n")
    
    # Calculate total size
    total_sz = sum(os.path.getsize(fp) for fp in files_to_include if os.path.exists(fp))
    
    archive_path = os.path.join(ARCHIVE_DIR, f"gow_models_{region}.7z")
    
    print(f"[{region}] {len(files_to_include)} files, {total_sz/1024/1024/1024:.1f} GB -> compressing...")
    t0 = time.time()
    
    # Run 7z
    result = subprocess.run([
        SEVEN_ZIP, "a",
        archive_path,
        f"@{file_list_path}",
        "-mx=5",           # Normal compression (fast, decent ratio)
        "-mmt=8",          # 8 threads
        f"-spf2",          # Store full path info relative to MODELS_DIR
    ], capture_output=True, text=True, timeout=3600)
    
    elapsed = time.time() - t0
    archive_sz = os.path.getsize(archive_path) if os.path.exists(archive_path) else 0
    
    if result.returncode == 0:
        ratio = archive_sz / total_sz * 100 if total_sz > 0 else 0
        print(f"  OK: {archive_sz/1024/1024/1024:.1f} GB ({ratio:.0f}%) in {elapsed:.0f}s")
    else:
        print(f"  FAILED: {result.stderr[:200]}")
    
    # Clean up file list
    os.remove(file_list_path)

# Also create a small archive with relinking script
relink_script = r'''# relink_textures.py - Recreate hard links after extraction
# Run this script after extracting all region archives to link textures into WAD dirs
import os, json, sys

MODELS_DIR = r"D:\God of War Ragnarok_extracted\models"

for root, dirs, files in os.walk(MODELS_DIR):
    if "material_mapping.json" not in files:
        continue
    map_path = os.path.join(root, "material_mapping.json")
    with open(map_path) as f:
        mapping = json.load(f)
    
    tex_dir = os.path.join(root, "textures")
    os.makedirs(tex_dir, exist_ok=True)
    
    for mesh in mapping.get("meshes", []):
        for tex in mesh.get("textures", []):
            if not tex.get("found"):
                continue
            hash_hex = tex["hash"].upper()
            target = os.path.join(tex_dir, f"{hash_hex}.dds")
            if os.path.exists(target):
                continue
            # Find source DDS
            dds_hash = tex.get("dds_hash", hash_hex)
            for r2, d2, f2 in os.walk(MODELS_DIR):
                for fn in f2:
                    if fn.upper() == f"{dds_hash}.DDS":
                        src = os.path.join(r2, fn)
                        try:
                            os.link(src, target)
                        except:
                            import shutil
                            shutil.copy2(src, target)
                        break
                else:
                    continue
                break
    print(f"Processed: {root}")
'''
relink_path = os.path.join(ARCHIVE_DIR, "relink_textures.py")
with open(relink_path, "w") as f:
    f.write(relink_script)

print(f"\nRelinking script saved to: {relink_path}")
print(f"\nArchives in: {ARCHIVE_DIR}")