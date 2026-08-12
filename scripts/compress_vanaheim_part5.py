import subprocess, os, time

SEVEN_ZIP = r"F:\soft\7-Zip\7z.exe"
ARCHIVE_DIR = r"F:\gow_archives"
SRC_ROOT = r"D:\God of War Ragnarok_extracted\models\vanaheim"

archive = os.path.join(ARCHIVE_DIR, "vanaheim_part5_zoo_misc.7z")

# All dirs missed by parts 1-4
missed_dirs = [
    "vanaheim_architecture_zoo",
    "vanaheim_crater_zoo",
    "vanaheim_rock_zoo",
    "textures",
    "val015_outerrealms",
    "val075_lights",
    "van010_realmscripts",
    "van020_freyafalcon",
    "van050_sound",
    "van075_lights",
]

log_path = os.path.join(ARCHIVE_DIR, "compress_log.txt")

ts = time.strftime("%Y-%m-%d %H:%M:%S")
with open(log_path, "a", encoding="utf-8") as f:
    f.write(f"[{ts}] START vanaheim_part5_zoo_misc - {len(missed_dirs)} dirs\n")
    f.flush()

start = time.time()
for d in missed_dirs:
    dp = os.path.join(SRC_ROOT, d)
    if not os.path.isdir(dp):
        continue
    cmd = [SEVEN_ZIP, "a", "-t7z", "-mx=3", "-mmt=8", "-spf2", archive, dp]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
    if proc.returncode != 0:
        ts2 = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{ts2}]   FAIL {d}: {proc.stderr[:500]}\n")

elapsed = time.time() - start
sz = os.path.getsize(archive) if os.path.exists(archive) else 0
ts = time.strftime("%Y-%m-%d %H:%M:%S")
with open(log_path, "a", encoding="utf-8") as f:
    f.write(f"[{ts}] DONE vanaheim_part5_zoo_misc - {sz/1024/1024:.1f} MB in {elapsed/60:.1f} min\n")
    f.write(f"[{ts}] VANAHEIM PART5 DONE\n")