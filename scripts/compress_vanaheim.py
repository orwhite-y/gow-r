import subprocess, os, time

SEVEN_ZIP = r"F:\soft\7-Zip\7z.exe"
ARCHIVE_DIR = r"F:\gow_archives"
SRC_DIR = r"D:\God of War Ragnarok_extracted\models\vanaheim"

archive = os.path.join(ARCHIVE_DIR, "vanaheim.7z")

log_path = os.path.join(ARCHIVE_DIR, "compress_log.txt")
with open(log_path, "a", encoding="utf-8") as logf:
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    logf.write(f"[{ts}] START vanaheim\n")
    logf.flush()

cmd = [SEVEN_ZIP, "a", "-t7z", "-mx=3", "-mmt=8", archive, SRC_DIR + os.sep + "*"]
start = time.time()
proc = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
elapsed = time.time() - start

with open(log_path, "a", encoding="utf-8") as logf:
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    if proc.returncode == 0:
        sz = os.path.getsize(archive)
        logf.write(f"[{ts}] DONE vanaheim - {sz/1024/1024:.1f} MB in {elapsed/60:.1f} min\n")
    else:
        logf.write(f"[{ts}] FAIL vanaheim - rc={proc.returncode} stderr={proc.stderr[:1000]}\n")
    logf.flush()