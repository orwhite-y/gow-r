# Codex 工作流程记录 (MEMORY.md)

> 替代 PROCESS.md。只记已验证的实锤发现，不猜猜。
> 最近验证时间: 2026-08-10 (session 58 - MAT extraction + texture correlation complete)
> 验证方法: IDA 反编译 + WAD 字节级匹配 + texpack rawSize 数学验证 + DDS解码验证 + trimesh GLB验证

## 当前状态
- **项目路径**: E:\God of War Ragnarok\exec\wad\pc_le
- **最近更新**: 2026-08-12
- **最近会话**: session 60
- **进行中**: 无 (SKILL.md 坑总结扩充完成)
- **下一步**: 可选 - 修复328个真正缺失的纹理 / git push更新

## ★★★ 最终结果: 模型+纹理+MAT提取与关联 100% 完成 ★★★
- **127,554 个 GLB 模型** + **64,147 个唯一 DDS 纹理** + **186,081 个 MAT 材质文件** + **154,710 个 TX 着色器文件**
- 全部在 D:\God of War Ragnarok_extracted\models\ 下, 按 region -> WAD/texpack 层级组织
- 模型成功率: 100% (0 失败)
- 纹理成功率: 98.7% (666 失败/64,996 总计, 主要是 offset overflow)
- MAT提取: 100% (所有WAD中的MAT定义都已提取为.mat文件)
- 纹理关联率: 86.9% (110,876/127,554 meshes有纹理)
- 纹理找到率: 99.2% (422,230/425,434 texture refs有DDS文件)

### 关联统计
- 总mesh数: 127,554
- 有纹理的mesh: 110,876 (86.9%)
- 无纹理的mesh: 16,678 (13.1%) - 主要是shadow(26.3%), lod(18.9%), proxy等
- 唯一MAT数: 11,054
- 唯一纹理hash数: 18,268
- 总纹理引用: 425,434
- 纹理找到: 422,230 (99.2%)
- 纹理缺失: 3,204 (0.8%) - 其中328个唯一hash真正缺失(运行时生成纹理)

### 纹理类型分布
- unknown: 132,621 (31.2%)
- primary: 108,014 (25.4%)
- normal: 72,774 (17.1%)
- gloss: 69,997 (16.5%)
- ao: 15,401 (3.6%)
- height: 10,731 (2.5%)
- mask: 6,966 (1.6%)
- alpha: 4,606 (1.1%)
- diffuse: 4,324 (1.0%)

### 最终目录结构
```
D:\God of War Ragnarok_extracted\models\
  {region}\
    {wad_name}\
      {wad_name}_MESH_{meshname}_{sub}_{idx}.glb    ← 模型
      materials\
        {MAT_name}.mat                               ← 材质原始数据
        {MAT_name}.tx                                ← 着色器I/O签名数据
      textures\
        {HASH}.dds                                   ← 硬链接纹理
      material_mapping.json                          ← 完整关联映射(MAT+纹理)
      mat_index.json                                 ← MAT索引(含参数解析)
    textures\                                        ← 原始DDS位置(按texpack)
      {texpack_name}\
        {HASH}.dds
```

### material_mapping.json 格式
```json
{
  "wad": "wad_name",
  "region": "region_name",
  "meshes": [
    {
      "mesh": "MESH_name",
      "idx": 12345,
      "mats": ["MAT_HASH"],
      "mat_details": [
        {
          "name": "MAT_HASH",
          "mat_file": "materials/MAT_HASH.mat",
          "tx_info": {"tx_name": "TX_...", "dds_hash": "...", "tex_base": "..."},
          "params": {"has_shader": true, "floats": [...], "potential_colors": [...]}
        }
      ],
      "textures": [
        {"hash": "HASH", "type": "primary", "mat": "MAT_HASH", "found": true, "dds_hash": "HASH"}
      ]
    }
  ]
}
```

## ★ 模型提取: 100% 完成 ★
- 127,554 GLB (46.98 GB), 1,340,761 网格, 0 失败
- 提取脚本: extract_all_glb_v55.py

