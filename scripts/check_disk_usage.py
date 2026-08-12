import os, ctypes
from ctypes import wintypes

MODELS_DIR = r"D:\God of War Ragnarok_extracted\models"

# Use Windows API to get file IDs and detect hard links
kernel32 = ctypes.windll.kernel32

def get_file_id(path):
    """Get unique file identifier (volume + file ID) to detect hard links"""
    handle = kernel32.CreateFileW(
        path, 0x80000000, 1, None, 3, 0x80, None  # OPEN_EXISTING, FILE_FLAG_BACKUP_SEMANTICS
    )
    if handle == -1:
        return None
    try:
        info = wintypes.BY_HANDLE_FILE_INFORMATION()
        if kernel32.GetFileInformationByHandle(handle, ctypes.byref(info)):
            # (volume_serial, file_index_high, file_index_low)
            return (info.dwVolumeSerialNumber, info.nFileIndexHigh, info.nFileIndexLow)
    finally:
        kernel32.CloseHandle(handle)
    return None

# Check a few regions
for region in ["characters", "alfheim", "midgard"]:
    rpath = os.path.join(MODELS_DIR, region)
    if not os.path.isdir(rpath):
        continue
    
    reported_size = 0
    unique_ids = set()
    unique_size = 0
    file_count = 0
    hardlink_count = 0
    
    for root, dirs, files in os.walk(rpath):
        for f in files:
            fp = os.path.join(root, f)
            try:
                size = os.path.getsize(fp)
                reported_size += size
                file_count += 1
                
                fid = get_file_id(fp)
                if fid:
                    if fid not in unique_ids:
                        unique_ids.add(fid)
                        unique_size += size
                    else:
                        hardlink_count += 1
            except:
                pass
    
    print(f"{region:20s}: files={file_count:6d} reported={reported_size/1e9:.2f}GB unique={unique_size/1e9:.2f}GB hardlinks={hardlink_count:6d}")
    print(f"  {'':20s}  savings from dedup = {(reported_size-unique_size)/1e9:.2f}GB ({100*(reported_size-unique_size)/max(reported_size,1):.1f}%)")