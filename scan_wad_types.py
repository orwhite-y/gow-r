import struct, lz4.frame, os, sys
from collections import defaultdict

PC_LE = r"E:\God of War Ragnarok\exec\wad\pc_le"

# Pick a WAD with mesh data
wad_name = "alf_bluff100_entrance.wad"
wad_path = os.path.join(PC_LE, wad_name)

with open(wad_path, "rb") as f:
    data = lz4.frame.decompress(f.read())

ec = struct.unpack_from("<I", data, 8)[0]
print(f"WAD: {wad_name}, entries: {ec}")

type_counts = defaultdict(int)
type_samples = defaultdict(list)

for i in range(ec):
    o = 64 + 144 * i
    word0 = struct.unpack_from("<H", data, o)[0]
    flags = struct.unpack_from("<H", data, o+2)[0]
    size = struct.unpack_from("<I", data, o+4)[0]
    name = data[o+24:o+104].split(b"\x00")[0].decode("ascii", errors="replace")
    hash_val = struct.unpack_from("<Q", data, o+8)[0]
    t108 = data[o+108]
    t109 = data[o+109]
    t110 = data[o+110]
    b111 = data[o+111]
    
    type_key = f"word0={word0:>3} t108={t108:#04x} t109={t109:#04x} b111={b111}"
    type_counts[type_key] += 1
    if len(type_samples[type_key]) < 5:
        type_samples[type_key].append(f"  name={name[:50]:<50} hash={hash_val:#018x} size={size}")

print(f"\n{'Type':<50} {'Count':>5}  Samples")
print("-" * 120)
for tk in sorted(type_counts.keys()):
    print(f"{tk:<50} {type_counts[tk]:>5}")
    for s in type_samples[tk]:
        print(s)