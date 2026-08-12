import struct, lz4.frame, os, re

PC_LE = r"E:\God of War Ragnarok\exec\wad\pc_le"
wad_name = "alf_bluff100_entrance.wad"

with open(os.path.join(PC_LE, wad_name), "rb") as f:
    data = lz4.frame.decompress(f.read())

ec = struct.unpack_from("<I", data, 8)[0]
ds = 64 + 144 * ec

entries = []
cur = ds
for i in range(ec):
    o = 64 + 144 * i
    word0 = struct.unpack_from("<H", data, o)[0]
    size = struct.unpack_from("<I", data, o+4)[0]
    hash_val = struct.unpack_from("<Q", data, o+8)[0]
    name = data[o+24:o+104].split(b"\x00")[0].decode("ascii", errors="replace")
    t109 = data[o+109]
    b111 = data[o+111]
    align = struct.unpack_from("<I", data, o+104)[0]
    fo = cur
    if align > 0: fo = (fo + align - 1) & ~(align - 1)
    cur = fo + size
    entries.append({"idx": i, "word0": word0, "size": size, "hash": hash_val,
                     "name": name, "t109": t109, "b111": b111, "fo": fo})

# Collect ALL DDS hashes from TX entries (from name suffix)
all_dds_hashes = set()
tx_data_entries = []  # word0=29, t109=0x19 (actual texture data)
for e in entries:
    if e["name"].startswith("TX_"):
        m = re.search(r'([0-9A-Fa-f]{16})$', e["name"])
        if m:
            all_dds_hashes.add(int(m.group(1), 16))
            if e["word0"] == 29:
                tx_data_entries.append(e)

print(f"Total unique DDS hashes from TX names: {len(all_dds_hashes)}")
print(f"TX data entries (word0=29): {len(tx_data_entries)}")

# === Check word0=60 TX entries for embedded DDS hashes ===
print("\n=== word0=60 TX entries: searching for embedded DDS hashes ===")
w60_tx = [e for e in entries if e["name"].startswith("TX_") and e["word0"] == 60]
print(f"Total word0=60 TX entries: {len(w60_tx)}")

multi_match = 0
single_match = 0
zero_match = 0

for te in w60_tx:
    edata = data[te["fo"]:te["fo"]+te["size"]]
    
    # Get the DDS hash from the entry's own name
    m = re.search(r'([0-9A-Fa-f]{16})$', te["name"])
    own_hash = int(m.group(1), 16) if m else 0
    
    # Search for ALL DDS hashes in the data
    found = []
    for off in range(0, len(edata)-7, 4):
        v = struct.unpack_from("<Q", edata, off)[0]
        if v in all_dds_hashes and v != 0:
            found.append((off, v))
    
    # Deduplicate
    found_hashes = list(set(v for _, v in found))
    
    if len(found_hashes) > 1:
        multi_match += 1
        if multi_match <= 5:
            print(f"\n  {te['name'][:55]} size={te['size']}")
            print(f"    Own DDS hash: {own_hash:016X}")
            print(f"    Found {len(found_hashes)} DDS hashes in data:")
            for off, v in sorted(found)[:10]:
                # Find the TX data entry name for this hash
                tx_name = "?"
                for tde in tx_data_entries:
                    m2 = re.search(r'([0-9A-Fa-f]{16})$', tde["name"])
                    if m2 and int(m2.group(1), 16) == v:
                        tx_name = tde["name"][:40]
                        break
                print(f"      @{off:#06x}: {v:016X} -> {tx_name}")
    elif len(found_hashes) == 1:
        single_match += 1
    else:
        zero_match += 1

print(f"\nResults: multi={multi_match}, single={single_match}, zero={zero_match}")

# === Also check: does the MAT data itself contain DDS hashes? ===
print("\n\n=== MAT data: searching for DDS hashes ===")
mat_defs = [e for e in entries if e["name"].startswith("MAT_") and e["t109"] == 0x0a]
mat_with_dds = 0
for me in mat_defs[:100]:
    edata = data[me["fo"]:me["fo"]+me["size"]]
    for off in range(0, len(edata)-7, 4):
        v = struct.unpack_from("<Q", edata, off)[0]
        if v in all_dds_hashes:
            mat_with_dds += 1
            if mat_with_dds <= 3:
                print(f"  {me['name']} -> DDS hash @{off:#06x}: {v:016X}")
            break

print(f"MAT defs with DDS hash (first 100): {mat_with_dds}")

# === Check if word0=60 TX entries have structured format ===
print("\n\n=== word0=60 TX entry structure analysis ===")
# Look at the first 32 bytes as u32 values
for te in w60_tx[:5]:
    edata = data[te["fo"]:te["fo"]+min(te["size"], 64)]
    print(f"\n  {te['name'][:55]} size={te['size']}")
    # Show as u32 array
    u32s = [struct.unpack_from("<I", edata, i)[0] for i in range(0, min(32, len(edata)), 4)]
    print(f"    u32[0:8]: {' '.join(f'{v:08x}' for v in u32s)}")
    # Show as floats
    floats = [struct.unpack_from("<f", edata, i)[0] for i in range(0, min(32, len(edata)), 4)]
    print(f"    f32[0:8]: {' '.join(f'{v:.4f}' for v in floats)}")