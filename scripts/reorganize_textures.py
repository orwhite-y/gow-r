"""
Reorganize textures from flat texpack structure to region hierarchy.

Before: D:\God of War Ragnarok_extracted\models\textures\{texpack_name}\*.dds
After:  D:\God of War Ragnarok_extracted\models\{region}\textures\{texpack_name}\*.dds

Uses shutil.move (instant on same volume D:).
"""
import os, shutil, sys, time

TEX_BASE = r"D:\God of War Ragnarok_extracted\models\textures"
DST_BASE = r"D:\God of War Ragnarok_extracted\models"

def get_region_for_texpack(texpack_name):
    n = texpack_name.lower()
    if "midgard" in n:      return "midgard"
    if "svartalfheim" in n: return "svartalfheim"
    if "alfheim" in n:      return "alfheim"
    if "jotunheim" in n:    return "jotunheim"
    if "vanaheim" in n:     return "vanaheim"
    if "asgard" in n:       return "asgard"
    if "muspelheim" in n:   return "muspelheim"
    if "helheim" in n:      return "helheim"
    if "niflheim" in n or "rbr" in n: return "niflheim"
    if "valhalla" in n:     return "valhalla"
    if n == "root":         return "base"
    return "other"

def main():
    if not os.path.exists(TEX_BASE):
        print(f"Texture directory not found: {TEX_BASE}")
        return
    
    texpacks = [d for d in os.listdir(TEX_BASE) if os.path.isdir(os.path.join(TEX_BASE, d))]
    print(f"Found {len(texpacks)} texpack directories")
    
    total_moved = 0
    t0 = time.time()
    
    for tp in sorted(texpacks):
        region = get_region_for_texpack(tp)
        src_dir = os.path.join(TEX_BASE, tp)
        dst_dir = os.path.join(DST_BASE, region, "textures", tp)
        
        os.makedirs(os.path.dirname(dst_dir), exist_ok=True)
        
        # Count files
        files = [f for f in os.listdir(src_dir) if f.endswith('.dds')]
        print(f"  {tp} -> {region}/textures/{tp} ({len(files)} files)")
        sys.stdout.flush()
        
        # Move entire directory (instant on same volume)
        if os.path.exists(dst_dir):
            # Merge: move individual files
            for f in files:
                src = os.path.join(src_dir, f)
                dst = os.path.join(dst_dir, f)
                if not os.path.exists(dst):
                    shutil.move(src, dst)
                    total_moved += 1
            # Remove empty source dir
            try:
                os.rmdir(src_dir)
            except:
                pass
        else:
            shutil.move(src_dir, dst_dir)
            total_moved += len(files)
    
    elapsed = time.time() - t0
    print(f"\nDone! Moved {total_moved} files in {elapsed:.0f}s")
    
    # Remove empty textures directory if all moved
    remaining = os.listdir(TEX_BASE)
    if not remaining:
        os.rmdir(TEX_BASE)
        print("Removed empty textures directory")
    else:
        print(f"Remaining in textures/: {remaining}")
    
    # Print final structure
    print("\n=== Final structure ===")
    for region in sorted(os.listdir(DST_BASE)):
        rpath = os.path.join(DST_BASE, region)
        if not os.path.isdir(rpath):
            continue
        tex_path = os.path.join(rpath, "textures")
        if os.path.exists(tex_path):
            tp_dirs = os.listdir(tex_path)
            dds_count = sum(len([f for f in os.listdir(os.path.join(tex_path, d)) if f.endswith('.dds')]) for d in tp_dirs)
            print(f"  {region}/textures/: {len(tp_dirs)} texpacks, {dds_count} DDS files")

if __name__ == "__main__":
    main()