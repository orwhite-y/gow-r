import subprocess, os, time

SEVEN_ZIP = r"F:\soft\7-Zip\7z.exe"
ARCHIVE_DIR = r"F:\gow_archives"
SRC_ROOT = r"D:\God of War Ragnarok_extracted\models\vanaheim"

# 4 sub-archives grouped by area prefix
groups = {
    "vanaheim_part1_crat": ["van_crat"],
    "vanaheim_part2_jngl": ["van_jngl"],
    "vanaheim_part3_vanvil": ["van_vanvil"],
    "vanaheim_part4_delta_falls_misc": ["van_delta", "van_falls", "van_misc", "vanaheim_zoo"],
}

log_path = os.path.join(ARCHIVE_DIR, "compress_log.txt")

def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(line + "\n")

for part_name, prefixes in groups.items():
    archive = os.path.join(ARCHIVE_DIR, f"{part_name}.7z")
    
    if os.path.exists(archive) and os.path.getsize(archive) > 0:
        log(f"SKIP {part_name} - already exists")
        continue
    
    # collect matching dirs
    all_dirs = [d for d in os.listdir(SRC_ROOT) if os.path.isdir(os.path.join(SRC_ROOT, d))]
    target_dirs = []
    for d in all_dirs:
        for pfx in prefixes:
            if d.startswith(pfx):
                target_dirs.append(d)
                break
    
    log(f"START {part_name} - {len(target_dirs)} dirs")
    
    # build file list for 7z
    listfile = os.path.join(ARCHIVE_DIR, f"{part_name}_listfile.txt")
    with open(listfile, "w", encoding="utf-8") as lf:
        for d in target_dirs:
            lf.write(os.path.join(SRC_ROOT, d) + os.sep + "*" + "\n")
    
    cmd = [SEVEN_ZIP, "a", "-t7z", "-mx=3", "-mmt=8", archive, f"@{listfile}"]
    log(f"CMD: 7z a {part_name}.7z @{part_name}_listfile.txt")
    
    start = time.time()
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
    elapsed = time.time() - start
    
    if proc.returncode == 0:
        sz = os.path.getsize(archive)
        log(f"DONE {part_name} - {sz/1024/1024:.1f} MB in {elapsed/60:.1f} min")
    else:
        log(f"FAIL {part_name} - rc={proc.returncode} stderr={proc.stderr[:2000]}")
    
    # cleanup listfile
    try:
        os.remove(listfile)
    except:
        pass

log("VANAHEIM ALL DONE")