#!/usr/bin/env python3
"""Validate GLB files with trimesh - check if they can actually be loaded and rendered."""
import trimesh
import os
import sys
import numpy as np

GLB_DIR = r"E:\gow_re_workspace\output\glb_test_v55"

glb_files = sorted([f for f in os.listdir(GLB_DIR) if f.endswith('.glb')])
print(f"Found {len(glb_files)} GLB files to validate\n")

for gf in glb_files:
    glb_path = os.path.join(GLB_DIR, gf)
    try:
        scene = trimesh.load(glb_path)
        if isinstance(scene, trimesh.Scene):
            geometries = scene.geometry
            print(f"=== {gf} ===")
            print(f"  Type: Scene with {len(geometries)} geometries")
            total_verts = 0
            total_faces = 0
            for name, mesh in geometries.items():
                v = len(mesh.vertices)
                f = len(mesh.faces)
                total_verts += v
                total_faces += f
                bbox_min = mesh.vertices.min(axis=0) if v > 0 else [0,0,0]
                bbox_max = mesh.vertices.max(axis=0) if v > 0 else [0,0,0]
                has_nan = np.any(np.isnan(mesh.vertices))
                has_inf = np.any(np.isinf(mesh.vertices))
                is_watertight = mesh.is_watertight if v > 0 else False
                print(f"    {name}: verts={v} faces={f} "
                      f"bbox=[{bbox_min[0]:.3f},{bbox_min[1]:.3f},{bbox_min[2]:.3f}]-"
                      f"[{bbox_max[0]:.3f},{bbox_max[1]:.3f},{bbox_max[2]:.3f}] "
                      f"nan={has_nan} inf={has_inf} watertight={is_watertight}")
            print(f"  Total: verts={total_verts} faces={total_faces}")
            print(f"  Scene bounds: {scene.bounds}")
        elif isinstance(scene, trimesh.Trimesh):
            print(f"=== {gf} ===")
            print(f"  Type: Trimesh")
            print(f"  Verts: {len(scene.vertices)} Faces: {len(scene.faces)}")
            print(f"  Bounds: {scene.bounds}")
            print(f"  Watertight: {scene.is_watertight}")
        else:
            print(f"=== {gf} ===")
            print(f"  Type: {type(scene).__name__}")
            print(f"  Loaded but unexpected type")
    except Exception as e:
        print(f"=== {gf} === ERROR: {e}")
        import traceback
        traceback.print_exc()
    print()