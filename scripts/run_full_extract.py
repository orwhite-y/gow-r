#!/usr/bin/env python3
"""Run full extraction with skip logic and progress logging."""
import os, sys, time, struct, lz4.frame, json
import numpy as np
from collections import defaultdict

# Import everything from extract_all_glb
sys.path.insert(0, r"E:\gow_re_workspace\scripts")
from extract_all_glb import *

PC_LE = r"E:\God of War Ragnarok\exec\wad\pc_le"
OUT_DIR = r"E:\gow_re_workspace\output\glb_all"
LOG_FILE = r"E:\gow_re_workspace\output\extract_progress.log"
os.makedirs(OUT_DIR, exist_ok=True)

def is_wad_processed(wad_base):
    for f in os.listdir(OUT_DIR):
        if f.startswith(wad_base + "_"):
            return True
    return False

def main():
    lodpack_index = load_lodpack_index()
    wad_names = sorted([f for f in os.listdir(PC_LE) if f.endswith(".wad")])
    
    stats = defaultdict(int)
    stats["skipped"] = 0
    t0 = time.time()
    
    with open(LOG_FILE, 'w') as log:
        log.write(f"Starting extraction of {len(wad_names)} WAD files\n")
        log.flush()
        
        for wi, wad_name in enumerate(wad_names):
            wad_base = os.path.splitext(wad_name)[0]
            if is_wad_processed(wad_base):
                stats["skipped"] += 1
                continue
            
            try:
                process_wad(wad_name, lodpack_index, stats)
            except Exception as e:
                log.write(f"  ERROR {wad_name}: {e}\n")
                log.flush()
            
            if (wi + 1) % 20 == 0:
                elapsed = time.time() - t0
                rate = (wi + 1 - stats["skipped"]) / elapsed if elapsed > 0 else 0
                remaining = (len(wad_names) - wi - 1) / rate if rate > 0 else 0
                msg = (f"[{wi+1}/{len(wad_names)}] GLBs={stats['glb_written']} "
                       f"inline={stats['inline_ok']}/{stats['inline_fail']} "
                       f"lodpack={stats['lodpack_ok']}/{stats['lodpack_fail']} "
                       f"skipped={stats['skipped']} "
                       f"verts={stats['total_verts']} tris={stats['total_tris']} "
                       f"elapsed={elapsed:.0f}s ETA={remaining:.0f}s\n")
                log.write(msg)
                log.flush()
        
        elapsed = time.time() - t0
        log.write(f"\n=== DONE ({elapsed:.1f}s) ===\n")
        log.write(f"GLB files written: {stats['glb_written']}\n")
        log.write(f"Inline: OK={stats['inline_ok']} FAIL={stats['inline_fail']} NO_VDATA={stats['inline_no_vdata']}\n")
        log.write(f"Lodpack: OK={stats['lodpack_ok']} FAIL={stats['lodpack_fail']}\n")
        log.write(f"Skipped: {stats['skipped']}\n")
        log.write(f"Total vertices: {stats['total_verts']}\n")
        log.write(f"Total triangles: {stats['total_tris']}\n")
        log.flush()

if __name__ == "__main__":
    main()