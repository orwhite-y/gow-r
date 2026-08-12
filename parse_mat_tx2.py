import struct, lz4.frame, os

PC_LE = r"E:\God of War Ragnarok\exec\wad\pc_le"
wad_name = "alf_bluff100_entrance.wad"

with open(os.path.join(PC_LE, wad_name), "rb") as f:
    data = lz4.frame.decompress(f.read())

ec = struct.unpack_from("<I", data, 8)[0]
ds = 64 + 144 * ec

# Fast offset calculation using running offset with alignment
offsets = []
cur = ds
for i in range(ec):
    o = 64 + 144 * i
    sz = struct.unpack_from("<I", data, o+4)[0]
    al = struct.unpack_from("<I", data, o+104)[0]
    if al > 0:
        cur = (cur + al - 1) & ~(al - 1)
    offsets.append(cur)
    cur += sz

# Find MAT_ entries (t109=0x0a)
print("=== MAT entries ===")
mat_count = 0
for i in range(ec):
    o = 64 + 144 * i
    name = data[o+24:o+104].split(b"\x00")[0].decode("ascii", errors="replace")
    t109 = data[o+109]
    if name.startswith("MAT_") and t109 == 0x0a:
        sz = struct.unpack_from("<I", data, o+4)[0]
        hash_val = struct.unpack_from("<Q", data, o+8)[0]
        fo = offsets[i]
        mat_data = data[fo:fo+sz]
        
        if mat_count < 3:
            print(f"\n{name} hash={hash_val:#018x} size={sz}")
            for off in range(0, min(96, len(mat_data)), 16):
                hex_str = " ".join(f"{b:02x}" for b in mat_data[off:off+16])
                ascii_str = "".join(chr(b) if 32 <= b < 127 else "." for b in mat_data[off:off+16])
                print(f"  {off:04x}: {hex_str:<48} {ascii_str}")
        mat_count += 1

print(f"\nTotal MAT entries: {mat_count}")

# Find TX_ entries
print("\n=== TX entries (first 10) ===")
tx_count = 0
tx_hashes = []
for i in range(ec):
    o = 64 + 144 * i
    name = data[o+24:o+104].split(b"\x00")[0].decode("ascii", errors="replace")
    t108 = data[o+108]
    t109 = data[o+109]
    b111 = data[o+111]
    if name.startswith("TX_"):
        sz = struct.unpack_from("<I", data, o+4)[0]
        hash_val = struct.unpack_from("<Q", data, o+8)[0]
        
        if tx_count < 10:
            print(f"  {name[:65]:<65} t108={t108:#x} b111={b111} entry_hash={hash_val:#018x} size={sz}")
        tx_count += 1

print(f"\nTotal TX entries: {tx_count}")

# Now check: do the TX_ names contain hashes that match DDS filenames?
# TX_wraplod_rkyrock_med_06_normal_031C4864F2469A3A
# The hash part: 031C4864F2469A3A -> is this the DDS filename?
print("\n=== Checking TX name hash vs DDS filenames ===")
import glob
dds_files = glob.glob(r"D:\God of War Ragnarok_extracted\models\alfheim\textures\**\*.dds", recursive=True)
dds_names = set(os.path.basename(f).replace(".dds","") for f in dds_files)
print(f"Total DDS files in alfheim: {len(dds_files)}")

# Check first 20 TX entries
matched = 0
checked = 0
for i in range(ec):
    o = 64 + 144 * i
    name = data[o+24:o+104].split(b"\x00")[0].decode("ascii", errors="replace")
    if name.startswith("TX_"):
        # Extract hash from name - last part after last underscore
        parts = name.split("_")
        hash_str = parts[-1]
        if len(hash_str) >= 16:
            hash_upper = hash_str.upper()
            checked += 1
            if hash_upper in dds_names:
                matched += 1
                if matched <= 5:
                    print(f"  MATCH: {name[:50]} -> {hash_upper}.dds")
        if checked >= 100:
            break

print(f"\nChecked {checked} TX entries, matched {matched} to DDS files")