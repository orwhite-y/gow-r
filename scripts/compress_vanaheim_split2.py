import subprocess, os, time

SEVEN_ZIP = r"F:\soft\7-Zip\7z.exe"
ARCHIVE_DIR = r"F:\gow_archives"
SRC_ROOT = r"D:\God of War Ragnarok_extracted\models\vanaheim"

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

all_dirs = sorted([d for d in os.listdir(SRC_ROOT) if os.path.isdir(os.path.join(SRC_ROOT, d))])

for part_name, prefixes in groups.items():
    archive = os.path.join(ARCHIVE_DIR, f"{part_name}.7z")
    
    if os.path.exists(archive) and os.path.getsize(archive) > 0:
        log(f"SKIP {part_name} - already exists")
        continue
    
    target_dirs = []
    for d in all_dirs:
        for pfx in prefixes:
            if d.startswith(pfx):
                target_dirs.append(d)
                break
    
    log(f"START {part_name} - {len(target_dirs)} dirs")
    
    # Compress each subdir individually into the same archive (append mode)
    # Use -spf2 to preserve full relative paths
    start = time.time()
    total_files = 0
    fail = False
    for i, d in enumerate(target_dirs):
        dp = os.path.join(SRC_ROOT, d)
        cmd = [SEVEN_ZIP, "a", "-t7z", "-mx=3", "-mmt=8", "-spf2", archive, dp]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
        if proc.returncode != 0:
            log(f"  FAIL subdir {d}: rc={proc.returncode} {proc.stderr[:500]}")
            fail = True
            break
        if (i+1) % 10 == 0:
            sz = os.path.getsize(archive) if os.path.exists(archive) else 0
            log(f"  progress: {i+1}/{len(target_dirs)} dirs, archive={sz/1024/1024:.1f} MB")
    
    elapsed = time.time() - start
    if not fail and os.path.exists(archive):
        sz = os.path.getsize(archive)
        log(f"DONE {part_name} - {sz/1024/1024:.1f} MB in {elapsed/60:.1f} min")
    else:
        log(f"FAIL {part_name}")

log("VANAHEIM SPLIT ALL DONE")