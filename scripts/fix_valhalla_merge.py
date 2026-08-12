import os, shutil, json

base_dir = r"D:\God of War Ragnarok_extracted\models\base"
valhalla_dir = r"D:\God of War Ragnarok_extracted\models\valhalla"

# Get all val_* dirs in base
base_val_dirs = []
for name in os.listdir(base_dir):
    full = os.path.join(base_dir, name)
    if os.path.isdir(full) and name.startswith("val_"):
        base_val_dirs.append(name)

print(f"Found {len(base_val_dirs)} val_* dirs in base")

merged = 0
no_dest = 0
deleted = 0

for name in base_val_dirs:
    src = os.path.join(base_dir, name)
    dest = os.path.join(valhalla_dir, name)
    
    if not os.path.isdir(dest):
        print(f"  NO DEST: {name}")
        no_dest += 1
        continue
    
    # Move materials\ folder if dest doesn't have it
    src_mat = os.path.join(src, "materials")
    dest_mat = os.path.join(dest, "materials")
    if os.path.isdir(src_mat) and not os.path.isdir(dest_mat):
        shutil.move(src_mat, dest_mat)
    
    # Move mat_index.json if dest doesn't have it
    src_mi = os.path.join(src, "mat_index.json")
    dest_mi = os.path.join(dest, "mat_index.json")
    if os.path.isfile(src_mi) and not os.path.isfile(dest_mi):
        shutil.move(src_mi, dest_mi)
    
    # material_mapping.json - keep the larger one
    src_map = os.path.join(src, "material_mapping.json")
    dest_map = os.path.join(dest, "material_mapping.json")
    if os.path.isfile(src_map):
        if not os.path.isfile(dest_map):
            shutil.move(src_map, dest_map)
        else:
            src_size = os.path.getsize(src_map)
            dest_size = os.path.getsize(dest_map)
            if src_size > dest_size:
                os.remove(dest_map)
                shutil.move(src_map, dest_map)
    
    # Merge textures - move only missing files
    src_tex = os.path.join(src, "textures")
    dest_tex = os.path.join(dest, "textures")
    if os.path.isdir(src_tex):
        if not os.path.isdir(dest_tex):
            shutil.move(src_tex, dest_tex)
        else:
            for tf in os.listdir(src_tex):
                src_file = os.path.join(src_tex, tf)
                dest_file = os.path.join(dest_tex, tf)
                if os.path.isfile(src_file) and not os.path.exists(dest_file):
                    shutil.move(src_file, dest_file)
            # Remove empty textures dir
            try:
                os.rmdir(src_tex)
            except:
                pass
    
    # Check if src dir is now empty (only has leftover files), try to remove
    remaining = os.listdir(src)
    if not remaining:
        os.rmdir(src)
        deleted += 1
    else:
        # Force remove remaining files and dir
        for f in remaining:
            fp = os.path.join(src, f)
            if os.path.isfile(fp):
                os.remove(fp)
            elif os.path.isdir(fp):
                shutil.rmtree(fp, ignore_errors=True)
        try:
            os.rmdir(src)
            deleted += 1
        except Exception as e:
            print(f"  Could not remove {name}: {e}")
    
    merged += 1

print(f"Merged: {merged}, No dest: {no_dest}, Deleted base dirs: {deleted}")