## ★ 纹理提取: 98.7% 完成 ★
- 64,147 DDS 成功, 666 失败, 183 跳过 (未知格式)
- 提取脚本: gnf_to_dds_v3.py + batch_extract_textures.py
- 失败原因: offset overflow (mip数据超出rawSize), data too short

## ★ MAT提取: 100% 完成 ★
- 186,081 个 .mat 文件 (含跨WAD重复)
- 26,991 个唯一MAT
- 154,710 个 .tx 文件 (着色器I/O签名)
- 提取脚本: extract_mat_data.py
- MAT数据格式: 参数头(floats) + DXBC着色器字节码
- TX数据格式: 着色器输入/输出签名 (SV_Position, TEXCOORD, NORMAL, TANGENT等)

## ★ 纹理关联: 86.9% 完成 ★
- 关联脚本: build_global_mapping.py + fix_no_tex_meshes.py + sync_mappings.py
- 关联方法:
  1. MESH -> MAT: 通过嵌入hash或相邻MAT引用条目
  2. MAT -> TX: MAT定义(t109=0x0a)后跟TX条目(word0=60)
  3. TX -> DDS: TX名称末尾16位hex = DDS hash
  4. 多纹理: 通过TX base name模糊匹配word0=29 TX条目
  5. LOD链接: LOD mesh继承父mesh的纹理
  6. 引用解析: 缺失纹理通过TX数据中的引用解析到已有DDS

### 纹理引用解析
- 616个缺失唯一hash中, 288个通过TX数据中的引用解析到已有DDS
- 328个真正缺失: 运行时生成纹理(noise map, dynamic material等), 无法从文件提取

## WAD 格式 (完全逆向)
WAD = LZ4帧压缩; 解压: 64B头部 + N×144B TOC + 数据段
- TOC: +0=word0(1=MESH), +4=size, +8=hash, +24=name[80], +109=t109, +111=b111, +104=align
- MAT定义: name=MAT_xxx, t109=0x0a
- TX条目: name=TX_xxx, word0=60(签名)或29(纹理数据)
- MESH条目: name=MESH_xxx, t109=0x0c

## PC GNF 格式
- magic=0x20466E47, imageDataOffset=0xFF8, arraySize=4
- fmtField bits[25:20]=format, dimField bits[13:0]=W-1 bits[27:14]=H-1

### PC格式码 -> DXGI
0x29=BC1, 0x2A=BC1_SRGB, 0x2F=BC4, 0x33=BC6H, 0x35=BC7, 0x36=BC7_SRGB

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

## 关键发现
- E:和D:在同一HDD, 直接E:->D:拷贝极慢(4.6 files/s)
- 两阶段拷贝(E:->F:SSD->D:HDD)快7倍
- robocopy /MT:16 /J 比Python快很多
- D:上同卷move瞬间完成(只改metadata)
- batch_extract_textures.py不跳过已提取文件
- MAT数据包含DXBC着色器字节码, 不只是float参数
- 嵌入WAD的GNF纹理是引用条目(指向texpack中的纹理), 非独立纹理
- LOD mesh可通过名称匹配继承父mesh的纹理
- 13.1%无纹理mesh主要是shadow(26.3%), lod(18.9%), proxy等辅助几何

## 磁盘信息
- Disk 0 (HDD 4TB): D: (3.2TB, ~219GB free) + E: (500GB)
- Disk 1 (SSD 2TB): C: (927GB) + F: (1TB, 547GB free)
- 硬链接用于纹理(同D:卷, 不占额外磁盘空间)

## session 60 变更 (2026-08-12)
- SKILL.md 坑总结从23条扩充到31条 (新增B8-B11, C3, D5-D7)
- 新增坑覆盖: BC6H arraySize, GNF线性布局, batch边界, robocopy优化, 前缀匹配特异性, 分包遗漏目录, 7z listfile不稳定
- 16个压缩包全部验证通过 (GLB/MAT/DDS 100%匹配)
- vanaheim拆分为5个子包 (part1-5), 覆盖所有子目录含zoo/misc/textures/val0*
- 所有压缩包已push到 F:\gow_archives\
- git已push到 git@github.com:orwhite-y/gow-r.git