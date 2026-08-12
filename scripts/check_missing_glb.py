import os, json

# Check material_mapping.json
d = r"D:\God of War Ragnarok_extracted\models\base\c_190_ironwoodarrival"
with open(os.path.join(d, "material_mapping.json"), "r") as f:
    m = json.load(f)
print(f"WAD: {m.get('wad','?')}")
print(f"Region: {m.get('region','?')}")
meshes = m.get("meshes", [])
print(f"Mesh entries in mapping: {len(meshes)}")
if meshes:
    for me in meshes[:10]:
        print(f"  mesh={me.get('mesh','?')} idx={me.get('idx',0)}")

# Check WAD file for mesh entries
wad_path = r"E:\God of War Ragnarok\exec\wad\pc_le\c_190_ironwoodarrival.wad"
print(f"\nWAD file: {wad_path} ({os.path.getsize(wad_path)/1e6:.1f}MB)")

# Decompress WAD and check TOC for MESH entries
import lz4.frame
import struct

with open(wad_path, "rb") as f:
    wad_data = f.read()

# Try LZ4 decompress
try:
    decompressed = lz4.frame.decompress(wad_data)
    print(f"Decompressed: {len(decompressed)} bytes")
    
    # Parse header (64 bytes)
    header = decompressed[:64]
    # TOC count is usually at offset 0 or nearby
    # Based on prior RE: 64B header + N*144B TOC entries
    # Try to find TOC count
    toc_count = struct.unpack_from("<I", decompressed, 0)[0]
    print(f"TOC count (from offset 0): {toc_count}")
    
    # Also check other possible offsets
    for off in [0, 4, 8, 12, 16, 20, 24, 28, 32]:
        val = struct.unpack_from("<I", decompressed, off)[0]
        if 1 < val < 10000:
            print(f"  Possible TOC count at +{off}: {val}")
    
    # Parse TOC entries (144 bytes each)
    mesh_count = 0
    mat_count = 0
    tx_count = 0
    other_count = 0
    
    # Try different TOC start offsets
    for toc_start in [64, 48, 32]:
        entries = []
        for off in [0, 4, 8, 12, 16, 20, 24, 28, 32]:
            tc = struct.unpack_from("<I", decompressed, off)[0]
            if 1 < tc < 10000:
                toc_count = tc
                break
        
        for i in range(min(toc_count, 500)):
            entry_off = toc_start + i * 144
            if entry_off + 144 > len(decompressed):
                break
            word0 = struct.unpack_from("<I", decompressed, entry_off + 0)[0]
            name_bytes = decompressed[entry_off+24:entry_off+104]
            name = name_bytes.split(b'\x00')[0].decode('ascii', errors='replace')
            t109 = decompressed[entry_off+109] if entry_off+109 < len(decompressed) else 0
            
            if name.startswith("MESH"):
                mesh_count += 1
                if mesh_count <= 5:
                    entries.append(f"  MESH: {name} word0={word0} t109={t109:#x}")
            elif name.startswith("MAT"):
                mat_count += 1
            elif name.startswith("TX"):
                tx_count += 1
            else:
                other_count += 1
        
        if mesh_count > 0 or mat_count > 0 or tx_count > 0:
            print(f"\nTOC at offset {toc_start}:")
            print(f"  MESH: {mesh_count}, MAT: {mat_count}, TX: {tx_count}, Other: {other_count}")
            for e in entries:
                print(e)
            break

except Exception as e:
    print(f"LZ4 decompress failed: {e}")
    # Try without LZ4
    print("First 64 bytes:", wad_data[:64].hex())