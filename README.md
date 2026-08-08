# GoW Ragnarok - Model & Texture Extraction Tools

Reverse-engineered extraction pipeline for God of War Ragnarok WAD files.

## Contents

- `scripts/` - Extraction & conversion scripts
  - `extract_all_glb_v55.py` - WAD -> GLB model extractor (127K+ models)
  - `gnf_to_dds_v3.py` - GNF -> DDS texture converter
  - `batch_extract_textures.py` - Batch texture extraction
  - `copy_glb_stage2_ssd_to_hdd.py` - Two-stage GLB copy (SSD->HDD)
  - `reorganize_textures.py` - Reorganize textures to region hierarchy
  - `run_full_extract.py` - One-click full pipeline
  - `validate_trimesh.py` - GLB validation via trimesh
  - `mcp_ida_client.py` - IDA MCP client
  - `ida_write_comments_v2.py` - Write IDA comments
  - `compress_all_regions.ps1` - 7z region compression
- `static_analysis/` - Decompiled reference code (WAD format, mesh pipeline)
- `MEMORY.md` - Progress log & key findings
- `TOOLS.md` - Tool inventory
- `format.txt` - Early WAD format reference

## Stats

- 127,554 GLB models extracted (1,340,761 meshes, 100% success)
- 64,147 DDS textures extracted (98.7% success)
- 13 regions, 992 WAD directories
- Compressed: 146.77 GB -> 59.61 GB (40.6% ratio)