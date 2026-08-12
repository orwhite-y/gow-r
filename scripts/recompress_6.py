import subprocess, sys, os, time

SEVEN_ZIP = r"F:\soft\7-Zip\7z.exe"
ARCHIVE_DIR = r"F:\gow_archives"
SRC_ROOT = r"D:\God of War Ragnarok_extracted\models"

# 6 regions to compress, smallest first
regions = [
    "cutscenes",
    "base",
    "muspelheim",
    "characters",
    "niflheim",
    "midgard",
]

log_path = os.path.join(ARCHIVE_DIR, "compress_log.txt")
logf = open(log_path, "w", encoding="utf-8")

def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    logf.write(line + "\n")
    logf.flush()

for region in regions:
    archive = os.path.join(ARCHIVE_DIR, f"{region}.7z")
    src_dir = os.path.join(SRC_ROOT, region)
    
    if os.path.exists(archive) and os.path.getsize(archive) > 0:
        log(f"SKIP {region} - archive already exists and non-empty")
        continue
    
    if not os.path.isdir(src_dir):
        log(f"SKIP {region} - source dir not found: {src_dir}")
        continue
    
    # count files
    total_files = sum(len(files) for _, _, files in os.walk(src_dir))
    log(f"START {region} - {total_files} files to compress")
    
    cmd = [SEVEN_ZIP, "a", "-t7z", "-mx=3", "-mmt=8", archive, src_dir + os.sep + "*"]
    log(f"CMD: {' '.join(cmd)}")
    
    start = time.time()
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
    elapsed = time.time() - start
    
    if proc.returncode == 0:
        sz = os.path.getsize(archive)
        log(f"DONE {region} - {sz/1024/1024:.1f} MB in {elapsed/60:.1f} min")
    else:
        log(f"FAIL {region} - returncode={proc.returncode}")
        log(f"STDERR: {proc.stderr[:2000]}")

log("ALL DONE")
logf.close()