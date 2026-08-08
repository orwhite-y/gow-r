"""Batch extract all textures from all 25 texpacks to DDS."""
import os, sys, time, glob

sys.path.insert(0, r"E:\gow_re_workspace\scripts")
from gnf_to_dds_v3 import Texpack, parse_gnf_header, PC_FMT_MAP, gnf_to_dds

TEXPACK_DIR = r"E:\God of War Ragnarok\exec\wad\pc_le"
OUT_BASE = r"D:\God of War Ragnarok_extracted\models\textures"

def main():
    os.makedirs(OUT_BASE, exist_ok=True)
    
    texpacks = sorted(glob.glob(os.path.join(TEXPACK_DIR, "*.texpack")))
    print(f"Found {len(texpacks)} texpack files")
    
    total_ok = 0; total_fail = 0; total_skip = 0
    t0 = time.time()
    
    for tp_path in texpacks:
        tp_name = os.path.splitext(os.path.basename(tp_path))[0]
        out_dir = os.path.join(OUT_BASE, tp_name)
        os.makedirs(out_dir, exist_ok=True)
        
        tp = Texpack(tp_path)
        ok = 0; fail = 0; skip = 0
        errors = []
        
        for i in range(tp.TexsCount):
            fh, uh, bo = tp.texInfos[i]
            gnf_header, block_data_list = tp.export_texture(i)
            if gnf_header is None:
                fail += 1; continue
            h = parse_gnf_header(gnf_header)
            if h is None:
                fail += 1; continue
            if h["fmt"] not in PC_FMT_MAP:
                skip += 1; continue
            out_path = os.path.join(out_dir, f"{fh:016X}.dds")
            success, msg = gnf_to_dds(gnf_header, block_data_list, out_path)
            if success:
                ok += 1
            else:
                fail += 1
                if len(errors) < 5:
                    errors.append(f"[{i}] {fh:016X}: {msg}")
        
        tp.close()
        total_ok += ok; total_fail += fail; total_skip += skip
        elapsed = time.time() - t0
        print(f"  {tp_name}: OK={ok} FAIL={fail} SKIP={skip} (total: {total_ok}/{total_ok+total_fail+total_skip}, {elapsed:.0f}s)")
        if errors:
            for e in errors:
                print(f"    ERR: {e}")
    
    elapsed = time.time() - t0
    print(f"\n=== DONE ===")
    print(f"Total: OK={total_ok} FAIL={total_fail} SKIP={total_skip} time={elapsed:.0f}s")

if __name__ == "__main__":
    main()