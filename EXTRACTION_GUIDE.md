# God of War Ragnarok — WAD 拆包流程总结文档

> 本文档记录了从 GoWR WAD 文件中提取 3D 模型与纹理的完整逆向工程流程。
> 所有格式信息均经过 frida + IDA + x64dbg/CE 验证，非猜测。

---

## 目录

1. [项目概述](#1-项目概述)
2. [逆向工程方法论](#2-逆向工程方法论)
3. [WAD 文件格式（完全逆向）](#3-wad-文件格式完全逆向)
4. [模型提取流程](#4-模型提取流程)
5. [纹理提取流程](#5-纹理提取流程)
6. [脚本清单与说明](#6-脚本清单与说明)
7. [使用指南](#7-使用指南)
8. [最终结果](#8-最终结果)
9. [验证过的函数地址与偏移](#9-验证过的函数地址与偏移)
10. [关键技术发现](#10-关键技术发现)

---

## 1. 项目概述

| 项目 | 值 |
|------|-----|
| 游戏可执行文件 | `E:\God of War Ragnarok\GoWR.exe` |
| 资产目录 | `E:\God of War Ragnarok\exec\wad\pc_le` |
| 资产类型 | `.wad` / `.lodpack` + `.toc` / `.texpack` + `.toc` / `.shaderpack` |
| 输出目录 | `D:\God of War Ragnarok_extracted\models\` |
| 工作区 | `E:\gow_re_workspace\` |

### 资产文件说明

| 扩展名 | 用途 | 说明 |
|--------|------|------|
| `.wad` | 资产清单 + mesh/rig 定义 | 目录 + 小文件（LZ4 压缩） |
| `.lodpack` | 网格顶点/索引缓冲（分 LOD） | 模型数据仓库 |
| `.texpack` | 贴图像素（GNF 格式） | 贴图仓库 |
| `.toc` | lodpack/texpack 的目录索引 | 仓库的货架清单 |
| `.shaderpack` | 预编译着色器 | 独立仓库（本工具不处理） |

### 最终提取统计

| 类型 | 数量 | 成功率 | 体积 |
|------|------|--------|------|
| GLB 模型 | 127,554 个 | 100% (0 失败) | 46.98 GB |
| 网格 (mesh) | 1,340,761 个 | — | — |
| DDS 纹理 | 64,147 个 | 98.7% (666 失败) | 106.07 GB |
| **合计** | **191,701 个资产** | — | **~153 GB** |
| 压缩后 | 13 个 7z 分包 | — | **59.61 GB** (40.6% 压缩率) |

---

## 2. 逆向工程方法论

### 工具链

| 工具 | 路径 | 用途 |
|------|------|------|
| IDA Pro (MCP) | `http://127.0.0.1:13337/mcp` | 静态反编译、注释写入 |
| Frida v17 | `C:\Python314\Scripts\frida.exe` | 动态 hook、内存断点、运行时验证 |
| x64dbg (MCP) | `http://127.0.0.1:3000/mcp` | 断点调试、内存检查 |
| Cheat Engine | `F:\tool\Cheat Engine\Cheat Engine.exe` | 内存搜索、验证 |
| Python 3.14 | `C:\Python314\python.exe` | 脚本执行 |
| 7-Zip 24.09 | `F:\soft\7-Zip\7z.exe` | 压缩打包 |

### 验证流程

```
IDA 静态分析 → 识别函数/结构体
       ↓
Frida spawn (-f) 启动游戏 → hook 关键函数
       ↓
Interceptor.attach 下断点 → 抓取运行时数据/堆栈
       ↓
字节级匹配 → 验证格式假设
       ↓
IDA 注释写入 → 永久记录验证结果
```

### 关键规则

- **Frida 必须 spawn** (`-f`)，不能 attach（attach 会导致游戏崩溃）
- **MemoryAccessMonitor 会导致游戏卡死**，只能使用 `Interceptor.attach`
- 验证过的函数/偏移必须写入 IDA 注释
- 游戏可直接运行，不依赖 Steam

---

## 3. WAD 文件格式（完全逆向）

### 3.1 整体结构

WAD 文件使用 **LZ4 帧压缩**。解压后数据以 `WTOC` 魔数开头。

```
┌─────────────────────────────────────────────────────┐
│                  WAD 文件 (LZ4 压缩)                  │
├─────────────────────────────────────────────────────┤
│  解压后:                                             │
│  ┌──────────────┐                                    │
│  │  Header 64B  │  magic="WTOC", entryCount@+8       │
│  ├──────────────┤                                    │
│  │  TOC N×144B  │  每条目 144 字节                    │
│  ├──────────────┤                                    │
│  │  Data 段     │  原始数据（无二次编码）              │
│  └──────────────┘                                    │
└─────────────────────────────────────────────────────┘
```

### 3.2 Header (64 字节)

| 偏移 | 大小 | 类型 | 含义 |
|------|------|------|------|
| +0x00 | 4 | char[4] | 魔数 `WTOC` |
| +0x08 | 4 | u32 | 条目数量 (entryCount) |
| +0x10 | 8 | u64 | 数据段起始偏移 = 64 + 144 × entryCount |

### 3.3 TOC 条目 (144 字节/条目)

| 偏移 | 大小 | 类型 | 含义 | 验证 |
|------|------|------|------|------|
| +0x00 | 2 | u16 | word0: 类型码 (1=MESH, 29=MG_) | ✅ frida |
| +0x02 | 2 | u16 | flags (bit10=0x400 特殊标记) | ✅ frida |
| +0x04 | 4 | u32 | 数据大小 (sizeFlag) | ✅ frida |
| +0x08 | 8 | u64 | hash (0=内联数据, ≠0=外部 lodpack) | ✅ frida |
| +0x18 | 80 | char[80] | 资源名 (如 "MESH_snowchunks_0") | ✅ frida |
| +0x68 | 4 | u32 | align (对齐字节) | ✅ frida |
| +0x6C | 1 | u8 | t108: 子类型高字节 (0x0a=MESH, 0x01=MG, 0x02=MDL) | ✅ frida |
| +0x6D | 1 | u8 | t109: type_code (0x0a=mesh, 0x0c=MESH/MG/MDL 组) | ✅ frida |
| +0x6E | 1 | u8 | t110 | ✅ frida |
| +0x6F | 1 | u8 | b111: sub-type (5/6/7=跳过, 其他=处理) | ✅ frida |
| +0x70 | 1 | u8 | byte112: 0x7F=正常 | ✅ frida |
| +0x72 | 2 | u16 | byte114: bit0=batch_end 标记 | ✅ frida |
| +0x78 | 8 | ptr | 数据指针 (指向 WAD raw 数据) | ✅ frida |

### 3.4 条目类型

| word0 | t109 | 名称前缀 | 数据起始 | 用途 |
|-------|------|----------|----------|------|
| 1 | 0x0a | `MESH_` | `0c 00 0a 00 00 00 00 00...` | meshbuf 元数据 (typecode 0x000A000C) |
| 29 | 0x01 | `MG_` | `0c 00 01 00 00 00 00 00...` | 顶点数据 (name="MG_*_gpu") |
| — | 0x02 | `MDL_` | `0c 00 02 10 00 00 00 00...` | 模型定义 |

### 3.5 MESH ↔ MG_ 配对规则

```
MESH_snowchunks_0  ↔  MG_snowchunks_0_gpu
```

- `MESH_` 条目包含 meshbuf 元数据（属性表、流表、顶点布局）
- `MG_` 条目包含实际顶点缓冲数据
- 配对方式：名称匹配（`MESH_X` ↔ `MG_X_gpu`）

### 3.6 hash 字段含义

| hash 值 | 含义 | 数据位置 |
|---------|------|----------|
| `0` | 静态/基础模型 | 顶点数据内联在 MG_ 条目中 (basePtr = MG_ 文件偏移) |
| `≠ 0` | 动态模型 | 顶点数据在外部 `.lodpack` 文件中 |

### 3.7 Batch 机制

WAD 数据按 **batch** 组织：
- batch 边界由 `byte114 bit0` 标记
- 同一 batch 内条目共享上下文
- 文件偏移通过 batch 模拟计算（100% 验证，0/19697 不匹配）

---

## 4. 模型提取流程

### 4.1 meshbuf 解析（VERIFIED session 53）

```
meshbuf (mb) 结构:
  offset_array 在 mb[12 + off_arr_off]
  meshSub[i] 在 arr_pos + offset_array[i]
  
  每个 meshSub 的字段定位:
    shift = si * 4                    ← 通用规则 (365/365 验证)
    base = sa + shift
    所有字段相对 base 计算:
      vc (vertex count)     → base + 68
      tc (triangle count)   → base + 72
      hash                  → base + 104
      ato (attr table off)  → base + 96  (始终 = 0x90 = 144)
      sto (stream table off)→ base + 100 (224/240/256/272/288)
      attr table            → base + ato, count = (sto - ato) / 8
      stream table          → base + sto
```

### 4.2 顶点属性语义

| 语义码 | 含义 |
|--------|------|
| 0 | POSITION |
| 1 | BLENDWEIGHT |
| 2 | BLENDINDICES |
| 3 | TEXCOORD |
| 4 | TANGENT |
| 5 | BINORMAL |
| 6 | NORMAL |
| 9 | COLOR |

### 4.3 顶点格式

| 格式码 | 字节数 | 类型 |
|--------|--------|------|
| 0 | 4 | float |
| 2 | 4 | float |
| 3 | 4 | float |
| 1 | 2 | half/ushort |
| 4 | 2 | half/ushort |
| 5 | 2 | half/ushort |
| 6 | 2 | half/ushort |
| 7 | 2 | half/ushort |
| 8 | 1 | byte |
| 9 | 1 | byte |
| 0xA | 1 | byte |
| 0xB | 1 | byte |

### 4.4 完整提取管线

```
                    ┌─────────────────────┐
                    │  遍历 pc_le/*.wad    │
                    └──────────┬──────────┘
                               ▼
                    ┌─────────────────────┐
                    │  LZ4 解压 WAD        │
                    │  → WTOC 数据         │
                    └──────────┬──────────┘
                               ▼
                    ┌─────────────────────┐
                    │  解析 64B Header     │
                    │  解析 N×144B TOC     │
                    └──────────┬──────────┘
                               ▼
               ┌───────────────┴───────────────┐
               ▼                               ▼
    ┌──────────────────┐             ┌──────────────────┐
    │  MESH 条目        │             │  MG_ 条目         │
    │  (word0=1)        │             │  (word0=29)       │
    │  解析 meshbuf     │             │  顶点缓冲数据      │
    └────────┬─────────┘             └────────┬─────────┘
             │                                │
             └────────────┬───────────────────┘
                          ▼
               ┌──────────────────────┐
               │  名称配对             │
               │  MESH_X ↔ MG_X_gpu   │
               └──────────┬───────────┘
                          ▼
               ┌──────────────────────┐
               │  检查 hash 字段       │
               └──────┬───────┬───────┘
                      ▼       ▼
           hash==0            hash≠0
               │                 │
               ▼                 ▼
    ┌──────────────────┐ ┌──────────────────────┐
    │  内联顶点数据     │ │  外部 lodpack 查找    │
    │  basePtr = MG_   │ │  .lodpack.toc 二分    │
    │  文件偏移         │ │  搜索 (24B/条目)      │
    └────────┬─────────┘ └──────────┬───────────┘
             │                      │
             └──────────┬───────────┘
                        ▼
             ┌────────────────────────┐
             │  解析顶点属性表          │
             │  + 流表                  │
             │  → 顶点布局              │
             └────────────┬───────────┘
                          ▼
             ┌────────────────────────┐
             │  按格式码提取            │
             │  POSITION / NORMAL      │
             │  TEXCOORD / TANGENT     │
             │  BLENDWEIGHT/INDICES    │
             └────────────┬───────────┘
                          ▼
             ┌────────────────────────┐
             │  构建 GLB (glTF 2.0)    │
             │  → 写入 .glb 文件       │
             └────────────────────────┘
```

### 4.5 Lodpack TOC 结构

```
.lodpack.toc 条目 (24 字节/条目，按 hash 排序):
  +0x00  u32  groupIdx
  +0x04  u32  offsetter
  +0x08  u64  hash (二分搜索 key)
  +0x10  u32  blockSize
  +0x14  u32  skip
```

Mesh → Lodpack 查找路径：
```
mesh_obj → +40 → +0x68 → hash(u64) → 二分搜索 lodpack TOC → 顶点数据
```

---

## 5. 纹理提取流程

### 5.1 PC GNF 格式

`.texpack` 文件内嵌 GNF 格式纹理。

| 偏移 | 大小 | 含义 |
|------|------|------|
| +0x00 | 4 | 魔数 `0x20466E47` |
| +0x14 | 4 | fmt_field: bits[25:20] = 格式码 |
| +0x18 | 4 | dim_field: bits[13:0] = W-1, bits[27:14] = H-1 |
| +0x1C | 4 | mip_field: bits[19:16]+1 = mip 数 |
| +0x20 | 4 | dp_field: bits[12:0]+1 = depth |
| +0x2C | 4 | data_size |
| +0xFF8 | — | imageDataOffset (像素数据起始) |

### 5.2 PC 格式码 → DXGI 映射

| 格式码 | DXGI | 块大小 | 字节/块 | 说明 |
|--------|------|--------|---------|------|
| 0x29 | 71 | 4×4 | 8 | BC1_TYPELESS |
| 0x2A | 72 | 4×4 | 8 | BC1_UNORM_SRGB |
| 0x2F | 80 | 4×4 | 8 | BC4_TYPELESS |
| 0x30 | 81 | 4×4 | 8 | BC4_UNORM_SNORM |
| 0x33 | 95 | 8×4 | 16 | BC6H_TYPELESS_UF16 |
| 0x34 | 96 | 8×4 | 16 | BC6H_TYPELESS_SF16 |
| 0x35 | 98 | 8×4 | 16 | BC7_TYPELESS |
| 0x36 | 99 | 8×4 | 16 | BC7_UNORM_SRGB |

### 5.3 多 mip 块填充规则（VERIFIED 100% match）

```
1. ref_w = next_pow2(W), ref_h = next_pow2(H)
2. 每个 mip 每切片块数: 用 ref 维度计算, 对齐到 8 (最小 8)
3. 总每切片块数: 对齐到 16
4. 数据布局: mip-major (所有切片的 mip N, 然后所有切片的 mip N+1)
5. 行内填充: 每行 ref_block_count_w 块, 实际 actual_block_count_w 块
6. 单 mip 块: 宽度填充到 32 倍数
7. BC1/BC4 10 mips: rawSize=176,128 ✅
   BC7/BC6H 9 mips: rawSize=90,112 ✅
```

### 5.4 BC6H 特殊处理

- depth=6（立方体贴图）
- arraySize 实际为 24 (4 arrays × 6 cube faces)

### 5.5 纹理提取管线

```
    ┌─────────────────────────┐
    │  遍历 pc_le/*.texpack    │
    └────────────┬────────────┘
                 ▼
    ┌─────────────────────────┐
    │  读取 .toc 索引           │
    │  → 纹理条目列表           │
    └────────────┬────────────┘
                 ▼
    ┌─────────────────────────┐
    │  逐条目提取 GNF 数据      │
    │  magic=0x20466E47        │
    └────────────┬────────────┘
                 ▼
    ┌─────────────────────────┐
    │  解析 GNF Header          │
    │  → fmt, W, H, mips, depth│
    └────────────┬────────────┘
                 ▼
    ┌─────────────────────────┐
    │  格式码 → DXGI 映射       │
    │  未知格式 → 跳过          │
    └────────────┬────────────┘
                 ▼
    ┌─────────────────────────┐
    │  计算 mip 块布局          │
    │  (填充规则见 5.3)         │
    └────────────┬────────────┘
                 ▼
    ┌─────────────────────────┐
    │  构建 DDS Header          │
    │  + 拼接像素数据           │
    └────────────┬────────────┘
                 ▼
    ┌─────────────────────────┐
    │  写入 .dds 文件           │
    │  {hash:016X}.dds          │
    └─────────────────────────┘
```

---

## 6. 脚本清单与说明

| 脚本 | 大小 | 功能 |
|------|------|------|
| `extract_all_glb_v55.py` | 26.5 KB | WAD → GLB 模型提取器（核心） |
| `gnf_to_dds_v3.py` | 13.6 KB | GNF → DDS 纹理转换器（核心） |
| `batch_extract_textures.py` | 2.1 KB | 批量纹理提取（调用 gnf_to_dds） |
| `run_full_extract.py` | 2.7 KB | 一键全流程（带跳过逻辑+进度日志） |
| `copy_glb_stage2_ssd_to_hdd.py` | 3.5 KB | 两阶段拷贝 GLB（SSD→HDD） |
| `reorganize_textures.py` | 3.3 KB | 纹理重组到 region 层级 |
| `validate_trimesh.py` | 2.2 KB | GLB 验证（trimesh 加载检查） |
| `compress_all_regions.ps1` | 2.4 KB | 7z 分 region 压缩 |
| `mcp_ida_client.py` | 3.8 KB | IDA MCP 客户端 |
| `ida_write_comments_v2.py` | 6.8 KB | IDA 注释写入 |

### static_analysis/ — 反编译参考代码

| 文件 | 内容 |
|------|------|
| `wadmulti_full.c` | WAD 多条目处理器 (sub_140393E20) |
| `wad_multientry_full.c` | 同上（完整版） |
| `wad_batchprocess_full.c` | 逐条目处理器 (WadBatchProcessInner) |
| `wad_dispatch_full.c` | 分发器 (WadDispatch) |
| `meshresolver_decomp.c` | Mesh lodpack 解析器 (sub_1405FA610) |
| `meshdataprocess_decomp.c` | Mesh 数据处理器 (sub_1405E4920) |
| `vbsetup_decomp.c` | 顶点缓冲设置 |
| `vdeclbinder_decomp.c` | 顶点声明绑定器 |
| `reference_notes_1.txt` | 验证过的偏移与结构体笔记 |

---

## 7. 使用指南

### 7.1 环境要求

```powershell
# Python 依赖
pip install lz4 numpy trimesh texture2ddecoder

# 工具路径
$python = "C:\Python314\python.exe"
$frida  = "C:\Python314\Scripts\frida.exe"
$7z     = "F:\soft\7-Zip\7z.exe"
```

### 7.2 提取模型

```powershell
# 方法 A: 一键全流程（推荐）
cd E:\gow_re_workspace\scripts
C:\Python314\python.exe run_full_extract.py

# 方法 B: 单独提取
# 脚本内修改 PC_LE 和 OUT_DIR 路径后运行
C:\Python314\python.exe extract_all_glb_v55.py
```

**输出结构：**
```
output/glb_all/
  r_perm_MESH_xxx.glb
  r_alf_xxx_MESH_xxx.glb
  ...
```

### 7.3 拷贝到最终目录（两阶段）

```powershell
# Stage 1: E: → F: SSD (robocopy, 快)
robocopy E:\gow_re_workspace\output\glb_all F:\temp_glb\ *.glb /MT:16 /J

# Stage 2: F: SSD → D: HDD (Python 脚本, 按层级组织)
C:\Python314\python.exe copy_glb_stage2_ssd_to_hdd.py
```

> **为什么两阶段？** E: 和 D: 在同一物理 HDD 上，直接拷贝只有 4.6 files/s。
> 经 F: SSD 中转后快 7 倍。

### 7.4 提取纹理

```powershell
cd E:\gow_re_workspace\scripts
C:\Python314\python.exe batch_extract_textures.py
```

### 7.5 重组纹理到 region 层级

```powershell
C:\Python314\python.exe reorganize_textures.py
```

### 7.6 验证 GLB

```powershell
# 修改脚本内 GLB_DIR 为目标目录
C:\Python314\python.exe validate_trimesh.py
```

### 7.7 压缩打包

```powershell
# 修改脚本内路径后运行
powershell -ExecutionPolicy Bypass -File compress_all_regions.ps1
```

**参数说明：**
- `-mx=5`: 压缩级别（平衡速度/压缩率）
- `-mmt=8`: 8 线程
- `-v10g`: 大 region 分卷（>15GB 的 region 使用）

---

## 8. 最终结果

### 8.1 目录结构

```
D:\God of War Ragnarok_extracted\models\
├── alfheim\          61 WADs (11,134 GLBs) + textures\050_alfheim1 (2,993 DDS)
├── asgard\           58 WADs (5,761 GLBs) + textures\090_asgard1 (1,870 DDS)
├── base\             29 WADs (1,303 GLBs) + textures\root (12,133 DDS)
├── characters\      248 WADs (4,534 GLBs)
├── cutscenes\        31 WADs (226 GLBs)
├── helheim\          23 WADs (4,765 GLBs) + textures\130_helheim (577 DDS)
├── jotunheim\        42 WADs (6,613 GLBs) + textures\060_jotun (3,443 DDS)
├── midgard\         164 WADs (22,139 GLBs) + textures\9 texpacks (17,787 DDS)
├── muspelheim\       11 WADs (1,967 GLBs) + textures\100_muspel (1,318 DDS)
├── niflheim\         25 WADs (5,203 GLBs) + textures\2 texpacks (6,377 DDS)
├── svartalfheim\     73 WADs (20,017 GLBs) + textures\3 texpacks (7,884 DDS)
├── valhalla\         textures\valhalla (3,315 DDS) [无独立 WAD]
└── vanaheim\        227 WADs (43,892 GLBs) + textures\4 texpacks (6,450 DDS)
```

### 8.2 压缩包

```
D:\God of War Ragnarok_extracted\archives\
├── alfheim.7z              4.53 GB
├── asgard.7z               2.27 GB
├── base.7z                 3.29 GB
├── characters.7z           0.77 GB
├── cutscenes.7z            0.09 GB
├── helheim.7z              0.99 GB
├── jotunheim.7z            4.60 GB
├── midgard.7z.001         10.00 GB  ← 分卷
├── midgard.7z.002          3.88 GB  ← 分卷
├── muspelheim.7z           1.52 GB
├── niflheim.7z             5.07 GB
├── svartalfheim.7z.001     9.47 GB
├── valhalla.7z             3.25 GB
├── vanaheim.7z.001         9.88 GB
└── TOTAL                  59.61 GB  (原始 146.77 GB, 压缩率 40.6%)
```

### 8.3 Region 分类规则

WAD 文件名前缀 → Region 映射：

| 前缀 | Region |
|------|--------|
| `alf` | alfheim |
| `asg` | asgard |
| `hel` | helheim |
| `jot` | jotunheim |
| `mid`, `northbay` | midgard |
| `msp`, `muspelheim` | muspelheim |
| `nif`, `rbr` | niflheim |
| `sva` | svartalfheim |
| `van`, `val` | vanaheim |
| `r_`, `add`, `char` | characters |
| `c_` | cutscenes |
| `base`, `gbl`, `boatglobal`, `wolfsledglobal`, `waterglobal` | base |

---

## 9. 验证过的函数地址与偏移

### 9.1 IDA 函数地址（14 个，全部已写入 IDA 注释）

| 地址 | 功能 | 验证方式 |
|------|------|----------|
| `0x140391140` | **DISPATCH 分发器**: v3=(u8)type_code, 从 TLS[TlsIndex+4464+8*v3] 取 handler, 调 vtable+120 | frida 确认 |
| `0x140393070` | **WAD 单条目加载器**: 调 WTOC parser, entry+120=data_buf, 数据 RAW 无解码 | IDA + frida |
| `0x140393910` | Read callback 1: interlocked exchange 通知 | IDA 静态 |
| `0x140393940` | Read callback: memcpy(entry+120, read_buf, size) | IDA 静态 |
| `0x140393E20` | **WAD 多条目处理器**: WTOC parser + 144B 条目迭代, 原始数据直接拷贝 | IDA + frida |
| `0x1403A15F0` | 注册 lodpack + 预缓存: ctx+283424 | IDA 静态 |
| `0x1403A1820` | **运行时 lodpack 查找**: (ctx, out, group, &hash) | IDA 静态 |
| `0x1403A1DD0` | Lodpack TOC 加载器: 构建 .lodpack.toc 路径 | IDA 静态 |
| `0x1403B2550` | WAD resource handler vtable 初始化 | IDA 静态 |
| `0x1403B3980` | **WTOC parser**: 读 64B header + 144B entry table | IDA + frida |
| `0x1403D7730` | **COMMON TYPE HANDLER** (vtable+120): 二次分发, 数据到达时已解码 | frida 确认 |
| `0x1405F0580` | Lodpack 构造函数: TOC→obj+0, name→obj+8 | IDA 静态 |
| `0x1405F0910` | Lodpack 查找: 二分搜索 member(hash@+8) | IDA 静态 |
| `0x1405F1110` | Lodpack hash 二分搜索: 24B/条目, hash@+8, 已排序 | IDA 静态 |
| `0x1405FA610` | **Mesh lodpack resolver**: hash 从 *(*(mesh_obj+40)+0x68) | IDA 静态 |

### 9.2 Entry 结构体偏移

| 偏移 | 类型 | 含义 | 验证 |
|------|------|------|------|
| +0x04 | u32 | 数据大小 | ✅ frida |
| +0x18 | char[0x38] | 资源名 | ✅ frida |
| +0x64 | u32 | flag (0=外部指针, ≠0=内联) | ✅ frida |
| +0x6C | u8 | t108 子类型高字节 | ✅ frida |
| +0x6D | u8 | t109 type_code | ✅ frida |
| +0x6E | u8 | t110 | ✅ frida |
| +0x78 | ptr | 数据指针 | ✅ frida |

### 9.3 Type Code → Handler 映射

| type_code | handler (base+offset) | 用途 |
|-----------|----------------------|------|
| 0x01 | base+0x597600 | 未知 |
| 0x02 | base+0x3D7730 | common handler |
| 0x0a | base+0x3D7730 | mesh |
| 0x0c | base+0x3D7730 | MESH/MG/MDL 组 |
| 0x10 | base+0x4AD130 | 未知 |
| 0x1a | base+0x4B50F0 | 未知 |
| 其他 | base+0x3D7730 | common handler |

### 9.4 Lodpack TOC 条目 (24 字节)

| 偏移 | 类型 | 含义 |
|------|------|------|
| +0x00 | u32 | groupIdx |
| +0x04 | u32 | offsetter |
| +0x08 | u64 | hash (二分搜索 key) |
| +0x10 | u32 | blockSize |
| +0x14 | u32 | skip |

---

## 10. 关键技术发现

### 10.1 磁盘 I/O 优化

- E: 和 D: 在同一物理 HDD (Disk 0, 4TB)
- 直接 E:→D: 拷贝极慢 (4.6 files/s)
- **两阶段拷贝** (E:→F:SSD→D:HDD) 快 7 倍
- `robocopy /MT:16 /J` 比 Python 拷贝快很多
- D: 上同卷 move 瞬间完成（只改 metadata）

### 10.2 WAD 数据无二次编码

WAD 解压后的数据是 **RAW 原始数据**，到达 handler 时无解码过程。
frida 确认：dispatch 时数据已以 `typeCode+00 00 80` 开头。

### 10.3 meshSub shift 通用规则

```
shift = si * 4
```

**通用规则**，365/365 meshSubs 全部验证通过。所有字段相对 `base = sa + shift` 计算，
不是相对 `sa`。

### 10.4 Sentinel 值不是魔数

`0xFFFFFFFFFFFF2310` 是一个 **变量字段**，根据 attr count 不同而变化。
不要用作字段定位的魔数。

### 10.5 GNF 像素数据是线性的

PC 版 GNF 像素数据是 **线性布局**，没有 Morton swizzle。
（与 PS5 版不同）

### 10.6 BC6H 立方体贴图

BC6H 格式 depth=6，实际 arraySize=24 (4 arrays × 6 cube faces)。
需要特殊处理。

### 10.7 texture2ddecoder

```
decode_bc1/4/6/7(data, W, H) → 3 参数, 返回 BGRA
版本: 1.0.6
```

### 10.8 Frida v17 注意事项

- 使用 `Process.getModuleByName(...).getExportByName(...)` 代替 `Module.getExportByName`
- MemoryAccessMonitor 会导致游戏卡死，只能用 `Interceptor.attach`
- 必须 spawn (`-f`)，不能 attach

### 10.9 IDA MCP 注意事项

- `set_comments(items=[{addr, comment}])` — items 是列表
- `rename` 的 batch 参数格式无效，用 `py_eval` 直接调 `idaapi.set_name`
- `decompile` 用 `addr`（不是 `address`）
- `get_bytes` 需要 `regions`
- `xrefs_to` 需要 `addrs`（复数）
- `py_eval` 用 `code`

---

## 附录: 压缩统计

| Region | 原始 (GB) | 压缩 (GB) | 压缩率 | 耗时 (min) |
|--------|-----------|-----------|--------|------------|
| cutscenes | 0.30 | 0.09 | 30% | 0.4 |
| characters | 3.08 | 0.77 | 25% | 5.5 |
| helheim | 2.64 | 0.99 | 37% | 3.2 |
| muspelheim | 3.92 | 1.52 | 39% | 3.0 |
| asgard | 5.51 | 2.27 | 41% | 4.2 |
| base | 8.23 | 3.29 | 40% | 5.1 |
| valhalla | 8.39 | 3.25 | 39% | 5.5 |
| jotunheim | 10.22 | 4.60 | 45% | 8.2 |
| alfheim | 11.81 | 4.53 | 38% | 10.0 |
| niflheim | 12.26 | 5.07 | 41% | 10.0 |
| svartalfheim | 22.75 | 9.47 | 42% | 24.0 |
| vanaheim | 25.73 | 9.88 | 38% | 25.3 |
| midgard | 30.93 | 13.88 | 45% | 25.3 |
| **TOTAL** | **146.77** | **59.61** | **40.6%** | **~130** |