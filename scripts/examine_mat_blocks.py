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

# Build MAT name hash set
mat_by_name_hash = {}
for e in entries:
    if e["name"].startswith("MAT_") and e["t109"] == 0x0a:
        try:
            nh = int(e["name"][4:], 16)
            mat_by_name_hash[nh] = e
        except: pass

# === Show complete entry sequence around MAT definitions ===
print("=== Complete entry sequence around MAT definitions ===")
mat_defs = [e for e in entries if e["name"].startswith("MAT_") and e["t109"] == 0x0a]

# Show first 3 MAT definition blocks with ALL following entries
for mi in range(3):
    me = mat_defs[mi]
    print(f"\n--- MAT block starting at entry {me['idx']} ---")
    # Show all entries from this MAT def until next MAT def (max 20)
    for j in range(me["idx"], min(me["idx"]+20, ec)):
        e = entries[j]
        edata_preview = ""
        if e["size"] > 0 and e["size"] < 500:
            edata = data[e["fo"]:e["fo"]+min(e["size"], 48)]
            edata_preview = " ".join(f"{b:02x}" for b in edata[:24])
        
        marker = ""
        if e["name"].startswith("MAT_") and e["t109"] == 0x0a:
            marker = " <<< MAT DEF"
        elif e["name"].startswith("TX_"):
            marker = " <<< TX"
        
        print(f"  [{j:5d}] w{e['word0']:<3} t{e['t109']:02x} b{e['b111']} sz={e['size']:<6} {e['name'][:45]:<45} {edata_preview}{marker}")
        
        # Stop at next MAT def (if not the first entry)
        if j > me["idx"] and e["name"].startswith("MAT_") and e["t109"] == 0x0a:
            break

# === Examine w1_t01_b0 entries (texture slot references?) ===
print("\n\n=== w1_t01_b0 entries after MAT defs ===")
count = 0
for me in mat_defs:
    for j in range(me["idx"]+1, min(me["idx"]+20, ec)):
        ne = entries[j]
        if ne["name"].startswith("MAT_") and ne["t109"] == 0x0a:
            break
        if ne["word0"] == 1 and ne["t109"] == 0x01 and ne["b111"] == 0:
            if count < 5:
                edata = data[ne["fo"]:ne["fo"]+min(ne["size"], 128)]
                print(f"\n  Entry {ne['idx']}: {ne['name'][:45]} size={ne['size']}")
                # Show hex + search for MAT hashes
                for off in range(0, min(128, len(edata)), 16):
                    hex_str = " ".join(f"{b:02x}" for b in edata[off:off+16])
                    ascii_str = "".join(chr(b) if 32 <= b < 127 else "." for b in edata[off:off+16])
                    print(f"    {off:04x}: {hex_str:<48} {ascii_str}")
                # Check for MAT name hashes
                for off in range(0, len(edata)-7, 4):
                    v = struct.unpack_from("<Q", edata, off)[0]
                    if v in mat_by_name_hash:
                        print(f"    *** MAT hash @{off:#06x}: {mat_by_name_hash[v]['name']}")
            count += 1
            break  # Only first w1_t01 per MAT

print(f"\nTotal w1_t01_b0 entries after MAT defs: {count}")

# === Examine w60_t00_b8 entries ===
print("\n\n=== w60_t00_b8 entries ===")
count = 0
for e in entries:
    if e["word0"] == 60 and e["t109"] == 0x00 and e["b111"] == 8:
        if count < 3:
            edata = data[e["fo"]:e["fo"]+min(e["size"], 128)]
            print(f"\n  Entry {e['idx']}: {e['name'][:50]} size={e['size']}")
            for off in range(0, min(128, len(edata)), 16):
                hex_str = " ".join(f"{b:02x}" for b in edata[off:off+16])
                ascii_str = "".join(chr(b) if 32 <= b < 127 else "." for b in edata[off:off+16])
                print(f"    {off:04x}: {hex_str:<48} {ascii_str}")
            # Check for MAT name hashes
            for off in range(0, len(edata)-7, 4):
                v = struct.unpack_from("<Q", edata, off)[0]
                if v in mat_by_name_hash:
                    print(f"    *** MAT hash @{off:#06x}: {mat_by_name_hash[v]['name']}")
        count += 1

print(f"\nTotal w60_t00_b8 entries: {count}")