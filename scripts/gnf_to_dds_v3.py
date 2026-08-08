"""
GNF -> DDS converter v3 for GoW Ragnarok PC textures.
VERIFIED padding rules:
  - Single-mip blocks: width padded to next multiple of 32
  - Multi-mip blocks: ref dims = next pow2, per-mip blocks aligned to 8 (min 8), total aligned to 16
  - Data layout: mip-major (all slices for mip N, then all slices for mip N+1)
  - PC GNF: magic=0x20464E47, arraySize=4, data is linear (no Morton swizzle)
  - BC6H: depth=6, treated as arraySize=24 (4 arrays * 6 cube faces)
"""
import struct, os, sys, math, time

PC_FMT_MAP = {
    0x29: (71,  4, 4, 8,  "BC1_TYPELESS"),
    0x2A: (72,  4, 4, 8,  "BC1_UNORM_SRGB"),
    0x2F: (80,  4, 4, 8,  "BC4_TYPELESS"),
    0x30: (81,  4, 4, 8,  "BC4_UNORM_SNORM"),
    0x33: (95,  8, 4, 16, "BC6H_TYPELESS_UF16"),
    0x34: (96,  8, 4, 16, "BC6H_TYPELESS_SF16"),
    0x35: (98,  8, 4, 16, "BC7_TYPELESS"),
    0x36: (99,  8, 4, 16, "BC7_UNORM_SRGB"),
}

def parse_gnf_header(data):
    if len(data) < 0x100: return None
    magic = struct.unpack_from("<I", data, 0)[0]
    if magic != 0x20464E47: return None
    fmt_field = struct.unpack_from("<I", data, 20)[0]
    dim_field = struct.unpack_from("<I", data, 24)[0]
    mip_field = struct.unpack_from("<I", data, 28)[0]
    dp_field  = struct.unpack_from("<I", data, 32)[0]
    data_size = struct.unpack_from("<I", data, 44)[0]
    fmt     = (fmt_field >> 20) & 0x3F
    width   = (dim_field & 0x3FFF) + 1
    height  = ((dim_field >> 14) & 0x3FFF) + 1
    mips    = ((mip_field >> 16) & 0xF) + 1
    depth   = (dp_field & 0x1FFF) + 1
    return dict(magic=magic, fmt=fmt, width=width, height=height,
                mips=mips, depth=depth, data_size=data_size)

def next_pow2(x):
    p = 1
    while p < x: p <<= 1
    return p

