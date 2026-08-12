import os, sys
sys.stdout.reconfigure(encoding='utf-8')

MODELS_DIR = r"D:\God of War Ragnarok_extracted\models"

regions = {}
for entry in os.listdir(MODELS_DIR):
    rpath = os.path.join(MODELS_DIR, entry)
    if not os.path.isdir(rpath): continue
    
    glb_sz = 0; dds_unique_sz = 0; mat_sz = 0; tx_sz = 0; json_sz = 0
    glb_n = 0; dds_u_n = 0; mat_n = 0; tx_n = 0; json_n = 0
    
    for root, dirs, files in os.walk(rpath):
        rel = os.path.relpath(root, rpath).replace("\\", "/")
        parts = rel.split("/")
        # Texpack dir: textures/texpack_name (2 levels from region root)
        is_texpack_tex = len(parts) == 2 and parts[0] == "textures"
        
        for f in files:
            fp = os.path.join(root, f)
            try: sz = os.path.getsize(fp)
            except: continue
            fl = f.lower()
            
            if fl.endswith(".glb"):
                glb_sz += sz; glb_n += 1
            elif fl.endswith(".dds"):
                if is_texpack_tex:
                    dds_unique_sz += sz; dds_u_n += 1
                # Skip hard-linked copies
            elif fl.endswith(".mat"):
                mat_sz += sz; mat_n += 1
            elif fl.endswith(".tx"):
                tx_sz += sz; tx_n += 1
            elif fl.endswith(".json"):
                json_sz += sz; json_n += 1
    
    total = glb_sz + dds_unique_sz + mat_sz + tx_sz + json_sz
    regions[entry] = {
        "total_gb": total/1024/1024/1024,
        "glb_gb": glb_sz/1024/1024/1024,
        "dds_gb": dds_unique_sz/1024/1024/1024,
        "mat_mb": (mat_sz+tx_sz)/1024/1024,
        "json_mb": json_sz/1024/1024,
        "files": glb_n + dds_u_n + mat_n + tx_n + json_n
    }

print(f"{'Region':<16} {'Total':>8} {'GLB':>8} {'DDS':>8} {'MAT+TX':>8} {'JSON':>8} {'Files':>8}")
print("-" * 72)
for name, info in sorted(regions.items(), key=lambda x: -x[1]["total_gb"]):
    print(f"{name:<16} {info['total_gb']:>7.1f}G {info['glb_gb']:>7.1f}G {info['dds_gb']:>7.1f}G {info['mat_mb']:>7.0f}M {info['json_mb']:>7.0f}M {info['files']:>8}")
print("-" * 72)
total_gb = sum(r["total_gb"] for r in regions.values())
print(f"{'TOTAL':<16} {total_gb:>7.1f}G")
print(f"\nNote: Hard-linked DDS copies excluded (saves ~200 GB)")