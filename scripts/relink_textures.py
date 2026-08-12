#!/usr/bin/env python3
"""
GoW Ragnarok Model Extractor - Texture Relink Script

Usage:
  1. Extract all region archives into the same parent directory
  2. Extract textures.7z into a "textures" subdirectory
  3. Run: python relink_textures.py <models_dir> <textures_dir>

This script reads material_mapping.json files and creates hard links
(or copies on non-NTFS) from the global textures directory to each
WAD's local textures directory.

Example:
  python relink_textures.py "D:\extracted\models" "D:\extracted\textures"
"""
import os, sys, json, shutil

def main():
    if len(sys.argv) < 3:
        print("Usage: python relink_textures.py <models_dir> <textures_dir>")
        print("Example: python relink_textures.py D:\\extracted\\models D:\\extracted\\textures")
        sys.exit(1)
    
    models_dir = os.path.abspath(sys.argv[1])
    textures_dir = os.path.abspath(sys.argv[2])
    
    if not os.path.isdir(models_dir):
        print(f"ERROR: models dir not found: {models_dir}")
        sys.exit(1)
    if not os.path.isdir(textures_dir):
        print(f"ERROR: textures dir not found: {textures_dir}")
        sys.exit(1)
    
    # Build index of available DDS files
    print("Indexing texture files...")
    dds_files = {}  # hash -> path
    for f in os.listdir(textures_dir):
        if f.endswith('.dds'):
            h = f[:-4]
            dds_files[h] = os.path.join(textures_dir, f)
    print(f"Found {len(dds_files)} unique DDS files")
    
    # Walk all WAD directories
    total_linked = 0
    total_copied = 0
    total_missing = 0
    regions_processed = 0
    
    for region in sorted(os.listdir(models_dir)):
        rpath = os.path.join(models_dir, region)
        if not os.path.isdir(rpath):
            continue
        regions_processed += 1
        
        for wad in sorted(os.listdir(rpath)):
            wpath = os.path.join(rpath, wad)
            if not os.path.isdir(wpath):
                continue
            if wad == "textures":
                continue
            
            map_file = os.path.join(wpath, "material_mapping.json")
            if not os.path.isfile(map_file):
                continue
            
            try:
                with open(map_file, 'r') as f:
                    mapping = json.load(f)
            except:
                continue
            
            tex_dir = os.path.join(wpath, "textures")
            os.makedirs(tex_dir, exist_ok=True)
            
            # Collect needed DDS hashes
            needed = set()
            for mesh_entry in mapping.get("meshes", []):
                for tex in mesh_entry.get("textures", []):
                    dds_hash = tex.get("dds_hash", "") or tex.get("hash", "")
                    if dds_hash:
                        needed.add(dds_hash)
            
            # Create links
            for h in needed:
                dest = os.path.join(tex_dir, h + ".dds")
                if os.path.exists(dest):
                    continue
                if h in dds_files:
                    src = dds_files[h]
                    try:
                        os.link(src, dest)  # Try hard link first
                        total_linked += 1
                    except OSError:
                        try:
                            shutil.copy2(src, dest)  # Fallback to copy
                            total_copied += 1
                        except:
                            total_missing += 1
                    except:
                        total_missing += 1
                else:
                    total_missing += 1
        
        print(f"  Processed region: {region}")
    
    print(f"\nDone!")
    print(f"  Hard links created: {total_linked}")
    print(f"  Files copied: {total_copied}")
    print(f"  Missing textures: {total_missing} (runtime-generated, not in files)")
    print(f"  Regions processed: {regions_processed}")

if __name__ == "__main__":
    main()