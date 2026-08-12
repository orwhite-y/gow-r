# God of War Ragnarok - 资产提取总结

## 概述
从 `E:\God of War Ragnarok\exec\wad\pc_le` 中的 WAD 文件格式逆向提取模型、纹理和材质资产。

## 提取成果

| 资产类型 | 数量 | 格式 | 成功率 |
|---------|------|------|--------|
| 模型 | 127,554 | GLB | 100% |
| 纹理 | 64,147 (唯一) | DDS | 98.7% |
| 材质 | 186,081 | .mat (原始二进制) | 100% |
| 着色器签名 | 154,710 | .tx (原始二进制) | 100% |

## 关联统计

| 指标 | 数值 | 百分比 |
|------|------|--------|
| 有纹理的模型 | 110,876 / 127,554 | 86.9% |
| 纹理引用已找到 | 422,230 / 425,434 | 99.2% |
| 唯一材质 | 11,054 | - |
| 唯一纹理 | 18,268 | - |

## 目录结构
```
D:\God of War Ragnarok_extracted\models\
  {region}\                           ← 区域 (alfheim, midgard, vanaheim 等)
    {wad_name}\                       ← WAD 包名
      {wad}_MESH_{name}_{sub}_{idx}.glb   ← 模型文件
      materials\                      ← 材质目录
        {MAT_name}.mat                ← 材质原始数据
        {MAT_name}.tx                 ← 着色器 I/O 签名
      textures\                       ← 纹理目录
        {HASH}.dds                    ← DDS 纹理 (硬链接)
      material_mapping.json           ← 完整关联映射
      mat_index.json                  ← MAT 索引
    textures\                         ← 原始 DDS (按 texpack)
      {texpack_name}\
        {HASH}.dds
```

## material_mapping.json 格式
每个 WAD 目录下的 `material_mapping.json` 包含完整的模型-材质-纹理关联：

```json
{
  "wad": "midgard_zoo",
  "region": "midgard",
  "meshes": [
    {
      "mesh": "MESH_woodchips1_1_0",
      "idx": 17152,
      "mats": ["MAT_81DD51505F5B93C5"],
      "mat_details": [
        {
          "name": "MAT_81DD51505F5B93C5",
          "mat_file": "materials/MAT_81DD51505F5B93C5.mat",
          "tx_info": {
            "tx_name": "TX_wood_02_d_857A19B9053D7866",
            "dds_hash": "857A19B9053D7866",
            "tex_base": "wood_02_d"
          },
          "params": {
            "has_shader": true,
            "floats": [{"offset": 0, "value": 1.97e-24}],
            "potential_colors": []
          }
        }
      ],
      "textures": [
        {"hash": "375C0D39138F5C72", "type": "primary", "mat": "MAT_81DD51505F5B93C5", "found": true},
        {"hash": "5EFE18380E127E9D", "type": "normal", "mat": "MAT_81DD51505F5B93C5", "found": true},
        {"hash": "006D75E4C31A4CED", "type": "height", "mat": "MAT_81DD51505F5B93C5", "found": true},
        {"hash": "0A958A8D269427B4", "type": "gloss", "mat": "MAT_81DD51505F5B93C5", "found": true},
        {"hash": "710FE17C49DF2BEE", "type": "ao", "mat": "MAT_81DD51505F5B93C5", "found": true}
      ]
    }
  ]
}
```

## 纹理类型说明
| 类型 | 说明 |
|------|------|
| primary | 主纹理 (来自 MAT 的 TX 条目) |
| normal | 法线贴图 |
| gloss | 光泽度/粗糙度贴图 |
| diffuse | 漫反射/颜色贴图 |
| height | 高度贴图 |
| ao | 环境光遮蔽贴图 |
| mask | 材质遮罩贴图 |
| alpha | 透明度贴图 |
| unknown | 未分类纹理变体 |

## WAD 文件格式 (逆向结果)
- **压缩**: LZ4 帧压缩
- **结构**: 64B 头部 + N×144B TOC + 数据段
- **TOC 条目**: +0=word0(类型), +4=size, +8=hash, +24=name[80], +109=t109, +111=b111, +104=align

### 条目类型
| word0 | t109 | 名称前缀 | 说明 |
|-------|------|---------|------|
| 1 | 0x0c | MESH_ | 网格数据 |
| 1 | 0x0a | MAT_ | 材质定义 |
| 60 | 0x00 | TX_ | 着色器 I/O 签名 |
| 29 | 0x19 | TX_ | 纹理数据 (含 GNF) |
| 1 | 0x00 | MAT_ | MAT 引用条目 (size=0) |

## 关联方法
1. **MESH → MAT**: 通过 MESH 数据中嵌入的 MAT hash 或相邻 MAT 引用条目
2. **MAT → TX**: MAT 定义 (t109=0x0a) 后紧跟 TX 条目 (word0=60), TX 名称含 DDS hash
3. **多纹理关联**: 通过 TX base name 模糊匹配 word0=29 TX 条目 (normal/gloss/diffuse 等)
4. **LOD 链接**: LOD mesh 通过名称匹配继承父 mesh 的纹理
5. **引用解析**: 缺失纹理通过 TX 数据中的纹理引用解析到已有 DDS

## 剩余工作
- **328 个真正缺失纹理**: 运行时生成 (noise map, dynamic material 等), 无法从文件提取
- **13.1% 无纹理模型**: 主要是 shadow mesh (26.3%), LOD (18.9%), proxy 等辅助几何体
- **666 个 DDS 提取失败**: offset overflow, 可通过改进 GNF 解码器修复
- **132,621 个 unknown 纹理类型**: 可通过更详细的纹理名称模式匹配改善分类

## 工具脚本位置
所有脚本在 `E:\gow_re_workspace\scripts\`:
- `extract_all_glb_v55.py` - GLB 模型提取
- `gnf_to_dds_v3.py` - GNF → DDS 纹理转换
- `batch_extract_textures.py` - 批量纹理提取
- `build_global_mapping.py` - 全局模型-纹理映射构建
- `extract_mat_data.py` - MAT 材质数据提取
- `fix_no_tex_meshes.py` - 无纹理 mesh 修复 (MAT TX + LOD 链接)
- `sync_mappings.py` - 同步 per-WAD 映射文件
- `correlate_textures_v2.py` - 纹理硬链接
- `resolve_missing_tex.py` - 缺失纹理引用解析