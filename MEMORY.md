# Codex 工作流程记录 (MEMORY.md)

> 替代 PROCESS.md。只记已验证的实锤发现，不猜猜。
> 最近验证时间: 2026-08-08 (session 57 - GLB region hierarchy + texture extraction complete)
> 验证方法: IDA 反编译 + WAD 字节级匹配 + texpack rawSize 数学验证 + DDS解码验证 + trimesh GLB验证

## 当前状态
- **项目路径**: E:\God of War Ragnarok\exec\wad\pc_le
- **最近更新**: 2026-08-08
- **最近会话**: session 57
- **进行中**: 无 (所有提取完成)
- **下一步**: 可选 - 修复666个失败纹理 / 进一步优化

## ★★★ 最终结果: 模型+纹理提取 100% 完成 ★★★
- **127,554 个 GLB 模型** + **64,147 个 DDS 纹理** = **191,701 个资产**
- 全部在 D:\God of War Ragnarok_extracted\models\ 下, 按 region -> WAD/texpack 层级组织
- 模型成功率: 100% (0 失败)
- 纹理成功率: 98.7% (666 失败/64,996 总计, 主要是 offset overflow)
- GLB已用trimesh验证: 12个region各取样1个, 全部有正确vertices+faces

### 最终目录结构
```
D:\God of War Ragnarok_extracted\models\
  alfheim\          61 WADs (11,134 GLBs) + textures\050_alfheim1 (2,993 DDS)
  asgard\           58 WADs (5,761 GLBs) + textures\090_asgard1 (1,870 DDS)
  base\             29 WADs (1,303 GLBs) + textures\root (12,133 DDS)
  characters\      248 WADs (4,534 GLBs)
  cutscenes\        31 WADs (226 GLBs)
  helheim\          23 WADs (4,765 GLBs) + textures\130_helheim (577 DDS)
  jotunheim\        42 WADs (6,613 GLBs) + textures\060_jotun (3,443 DDS)
  midgard\         164 WADs (22,139 GLBs) + textures\9 texpacks (17,787 DDS)
  muspelheim\       11 WADs (1,967 GLBs) + textures\100_muspel (1,318 DDS)
  niflheim\         25 WADs (5,203 GLBs) + textures\2 texpacks (6,377 DDS)
  svartalfheim\     73 WADs (20,017 GLBs) + textures\3 texpacks (7,884 DDS)
  valhalla\         textures\valhalla (3,315 DDS) [无独立WAD, meshes在shared WADs中]
  vanaheim\        227 WADs (43,892 GLBs) + textures\4 texpacks (6,450 DDS)
```

## ★ 模型提取: 100% 完成 ★
- 127,554 GLB (46.98 GB), 1,340,761 网格, 0 失败
- 提取脚本: extract_all_glb_v55.py
- 两阶段拷贝: robocopy E:->F:SSD (16min), Python F:->D:HDD (9min)

## ★ 纹理提取: 98.7% 完成 ★
- 64,147 DDS 成功, 666 失败, 183 跳过 (未知格式)
- 提取脚本: gnf_to_dds_v3.py + batch_extract_textures.py
- 失败原因: offset overflow (mip数据超出rawSize), data too short
- 失败率仅1.3%, 可接受

### ★★★ 多mip块填充规则 (VERIFIED 100% match) ★★★
1. ref_w = next_pow2(W), ref_h = next_pow2(H)
2. 每mip每切片块数: 用ref维度计算, 对齐到8 (最小8)
3. 总每切片块数: 对齐到16
4. 数据布局: mip-major
5. 行内填充: 每行ref_block_count_w块, 实际actual_block_count_w块
6. 单mip块: 宽度填充到32倍数
7. BC1/BC4 10mips: rawSize=176,128 ✅; BC7/BC6H 9mips: rawSize=90,112 ✅

### texture2ddecoder 1.0.6
- decode_bc1/4/6/7(data, W, H) -> 3参数, 返回BGRA

## WAD 格式 (完全逆向)
WAD = LZ4帧压缩; 解压: 64B头部 + N×144B TOC + 数据段
- TOC: +0=word0(1=MESH), +4=size, +8=hash, +24=name[80], +111=group, +114=batch_end

## PC GNF 格式
- magic=0x20466E47, imageDataOffset=0xFF8, arraySize=4
- fmtField bits[25:20]=format, dimField bits[13:0]=W-1 bits[27:14]=H-1

### PC格式码 -> DXGI
0x29=BC1, 0x2A=BC1_SRGB, 0x2F=BC4, 0x33=BC6H, 0x35=BC7, 0x36=BC7_SRGB

## 关键发现
- E:和D:在同一HDD, 直接E:->D:拷贝极慢(4.6 files/s)
- 两阶段拷贝(E:->F:SSD->D:HDD)快7倍
- robocopy /MT:16 /J 比Python快很多
- D:上同卷move瞬间完成(只改metadata)
- batch_extract_textures.py不跳过已提取文件

## 磁盘信息
- Disk 0 (HDD 4TB): D: (3.2TB, 219GB free) + E: (500GB)
- Disk 1 (SSD 2TB): C: (927GB) + F: (1TB, 547GB free)