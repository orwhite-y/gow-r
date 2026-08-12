import lz4.frame, struct, os, re, json

PC_LE = r"E:\God of War Ragnarok\exec\wad\pc_le"
GNF_MAGIC = b"GNF "

with open(r"E:\gow_re_workspace\output\missing_tex_hashes.json","r") as f:
    missing = set(json.load(f))
with open(r"E:\gow_re_workspace\output\dds_index_complete.json","r") as f:
    dds_index = json.load(f)

def parse_wad(wad_path):
    with open(wad_path, "rb") as f:
        data = lz4.frame.decompress(f.read())
    ec = struct.unpack_from("<I", data, 8)[0]
    ds = 64 + 144 * ec
    cur = ds
    entries = []
    for i in range(ec):
        o = 64 + 144 * i
        word0 = struct.unpack_from("<H", data, o)[0]
        size = struct.unpack_from("<I", data, o+4)[0]
        name = data[o+24:o+104].split(b"\x00")[0].decode("ascii", errors="replace")
        t109 = data[o+109]
        b111 = data[o+111]
        align = struct.unpack_from("<I", data, o+104)[0]
        fo = cur
        if align > 0: fo = (fo + align - 1) & ~(align - 1)
        cur = fo + size
        entries.append({"idx": i, "word0": word0, "size": size,
                         "name": name, "t109": t109, "b111": b111, "fo": fo})
    return entries, data

# For each missing hash, look for TX references in the data
missing_resolved = {}  # missing_hash -> referenced_hash (found in DDS index)
missing_unresolved = set()

wads = [f for f in os.listdir(PC_LE) if f.endswith(".wad")]
for wf in wads:
    try:
        entries, data = parse_wad(os.path.join(PC_LE, wf))
        for e in entries:
            if not e["name"].startswith("TX_"): continue
            m = re.search(r'([0-9A-Fa-f]{16})$', e["name"])
            if not m or m.group(1).upper() not in missing: continue
            
            edata = data[e["fo"]:e["fo"]+e["size"]]
            own_hash = m.group(1).upper()
            
            # If already resolved, skip
            if own_hash in missing_resolved: continue
            
            # Search for TX_ references in the data (format: TX_name_HASHHEX)
            tx_refs = re.findall(rb'TX_[A-Za-z0-9_\.]*_([0-9A-Fa-f]{16})', edata)
            for ref in tx_refs:
                ref_hash = ref.decode().upper()
                if ref_hash != own_hash and ref_hash in dds_index:
                    missing_resolved[own_hash] = ref_hash
                    break
            
            if own_hash not in missing_resolved:
                # Also search for bare 16-hex-char strings
                hex_refs = re.findall(rb'([0-9A-Fa-f]{16})', edata)
                for ref in hex_refs:
                    ref_hash = ref.decode().upper()
                    if ref_hash != own_hash and ref_hash in dds_index:
                        missing_resolved[own_hash] = ref_hash
                        break
            
            if own_hash not in missing_resolved:
                missing_unresolved.add(own_hash)
    except:
        pass

print(f"Missing hashes total: {len(missing)}")
print(f"Resolved via reference: {len(missing_resolved)}")
print(f"Still unresolved: {len(missing_unresolved)}")

# Show some resolved examples
print(f"\nSample resolved:")
for mh, rh in list(missing_resolved.items())[:10]:
    print(f"  {mh} -> {rh}")

# Show some unresolved
print(f"\nSample unresolved:")
for mh in sorted(list(missing_unresolved))[:10]:
    print(f"  {mh}")

# Save resolution map
with open(r"E:\gow_re_workspace\output\tex_ref_resolution.json","w") as f:
    json.dump(missing_resolved, f, indent=2)
print(f"\nResolution map saved.")