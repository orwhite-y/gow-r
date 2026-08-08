"""
Stage 2: Copy GLB files from SSD staging (F:\temp_glb\) to final HDD destination
with region -> WAD hierarchy.

Reads from SSD (fast), writes to HDD (only writes, no read seeking).
"""
import os, shutil, sys, time, collections

SRC_DIR = r"F:\temp_glb"
DST_BASE = r"D:\God of War Ragnarok_extracted\models"

def get_region(wad_name):
    n = wad_name.lower()
    if n.startswith("alf"):        return "alfheim"
    if n.startswith("asg"):        return "asgard"
    if n.startswith("hel"):        return "helheim"
    if n.startswith("jot"):        return "jotunheim"
    if n.startswith("mid"):        return "midgard"
    if n.startswith("msp"):        return "muspelheim"
    if n.startswith("muspelheim"): return "muspelheim"
    if n.startswith("nif"):        return "niflheim"
    if n.startswith("sva"):        return "svartalfheim"
    if n.startswith("van"):        return "vanaheim"
    if n.startswith("val"):        return "vanaheim"
    if n.startswith("rbr"):        return "niflheim"
    if n.startswith("northbay"):   return "midgard"
    if n.startswith("r_"):         return "characters"
    if n.startswith("add"):        return "characters"
    if n.startswith("char"):       return "characters"
    if n.startswith("c_"):         return "cutscenes"
    if n.startswith("base"):       return "base"
    if n.startswith("gbl"):        return "base"
    if n.startswith("boatglobal"): return "base"
    if n.startswith("wolfsledglobal"): return "base"
    if n.startswith("waterglobal"):    return "base"
    return "other"

def get_wad_name(filename):
    base = filename.rsplit('.', 1)[0]
    if '_MESH_' in base:
        return base.split('_MESH_')[0]
    return base

def main():
    files = sorted([f for f in os.listdir(SRC_DIR) if f.endswith('.glb')])
    print(f"Total GLB files to copy: {len(files)}")
    sys.stdout.flush()
    
    # Pre-create all destination directories
    dir_cache = set()
    for f in files:
        wad = get_wad_name(f)
        region = get_region(wad)
        dst_dir = os.path.join(DST_BASE, region, wad)
        if dst_dir not in dir_cache:
            os.makedirs(dst_dir, exist_ok=True)
            dir_cache.add(dst_dir)
    print(f"Created {len(dir_cache)} WAD directories in {len(set(get_region(get_wad_name(f)) for f in files))} regions")
    sys.stdout.flush()
    
    # Copy files (use shutil.copy - no metadata, faster than copy2)
    total_copied = 0
    total_skipped = 0
    t0 = time.time()
    
    for f in files:
        wad = get_wad_name(f)
        region = get_region(wad)
        dst_dir = os.path.join(DST_BASE, region, wad)
        src = os.path.join(SRC_DIR, f)
        dst = os.path.join(dst_dir, f)
        
        if os.path.exists(dst):
            total_skipped += 1
        else:
            shutil.copy(src, dst)
            total_copied += 1
        
        if (total_copied + total_skipped) % 5000 == 0:
            elapsed = time.time() - t0
            pct = (total_copied + total_skipped) / len(files) * 100
            rate = (total_copied + total_skipped) / elapsed if elapsed > 0 else 0
            eta = (len(files) - total_copied - total_skipped) / rate if rate > 0 else 0
            print(f"  {total_copied + total_skipped}/{len(files)} ({pct:.1f}%) - {rate:.0f} files/s - ETA {eta:.0f}s - {region}/{wad}")
            sys.stdout.flush()
    
    elapsed = time.time() - t0
    print(f"\nDone! Copied {total_copied}, skipped {total_skipped} in {elapsed:.0f}s ({total_copied/elapsed:.0f} files/s)")
    sys.stdout.flush()

if __name__ == "__main__":
    main()