def block_count(w, pixbl):
    return max(1, (w + pixbl - 1) // pixbl)

def mip_dims(w, h, idx):
    return max(1, w >> idx), max(1, h >> idx)

def padded_width_m32(w):
    """Pad width to next multiple of 32 (for single-mip blocks)."""
    return ((w + 31) // 32) * 32

def unpad_rows(src_data, actual_bw, padded_bw, bh, blkbytes):
    """Remove width padding from block-compressed data."""
    if actual_bw == padded_bw:
        return src_data[:actual_bw * bh * blkbytes]
    row_src = padded_bw * blkbytes
    row_dst = actual_bw * blkbytes
    out = bytearray(actual_bw * bh * blkbytes)
    for row in range(bh):
        src_off = row * row_src
        dst_off = row * row_dst
        out[dst_off:dst_off+row_dst] = src_data[src_off:src_off+row_dst]
    return bytes(out)

def build_dds_header(W, H, n_mips, dxgi_fmt, array_size, is_cube=False):
    """Build DDS header with DX10 extension."""
    magic = b"DDS "
    flags = 0x1 | 0x2 | 0x4 | 0x1000 | 0x20000 | 0x80000  # CAPS|HEIGHT|WIDTH|PIXELFORMAT|MIPMAPCOUNT|LINEARSIZE
    caps = 0x1000 | 0x8 | 0x400000  # TEXTURE|COMPLEX|MIPMAP
    
    pf_flags = 0x4  # DDPF_FOURCC
    pf_fourcc = b"DX10"
    
    header = struct.pack("<7I", 124, flags, H, W, 0, 0, n_mips)  # dwSize,flags,H,W,pitch,depth,mipcount
    header += struct.pack("<11I", 0,0,0,0,0,0,0,0,0,0,0)  # reserved[11] = 44 bytes
    # pixel format (32 bytes)
    header += struct.pack("<2I", 32, pf_flags)
    header += pf_fourcc
    header += struct.pack("<5I", 0,0,0,0,0)
    # caps
    header += struct.pack("<5I", caps, 0, 0, 0, 0)
    
    # DX10 header (20 bytes)
    misc_flag = 0x4 if is_cube else 0  # DDS_RESOURCE_MISC_TEXTURECUBE
    dx10 = struct.pack("<IIIHH", dxgi_fmt, 3, misc_flag, array_size, 0)  # 16 bytes
    dx10 += struct.pack("<I", 0)  # miscFlags2
    
    return magic + header + dx10

class Texpack:
    def __init__(self, filepath):
        self.fs = open(filepath, "rb")
        data = self.fs.read(0x40)
        self.texSectionOff, self.blocksCount, self.blocksInfoOff, self.TexsCount = \
            struct.unpack_from("<IIII", data, 0x20)
        self.fs.seek(0x38)
        self.texInfos = []
        for i in range(self.TexsCount):
            fh, uh, bo = struct.unpack("<QQQ", self.fs.read(24))
            self.texInfos.append((fh, uh, bo))
        self.fs.seek(self.blocksInfoOff)
        self.blockInfos = []
        self.blockInfoOffsets = []
        for i in range(self.blocksCount):
            off = self.fs.tell()
            self.blockInfoOffsets.append(off)
            raw = self.fs.read(32)
            blockOff, rawSize = struct.unpack_from("<II", raw, 0)
            blockSize = struct.unpack_from("<Q", raw, 8)[0]
            mipStart, mipEnd = raw[16], raw[17]
            tocIdx, mipW, mipH = struct.unpack_from("<HHH", raw, 18)
            nextSib = struct.unpack_from("<Q", raw, 24)[0]
            self.blockInfos.append(dict(off=off, blockOff=blockOff, rawSize=rawSize,
                blockSize=blockSize, mipStart=mipStart, mipEnd=mipEnd,
                tocIdx=tocIdx, mipW=mipW, mipH=mipH, nextSib=nextSib))
        self.boMap = {off: i for i, off in enumerate(self.blockInfoOffsets)}

    def get_block_chain(self, tex_info_idx):
        fh, uh, bo = self.texInfos[tex_info_idx]
        idx = self.boMap.get(bo)
        if idx is None: return None
        chain = [self.blockInfos[idx]]
        while chain[0]["nextSib"] != 0xFFFFFFFFFFFFFFFF:
            ns = chain[0]["nextSib"]
            ni = self.boMap.get(ns)
            if ni is None: break
            chain.insert(0, self.blockInfos[ni])
        return chain

    def read_block_data(self, block):
        base = (block["blockOff"] << 4) + 4
        self.fs.seek(base)
        off_val = struct.unpack("<I", self.fs.read(4))[0]
        ln_val = struct.unpack("<I", self.fs.read(4))[0]
        self.fs.read(4)
        header = None
        if off_val != 0x20:
            header = self.fs.read(0x100)
            self.fs.read(4)
        self.fs.read(8)
        decSize = struct.unpack("<I", self.fs.read(4))[0]
        self.fs.read(4)
        data = self.fs.read(decSize)
        return header, data

    def export_texture(self, tex_info_idx):
        chain = self.get_block_chain(tex_info_idx)
        if chain is None: return None, None
        gnf_header = None
        block_data_list = []
        for b in chain:
            hdr, d = self.read_block_data(b)
            if gnf_header is None and hdr is not None:
                gnf_header = hdr
            block_data_list.append((b, d))
        return gnf_header, block_data_list

    def close(self):
        self.fs.close()


def gnf_to_dds(gnf_header, block_data_list, out_path):
    h = parse_gnf_header(gnf_header)
    if h is None: return False, "bad GNF header"
    if h["fmt"] not in PC_FMT_MAP: return False, f"unsupported fmt 0x{h['fmt']:02X}"
    
    dxgi, bpp, pixbl, blkbytes, fmt_name = PC_FMT_MAP[h["fmt"]]
    W, H, n_mips = h["width"], h["height"], h["mips"]
    depth = h["depth"]
    
    # Determine array_size
    if depth == 6:
        array_size = 4  # 4 texture arrays
        n_faces = 6    # 6 cube faces per array
        is_cube = True
    else:
        array_size = 4
        n_faces = 1
        is_cube = False
    
    total_slices = array_size * n_faces
    
    # Compute per-mip info for each block
    # Each block covers a range of mips. We need to map mip indices to block data.
    mip_to_block = {}  # mip_idx -> (block_idx, offset_within_block, per_slice_size, actual_bw, padded_bw, bh)
    
    for bi, (block, bdata) in enumerate(block_data_list):
        actual_mip_start = (n_mips - 1) - block["mipStart"]
        actual_mip_end = (n_mips - 1) - block["mipEnd"]
        is_single = (actual_mip_start == actual_mip_end)
        
        if is_single:
            # Single-mip block: width padded to next multiple of 32
            m = actual_mip_start
            mw, mh = mip_dims(W, H, m)
            actual_bw = block_count(mw, pixbl)
            actual_bh = block_count(mh, pixbl)
            padded_w = padded_width_m32(mw)
            padded_bw = block_count(padded_w, pixbl)
            per_slice_sz = padded_bw * actual_bh * blkbytes
            per_mip_sz = per_slice_sz * total_slices
            
            if len(bdata) < per_mip_sz:
                return False, f"block {bi} mip {m}: data too short ({len(bdata)} < {per_mip_sz})"
            
            mip_to_block[m] = (bi, 0, per_slice_sz, actual_bw, padded_bw, actual_bh)
        else:
            # Multi-mip block: ref dims = next pow2, per-mip blocks aligned to 8, total aligned to 16
            ref_w = next_pow2(W)
            ref_h = next_pow2(H)
            
            # Compute per-mip padded block counts
            mip_blocks = []
            for m in range(actual_mip_start, actual_mip_end + 1):
                rfm, rfh = mip_dims(ref_w, ref_h, m)
                ref_blocks = block_count(rfm, pixbl) * block_count(rfh, pixbl)
                padded_blocks = max(8, ((ref_blocks + 7) // 8) * 8)
                mip_blocks.append((m, padded_blocks))
            
            # Align total to 16
            total_blocks = sum(b for _, b in mip_blocks)
            total_aligned = ((total_blocks + 15) // 16) * 16
            extra = total_aligned - total_blocks
            if extra > 0:
                # Add extra to last mip
                last_m, last_b = mip_blocks[-1]
                mip_blocks[-1] = (last_m, last_b + extra)
            
            # Compute offsets within block data
            offset = 0
            for m, padded_blocks in mip_blocks:
                mw, mh = mip_dims(W, H, m)
                actual_bw = block_count(mw, pixbl)
                actual_bh = block_count(mh, pixbl)
                
                rfm, rfh = mip_dims(ref_w, ref_h, m)
                ref_bw = block_count(rfm, pixbl)
                ref_bh = block_count(rfh, pixbl)
                
                per_slice_sz = padded_blocks * blkbytes
                per_mip_sz = per_slice_sz * total_slices
                
                if offset + per_mip_sz > len(bdata) + 1:
                    return False, f"block {bi} mip {m}: offset overflow ({offset+per_mip_sz} > {len(bdata)})"
                
                mip_to_block[m] = (bi, offset, per_slice_sz, actual_bw, ref_bw, actual_bh)
                offset += per_mip_sz
            
            # Verify total
            expected_total = total_aligned * blkbytes * total_slices
            if expected_total != block["rawSize"]:
                # Warning but continue
                pass
    
    # Build DDS
    dds_header = build_dds_header(W, H, n_mips, dxgi, array_size, is_cube)
    if dds_header is None:
        return False, "failed to build DDS header"
    
    out_data = bytearray(dds_header)
    
    # DDS data layout: for each array element, for each face, for each mip
    # For cube maps: arraySize * 6 faces, for 2D: arraySize * 1
    for arr_idx in range(array_size):
        for face_idx in range(n_faces):
            slice_idx = arr_idx * n_faces + face_idx
            for mip_idx in range(n_mips):
                if mip_idx not in mip_to_block:
                    # Pad with zeros
                    mw, mh = mip_dims(W, H, mip_idx)
                    sz = block_count(mw, pixbl) * block_count(mh, pixbl) * blkbytes
                    out_data += b"\x00" * sz
                    continue
                
                bi, offset, per_slice_sz, actual_bw, padded_bw, bh = mip_to_block[mip_idx]
                block, bdata = block_data_list[bi]
                
                # Extract this slice's data
                start = offset + slice_idx * per_slice_sz
                end = start + per_slice_sz
                
                if end > len(bdata):
                    chunk = bdata[start:min(start, len(bdata))]
                    chunk = chunk + b"\x00" * (per_slice_sz - len(chunk))
                else:
                    chunk = bdata[start:end]
                
                # Unpad rows: extract actual_bw blocks per row from padded_bw blocks per row
                actual_slice_sz = actual_bw * bh * blkbytes
                if padded_bw != actual_bw:
                    unpadded = unpad_rows(chunk, actual_bw, padded_bw, bh, blkbytes)
                    out_data += unpadded[:actual_slice_sz]
                else:
                    out_data += chunk[:actual_slice_sz]
    
    with open(out_path, "wb") as f:
        f.write(out_data)
    
    return True, f"{fmt_name} {W}x{H} mips={n_mips} arr={array_size} cube={is_cube} ({len(out_data)} bytes)"


def extract_texpack(tp_path, out_dir, limit=None):
    tp = Texpack(tp_path)
    ok = 0; fail = 0; skip = 0
    errors = []
    n = tp.TexsCount if limit is None else min(limit, tp.TexsCount)
    for i in range(n):
        fh, uh, bo = tp.texInfos[i]
        gnf_header, block_data_list = tp.export_texture(i)
        if gnf_header is None:
            fail += 1; errors.append(f"[{i}] no GNF header"); continue
        h = parse_gnf_header(gnf_header)
        if h is None:
            fail += 1; errors.append(f"[{i}] bad GNF header"); continue
        if h["fmt"] not in PC_FMT_MAP:
            skip += 1; continue
        out_path = os.path.join(out_dir, f"{fh:016X}.dds")
        success, msg = gnf_to_dds(gnf_header, block_data_list, out_path)
        if success: ok += 1
        else: fail += 1; errors.append(f"[{i}] {fh:016X}: {msg}")
    tp.close()
    return ok, fail, skip, errors


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 3:
        tp_path = sys.argv[1]
        out_dir = sys.argv[2]
        limit = int(sys.argv[3]) if len(sys.argv) >= 4 else None
    else:
        tp_path = r"E:\God of War Ragnarok\exec\wad\pc_le\170_midgard10_postgame.texpack"
        out_dir = r"E:\gow_re_workspace\output\tex_dds_v3"
        limit = 30
    
    os.makedirs(out_dir, exist_ok=True)
    print(f"Extracting from {os.path.basename(tp_path)}...")
    t0 = time.time()
    ok, fail, skip, errors = extract_texpack(tp_path, out_dir, limit)
    elapsed = time.time() - t0
    print(f"OK={ok} FAIL={fail} SKIP={skip} time={elapsed:.1f}s")
    if errors:
        for e in errors[:10]:
            print(f"  ERR: {e}")