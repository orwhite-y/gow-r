# SKILL: Game Asset Extraction via Reverse Engineering

> 通用技能: 从任意商业游戏的打包文件中提取 3D 模型、纹理、材质。
> 方法论基于静态分析(IDA) + 动态验证(Frida) + 字节级确认的三层验证体系。

---

## 适用场景

- 游戏使用自定义打包格式 (非标准 zip/pak)
- 无官方 mod 工具或 SDK
- 目标: 从文件中提取 90%+ 可用模型/纹理 (文件级, 非内存级)
- 有可执行文件 + 逆向工具 (IDA/Frida/x64dbg)

---

## 核心原则

```
1. 永远不要猜文件格式 — 用逆向验证
2. IDA 静态假设 -> Frida 动态确认 -> 字节级/数学验证收尾
3. 验证过的函数和偏移必须写入 IDA 注释 (持久化)
4. 每一步都要有交叉验证: 假设值 vs 已知值
5. 不信未经验证的假设; 批量验证 (如 365/365 匹配才算通过)
6. 先小批量测试, 再全量跑
```

---

## Phase 1: 侦察 — 文件级观察

### 目标
理解打包文件的总体结构: 压缩方式、魔数、条目布局。

### 步骤

1. **识别资产类型**
   ```
   游戏目录扫描:
     .wad/.pak/.pkg/.archive  -> 资产清单/目录
     .*mesh/.lod/.stream      -> 顶点/索引数据仓库
     .*tex/.texture/.dds      -> 贴图像素仓库
     .*shader/.fx             -> 着色器仓库
     .*toc/.index             -> 仓库的索引/目录
   ```

2. **Hex editor 观察**
   - 文件头部是否明文? -> 否=压缩/加密
   - 尝试常见解压: LZ4 frame, zstd, zlib, Oodle, LZMA
   - 解压后找魔数 (4-8 字节的 ASCII 或特征值)

3. **解压验证**
   ```python
   import lz4.frame
   with open("sample.wad", "rb") as f:
       data = lz4.frame.decompress(f.read())
   print(data[:16])  # 看魔数
   ```

4. **结构模式识别**
   - 固定大小重复块 = TOC/entry table (计算块大小: 文件大小/条目数)
   - 偏移+大小对 = 数据索引
   - hash 值 (16/8 字节) = 资源标识

### 产出
- 压缩方式确认
- 解压后魔数
- 初步结构假设 (header 大小, entry 大小, 数据段位置)

---

## Phase 2: 静态分析 — 找入口 (IDA)

### 目标
从可执行文件中找到游戏自己解析这些文件的代码。

### 步骤

1. **字符串搜索**
   ```
   搜索文件扩展名: ".wad", ".lodpack", ".texpack"
   搜索加载相关词: "Async", "Load", "Stream", "Mount"
   搜索魔数字符串: "WTOC", "GNF" (如果是 ASCII)
   ```

2. **xref 追踪链**
   ```
   字符串 ".xxx"
     ↑ 被引用于
   sub_A (路径构建函数)
     ↑ 被调用于
   sub_B (注册/预缓存函数)
     ↑ 被调用于
   sub_C (运行时查找函数)
     ↑ 被调用于
   sub_D (消费函数 — 这里用数据)
   ```

3. **反编译加载主链**
   - 找到异步加载线程入口
   - 顺着调用链: 文件读取 -> 解压 -> 解析 -> 分发
   - 识别关键函数: parser (读 header/entries), dispatcher (type -> handler)

4. **确认结构体布局**
   ```c
   // 从反编译中提取:
   entryCount = *(int*)(data + OFFSET);     // entry count 在哪
   entry = data + HEADER_SIZE + ENTRY_SIZE * i;  // entry 怎么定位
   type = *(uint16_t*)(entry + 0);          // type 字段在哪
   ```

### 产出
- 加载调用链 (函数地址)
- header 结构假设 (大小, 字段偏移)
- entry 结构假设 (大小, 字段偏移)
- type -> handler 路由机制

---

## Phase 3: 动态验证 — 确认数据流 (Frida)

### 目标
在运行时确认 IDA 分析的假设, 抓取实际数据。

### 关键规则

```
- Frida spawn (-f) 启动, 不能 attach (很多游戏有反作弊)
- MemoryAccessMonitor 可能导致卡死, 优先用 Interceptor.attach
- v17 API: Process.getModuleByName("exe").base 获取基址
- hook 函数入口 (onEnter) 读参数/内存, 出口 (onLeave) 看返回值
```

### Hook 模板

```javascript
var base = Process.getModuleByName("game.exe").base;
var targetAddr = base.add(OFFSET);  // IDA 地址 - imagebase

Interceptor.attach(targetAddr, {
    onEnter: function(args) {
        // args[0], args[1]... = 函数参数
        // 读结构体字段:
        var field = args[0].add(OFFSET).readU32();
        // 读字符串:
        var name = args[0].add(STR_OFFSET).readUtf8String();
        // dump 内存:
        console.log(hexdump(args[0], {length: 256}));
    }
});
```

### 验证内容

| 验证项 | 方法 | 通过标准 |
|--------|------|----------|
| 函数用途 | hook + 调用计数 | 调用次数与预期一致 |
| entry 偏移 | 读内存 + 与已知值交叉验证 | 值与文件数据匹配 |
| type code 映射 | 抓取所有 dispatch | type -> handler 一一对应 |
| 数据编码 | hook memcpy 层 | 数据是纯拷贝还是有解码 |
| 数据流 | hook 链上多个函数 | 从读取到消费的数据连续 |

### 交叉验证技巧

```
entry+0x04 (size)  ↔ memcpy 的长度参数
entry+0x08 (hash)  ↔ lodpack 二分搜索的 key
entry+0x18 (name)  ↔ 文件名模式 (MESH_xxx ↔ MG_xxx)
entry+0x78 (ptr)   ↔ 解压后数据中的位置
```

### 产出
- 所有偏移 frida 确认 (标记 ✅)
- type -> handler 完整映射
- 数据是否有二次编码 (确认 RAW 或编码层)
- entry 结构体完整定义

---

## Phase 4: 格式规范定稿

### 目标
将所有验证过的发现整合成可编程的格式规范。

### 文件格式文档模板

```
文件: .xxx (压缩方式: LZ4/zstd/raw)
  解压后:
  ┌──────────────┐
  │  Header      │  magic, entryCount, dataOffset
  ├──────────────┤
  │  TOC N×Entry │  每条目 EntrySize 字节
  ├──────────────┤
  │  Data 段     │  原始数据
  └──────────────┘

Header (Hsize 字节):
  +0x00  magic[4]
  +0x08  u32  entryCount
  +0x10  u64  dataOffset = Hsize + EntrySize × entryCount

Entry (EntrySize 字节):
  +0x00  u16  typeCode     (类型, 决定 handler)
  +0x04  u32  size         (数据大小)
  +0x08  u64  hash         (0=内联, ≠0=外部仓库)
  +0x18  char[] name       (资源名)
  +0x6D  u8   subType      (子类型)
  +0x78  ptr  dataPtr      (-> raw 数据)
```

### 外部仓库格式 (lodpack/texpack 等)

```
仓库文件 + .toc 索引:
  .toc 条目 (TocEntrySize 字节, 按 hash 排序):
    +0x00  u32  groupIdx
    +0x04  u32  offsetter
    +0x08  u64  hash     ← 二分搜索 key
    +0x10  u32  blockSize
    +0x14  u32  skip

查找路径:
  entry.hash -> .toc 二分搜索 -> groupIdx + offsetter
  -> 仓库文件偏移 = group_offset[groupIdx] + offsetter
  -> 读取 blockSize 字节
```

### 顶点数据格式 (meshbuf)

```
meshbuf 结构:
  offset_array -> sub-mesh 偏移表
  meshSub[i] = base + offset_array[i] + shift(i)

  每个 meshSub:
    +68   u32  vertexCount
    +72   u32  triangleCount
    +96   u32  attrTableOffset
    +100  u32  streamTableOffset
    +104  u64  hash (外部仓库查找 key)

  属性表: 每条目 8B
    semantic(1B) + format(1B) + streamIdx(1B) + ...

  语义码: 0=POSITION 3=TEXCOORD 4=TANGENT 6=NORMAL 1=BLENDWEIGHT 2=BLENDINDICES
  格式码: 0/2/3=4B(float) 1/4/5/6/7=2B(half) 8/9/A/B=1B(byte)
```

### 纹理格式

```
通用块压缩格式 (BC1-BC7):
  magic + format_field + dim_field + mip_field
  format = (fmt_field >> 20) & 0x3F
  width  = (dim_field & 0x3FFF) + 1
  height = ((dim_field >> 14) & 0x3FFF) + 1
  mips   = ((mip_field >> 16) & 0xF) + 1

  像素数据通常在固定偏移 (如 0xFF8)
  数据布局: mip-major, 行内可能有填充对齐

  格式码 -> DXGI:
    BC1=4B/block  BC4=8B/block  BC6H=16B/block  BC7=16B/block

  Mip 填充验证:
    ref_w = next_pow2(W), ref_h = next_pow2(H)
    每 mip 块数用 ref 维度计算, 对齐到 8 (最小), 总对齐到 16
    total_blocks × bytes_per_block == rawSize => 验证通过
```

---

## Phase 5: 模型提取

### 管线

```
遍历所有打包文件
  ↓
解压 (LZ4/zstd/raw)
  ↓
解析 Header + TOC
  ↓
分离条目类型 (MESH / 顶点数据 / 模型定义)
  ↓
名称配对 (MESH_X ↔ VertexData_X)
  ↓
检查 hash:
  hash==0 -> 内联数据 (basePtr = 条目文件偏移)
  hash≠0  -> 外部仓库二分搜索
  ↓
解析顶点属性表 + 流表 -> 顶点布局
  ↓
按格式码提取: POSITION / NORMAL / TEXCOORD / TANGENT / BLEND*
  ↓
构建 GLB (glTF 2.0) -> 写入 .glb
```

### GLB 构建

```python
import trimesh
# 或手动构建 glTF 2.0 二进制:
# JSON header + binary buffer
# attributes: POSITION, NORMAL, TEXCOORD_0, TANGENT
# indices: 16/32-bit based on vertex count
# targets: (可选) morph targets
```

### 验证

```python
import trimesh
mesh = trimesh.load("output.glb")
assert mesh.geometry  # 有几何体
for name, geom in mesh.geometry.items():
    assert len(geom.vertices) > 0
    assert len(geom.faces) > 0
```

---

## Phase 6: 纹理提取

### 管线

```
遍历纹理仓库 + 索引
  ↓
索引解析: hash -> offset -> size
  ↓
读取纹理 header (magic, format, dimensions, mips)
  ↓
按 mip 填充规则计算 rawSize (验证)
  ↓
提取像素数据 (从 imageDataOffset 开始)
  ↓
块解码: texture2ddecoder.decode_bc1/4/6/7(data, W, H) -> BGRA
  ↓
BGRA -> RGBA 转换
  ↓
写入 DDS (DXGI 格式头 + 像素数据)
```

### DDS 头部

```python
# DDS header (124 bytes + 4 bytes magic)
# magic = b"DDS "
# dwMagic2 = 0x00000007 (DX10)
# dxgiFormat = 对应的 DXGI 格式码
# BC1=71, BC1_SRGB=72, BC4=80, BC6H=95, BC7=98, BC7_SRGB=99
```

---

## Phase 7: 材质提取

### 识别材质条目

```
TOC 中的材质相关条目:
  材质定义: 特定 typeCode, name=MAT_xxx
  着色器签名: 特定 typeCode, name=TX_xxx
  纹理引用: 特定 typeCode, name=TX_xxx

数据格式:
  材质: 参数头 (floats) + 着色器字节码 (DXBC/SPIR-V)
  签名: 着色器输入/输出语义 (POSITION, TEXCOORD, NORMAL...)
```

---

## Phase 8: 关联 (模型 ↔ 纹理 ↔ 材质)

### 关联链

```
MESH -> 材质:  通过嵌入 hash 或相邻引用条目
材质 -> 纹理引用: 材质定义后跟纹理签名条目
纹理引用 -> DDS: 引用名称末尾 hex = DDS hash
多纹理:      通过 base name 模糊匹配
LOD 链接:    LOD mesh 继承父 mesh 的纹理
引用解析:    缺失纹理通过引用数据中的二次引用解析
```

### 输出: mapping JSON

```json
{
  "wad": "wad_name",
  "meshes": [{
    "mesh": "MESH_name",
    "mats": ["MAT_HASH"],
    "textures": [
      {"hash": "HASH", "type": "primary|normal|gloss|ao|...", "found": true}
    ]
  }]
}
```

### 预期覆盖率

```
有纹理的 mesh: ~85-90% (无纹理的是 shadow/lod/proxy/locator)
纹理引用找到 DDS: ~99% (缺失的是运行时生成纹理)
```

---

## Phase 9: 目录组织

### 输出结构

```
output/models/
  {region}/                         ← 按游戏区域/关卡分组
    {wad_name}/                     ← 按打包文件分组
      {wad}_MESH_{name}.glb         ← 模型
      materials/                    ← 材质
        {MAT_name}.mat
      textures/                     ← 纹理
        {HASH}.dds
      material_mapping.json         ← 关联映射
    textures/                       ← 区域级共享纹理
      {texpack}/
        {HASH}.dds
```

### 区域分类

```
根据文件名前缀分类到区域目录:
  base_  -> base      (基础场景)
  c_     -> cutscenes (过场动画)
  add_   -> characters (角色)
  其他前缀 -> 对应游戏区域

注意: 整理完目录后再压缩, 不要边整理边压缩
```

---

## Phase 10: 压缩打包

### 策略

- 按 region 分包, 不压成一个巨型文件
- 大 region 按子区域再拆分 (单包 <15GB 方便上传)
- `-mx=3` 平衡速度与压缩率 (游戏数据通常 35-45% 压缩率)
- 不要用硬链接 (跨电脑不可用), 7z 会自动转为独立文件

### 压缩命令

```bash
# 单个区域
7z a -t7z -mx=3 -mmt=8 output.7z "region_dir/*"

# 多子目录压入同一包 (避免 Duplicate filename)
# 方案: 逐目录追加 + -spf2 保留完整路径
7z a -t7z -mx=3 -mmt=8 -spf2 archive.7z "dir1"
7z a -t7z -mx=3 -mmt=8 -spf2 archive.7z "dir2"
```

### 验证 (必须)

```
对每个 .7z:
  1. 7z l 列出包内文件
  2. 统计 .glb / .mat / .dds 数量
  3. 与磁盘对应目录的文件数比对
  4. 全部匹配 = OK, 任何不匹配 = 重新压缩
```

---

## Phase 11: IDA 注释持久化

### 通过 MCP 写入

```python
# 写注释 (items 是列表)
ida.set_comments(items=[
    {"addr": "0xADDR", "comment": "FUNCTION_NAME: 描述. VERIFIED frida+IDA"},
])

# 重命名
ida.py_eval(code="idaapi.set_name(0xADDR, 'FunctionName', idaapi.SN_NOWARN|idaapi.SN_FORCE)")

# 保存 IDB
ida.idb_save({})
```

### 注释格式

```
函数地址: "FUNCTION_NAME: 用途描述. 验证方法"
偏移: "字段名 (类型) - 用途. VERIFIED frida"
```

---

## 踩过的坑与解决方案 (实战总结)

> 以下是实际项目中遇到的所有坑, 按类别整理。每个坑都记录了现象、原因、排查过程和最终解决方案。

### A. Frida / 动态分析类

#### A1. Frida attach 导致游戏崩溃

- **现象**: 游戏运行后 `frida -p <PID>` 附加, 游戏立即崩溃退出
- **原因**: 游戏有反作弊检测, 检测到调试器附加就终止进程
- **排查**: 尝试 x64dbg attach 同样崩溃; 但游戏本身可以正常运行
- **解决**: 用 `frida -f` spawn 模式启动游戏, Frida 在进程创建时就注入, 绕过反附加检测
- **教训**: 优先用 spawn, 不要 attach

#### A2. MemoryAccessMonitor 导致游戏卡死

- **现象**: 在 meshbuf buffer 地址范围下 MemoryAccessMonitor 内存访问断点, 游戏立即卡住, 无法操作
- **原因**: MemoryAccessMonitor 的 overhead 极大, 游戏渲染线程每帧访问大量内存, 全部触发回调导致阻塞
- **排查**: 尝试缩小监控范围 -> 仍然卡; 尝试单线程访问 -> 仍卡
- **解决**: 放弃 MemoryAccessMonitor, 改用 `Interceptor.attach` hook 函数入口/出口, 只在函数调用时读内存
- **教训**: 内存访问断点对实时渲染的游戏不实用; 函数级 hook 足够

#### A3. Frida v17 API 变化

- **现象**: `Module.getExportByName("game.exe", "xxx")` 报错 "函数不存在"
- **原因**: Frida v17 改了 API, 旧写法废弃
- **解决**: 改用 `Process.getModuleByName("game.exe").getExportByName("xxx")`
- **教训**: 升级 Frida 前查 changelog, API 可能 breaking change

#### A4. 游戏需要手动进关卡才能触发资产加载

- **现象**: Frida hook 分发器后, 到游戏主界面没有 dispatch 触发
- **原因**: 资产在进关卡时才按需加载, 主界面不加载关卡资产
- **解决**: Frida spawn 启动到主界面 -> 通知手动进关卡 -> hook 开始捕获数据
- **教训**: 提前规划好需要 hook 什么, 进哪个关卡能触发; 某些资产只在特定场景加载

#### A5. 进关卡后 hook 数据已跑过

- **现象**: 想抓某个 buffer 的解析过程, 但进关卡后游戏已经解析完了, hook 没触发
- **原因**: 游戏在加载关卡时一次性解析所有资产, 等手动操作时已经结束
- **解决**: 要么在主界面就下好 hook 然后进关卡 (捕获加载过程); 要么重启游戏重新来
- **教训**: hook 要在资产加载之前下好, 不能事后补

### B. 格式逆向类

#### B1. Sentinel 值误判为魔数

- **现象**: 在 meshbuf 中发现 `0xFFFFFFFFFFFF2310` 重复出现, 尝试用它作为字段定位锚点, 对部分 meshbuf 有效但很多不匹配
- **原因**: 这个值不是固定魔数, 是一个变量字段, 根据 attribute count 不同而变化
- **排查**: dump 多个不同 meshbuf, 对比该位置的值 -> 发现值会变
- **解决**: 放弃用 sentinel 定位, 改用 offset_array + shift 规则 (`shift = si * 4`) 定位 sub-mesh 字段
- **教训**: 不要用单个样本的特征值做定位; 至少对比 5+ 个样本确认值是否固定

#### B2. hash==0 误判为数据缺失

- **现象**: 大量 MESH 条目的 hash=0, 最初以为数据缺失或格式错误
- **原因**: hash=0 实际表示静态/基础模型, 顶点数据内联在 MG_ 条目中, 不需要外部 lodpack 查找
- **排查**: 对比 hash=0 和 hash≠0 的条目, 发现 hash=0 的条目 MG_ 数据更大 (包含顶点数据)
- **解决**: 
  - hash==0: `basePtr = MG_ 条目的文件偏移` (内联数据)
  - hash≠0: 去 `.lodpack.toc` 二分搜索 (外部数据)
- **教训**: 特殊值 (0, -1, 0xFFFFFFFF) 可能有语义含义, 不是错误

#### B3. 数据二次编码误判

- **现象**: 从 WAD 解压后的数据, 不确定是否还有二次编码层
- **排查**: hook ReadCallback (`memcpy(entry+120, read_buf, size)`), 发现是纯 memcpy, 无解码
- **解决**: 确认 WAD 解压后就是最终格式, 可以直接按字节解析
- **教训**: 如果不确定数据是否解码过, hook memcpy/数据拷贝层, 看源数据 vs 目标数据是否一致

#### B4. 嵌入 WAD 的纹理是引用而非独立纹理

- **现象**: WAD 中发现 GNF 纹理数据, 以为是独立纹理, 提取后发现尺寸/格式不对
- **原因**: WAD 中的 GNF 是引用条目, 指向 texpack 仓库中的实际纹理, 不是独立纹理
- **解决**: 通过 TX 条目 (word0=29) 解析引用关系, 从 texpack 中提取真正的纹理
- **教训**: 打包文件中的"纹理"可能只是引用; 检查数据大小是否合理 (引用条目通常很小)

#### B5. MESH/MG_/MDL_ 三件套配对

- **现象**: 最初只解析 MESH 条目, 发现缺少顶点数据
- **原因**: MESH 条目只有 meshbuf 元数据 (属性表/流表), 顶点数据在 MG_ 条目中, 模型定义在 MDL_ 条目中
- **排查**: Frida 抓取发现三个条目总是成组出现, 名称有对应关系
- **解决**: 名称配对 `MESH_X ↔ MG_X_gpu`, MESH 提供布局, MG_ 提供数据
- **教训**: 一个"模型"可能跨多个 TOC 条目; 用名称模式配对

#### B6. meshSub shift 规则发现

- **现象**: 用 offset_array[i] 定位 sub-mesh, 字段值不对 (vertex count 出现荒谬值)
- **原因**: sub-mesh 字段位置不是简单的 offset_array[i], 还需要一个 shift
- **排查**: dump 多个 sub-mesh, 对比 si=0/1/2 的字段位置 -> 发现 shift = si * 4
- **解决**: `base = sa + offset_array[i] + si * 4`, 所有字段相对 base 计算
- **验证**: 365/365 meshSubs 全部字段合理 -> 100% 匹配
- **教训**: 字段定位要批量验证, 不能只看一个样本; shift/stride 规则要数学确认

#### B7. Mip 填充规则 (最耗时的坑)

- **现象**: GNF 纹理提取后, 像素数据大小与 rawSize 不匹配
- **原因**: PC 版 GNF 的 mip 数据有复杂的填充对齐规则, 不是简单的 mip 链
- **排查过程** (耗时最长):
  1. 尝试标准 mip 链计算 -> 不匹配
  2. 发现需要 next_pow2 参考维度 -> 部分匹配
  3. 发现每 mip 块数需要对齐到 8 -> 更多匹配
  4. 发现总块数需要对齐到 16 -> 100% 匹配
- **最终规则**:
  ```python
  ref_w = next_pow2(W); ref_h = next_pow2(H)
  每 mip: blocks_w = max(8, ceil(mw/pixbl)); blocks_w = align16(blocks_w)
  每 mip: blocks_h = max(8, ceil(mh/pixbl))
  total = sum(blocks_w * blocks_h for each mip)
  # BC1/BC4: total * 8 == rawSize (176,128 for 10 mips)
  # BC7/BC6H: total * 16 == rawSize (90,112 for 9 mips)
  ```
- **教训**: 块压缩纹理的 mip 填充可能有非标准对齐; 逐个变量试, 用 rawSize 做验证锚点

#### B8. BC6H 立方体贴图 arraySize 陷阱

- **现象**: BC6H 格式的立方体贴图提取后, 面数不对, 解码结果错乱
- **原因**: GNF 头部 depth=6 (6 个立方体面), 但实际 arraySize=24 (4 arrays × 6 cube faces)
- **解决**: 解码时按 arraySize=24 处理, 每个 array 包含 6 个面; 不能只看 depth 字段
- **教训**: 立方体贴图的 arraySize 可能是 depth 的倍数; 交叉验证 rawSize / (面数 × 块大小)

#### B9. PC 版 GNF 像素数据是线性的 (非 Morton swizzle)

- **现象**: 按 Morton/Z-order 曲线解码 GNF 像素, 结果完全错乱
- **原因**: PS5 版 GNF 使用 Morton swizzle, 但 PC 版 (pc_le) 像素数据是 **线性布局**
- **解决**: PC 版直接按行优先线性读取, 不需要 deswizzle
- **教训**: 同一格式在不同平台可能有不同的像素布局; 先确认平台再选解码策略

#### B10. WAD batch 边界处理

- **现象**: 计算 WAD 内文件偏移时, 部分条目偏移错误 (0/19697 不匹配 -> 后来发现是初始版本有 bug)
- **原因**: WAD 数据按 batch 组织, 文件偏移计算需要考虑 batch 边界
- **解决**: 通过 entry byte114 bit0 (batch_end) 标记 batch 边界; 模拟 batch 遍历计算偏移
- **验证**: batch 模拟计算文件偏移, 0/19697 不匹配 -> 100% 正确
- **教训**: 打包格式可能有内部 batch/group 分组; 偏移计算要模拟游戏自己的遍历逻辑

#### B11. WAD 解压后数据无二次编码

- **现象**: 从 WAD 解压后的数据, 怀疑还有二次编码层 (如 Oodle/zstd 再压缩)
- **排查**: frida hook dispatch 层, 发现数据已以 `typeCode + 00 00 80` 开头 (明文结构)
- **解决**: 确认 WAD (LZ4) 解压后就是最终 RAW 格式, handler 直接按字节解析, 无解码
- **教训**: 不确定是否有二次编码时, hook 数据拷贝层 (memcpy), 看源 vs 目标是否一致

### C. 磁盘 I/O 类

#### C1. 同物理 HDD 两分区互拷极慢

- **现象**: 从 E: 拷贝到 D: (同一物理 HDD), 速度只有 4.6 files/s
- **原因**: 同一物理磁盘, 磁头在两个分区之间反复寻道, 随机 I/O 瓶颈
- **解决**: 两阶段拷贝: E: -> F:(SSD) -> D:(HDD), 快 7 倍
- **备选**: `robocopy /MT:16 /J` (多线程+无缓冲) 比 Python 快很多
- **教训**: 拷贝大量小文件时, 注意物理磁盘布局; SSD 做中转

#### C2. 硬链接跨电脑不可用

- **现象**: 用硬链接节省磁盘空间 (同卷不占额外空间), 但拷贝到其他电脑后链接失效
- **原因**: 硬链接只在同一卷内有效, 跨卷/跨电脑拷贝时链接关系丢失
- **解决**: 最终打包时用 7z 压缩 (7z 自动将硬链接转为独立文件); 或直接 copy 而非 link
- **教训**: 中间过程可以用硬链接省空间; 最终输出必须是独立文件

#### C3. robocopy /MT:16 /J 比 Python 拷贝快很多

- **现象**: Python shutil.copy 拷贝 127K 文件极慢 (4.6 files/s)
- **原因**: Python 单线程 + 频繁系统调用, 小文件 I/O 瓶颈
- **解决**: 
- **解决**: `robocopy /MT:16 /J` (16 线程 + 无缓冲 I/O) 速度提升数倍
- **备选**: 如果必须用 Python, 用 multiprocessing.Pool 并行拷贝
- **教训**: 批量文件操作优先用系统级工具 (robocopy/xcopy); Python 只做逻辑不做 I/O

### D. 压缩打包类

#### D1. 7z Duplicate filename 错误

- **现象**: `7z a archive.7z @listfile` 报错 "Duplicate filename on disk: materials"
- **原因**: listfile 中多个目录都有 `materials\` 子目录, 7z 不保留父路径导致同名冲突
- **排查**: 尝试 `-spf2` (保留完整路径) -> 解决; 但 listfile 方式仍不稳定
- **解决**: 逐目录追加到同一 archive, 每次用 `-spf2`:
  ```bash
  7z a -t7z -mx=3 -spf2 archive.7z "dir1"
  7z a -t7z -mx=3 -spf2 archive.7z "dir2"  # 追加
  ```
- **教训**: 7z 默认不保留父路径; 多目录有同名子目录时必须用 `-spf2`

#### D2. 压缩时机错误导致包与磁盘不一致

- **现象**: 压缩跑完后做了目录整理 (MAT 合并、冗余目录删除), 导致压缩包内容与磁盘不一致
- **原因**: 压缩和目录整理是并行/串行交叉进行的, 先压的包缺文件, 后整理的目录多了文件
- **具体**: 压缩跑在 13:37-15:23, MAT 合并在 15:39 才跑; 6 个包与磁盘不匹配
- **解决**: 删除不一致的包, 确认磁盘稳定后重新压缩; 压后逐包验证文件数
- **教训**: 压缩必须是最后一步; 压后必须验证 (包内文件数 vs 磁盘文件数)

#### D3. 大区域单包太大

- **现象**: 最大区域 (30K GLB, 137K 文件) 压成单包 34GB, 上传/拷贝不便
- **解决**: 按子区域前缀拆分成多个子包 (如 4-5 个, 每个 <10GB)
- **注意**: 拆分时要覆盖所有子目录, 避免遗漏 (如 zoo/misc/textures 等特殊目录)
- **验证**: 所有子包的文件数之和 = 磁盘总文件数
- **教训**: 拆分后做一次全量验证, 确认没有遗漏的目录

#### D4. 7z 进程卡死产生 0 字节文件

- **现象**: 某个区域的 7z 压缩进程卡死 (运行数小时), 产出 0 字节文件
- **原因**: 可能是磁盘 I/O 超时或内存不足
- **解决**: kill 卡死的 7z 进程, 删除 0 字节文件, 重新压缩
- **教训**: 压缩脚本要支持断点续传 (skip 已完成的); 监控进程状态

#### D5. 前缀匹配特异性 (vanaheim_zoo ≠ vanaheim_architecture_zoo)

- **现象**: 按区域前缀拆分压缩包, 用 "vanaheim_zoo" 作为前缀, 但 "vanaheim_architecture_zoo" 目录没被匹配到
- **原因**: 前缀匹配是精确字符串前缀, "vanaheim_zoo" 不是 "vanaheim_architecture_zoo" 的前缀
- **排查**: 审计发现 3 个 anaheim_*_zoo 目录 + textures + val0* 目录被遗漏
- **解决**: 用更宽泛的前缀 "vanaheim_" 匹配所有子目录; 或显式列出所有目录名
- **教训**: 前缀匹配要验证覆盖率; 拆分后做全量审计 (磁盘文件数 = 所有子包文件数之和)

#### D6. 分包时遗漏特殊目录

- **现象**: 按区域前缀拆分后, 审计发现部分目录 (zoo/misc/textures/val0*) 没有被任何子包覆盖
- **原因**: 拆分逻辑只考虑了主要子区域前缀 (crat/jngl/vanvil/delta/falls), 漏掉了 zoo/misc 等次要目录
- **解决**: 拆分后立即做全量审计: 磁盘文件数 vs 所有子包文件数之和; 发现遗漏后补一个 misc 子包
- **教训**: 拆分逻辑要覆盖所有目录; 不能只按已知前缀, 要有 fallback (catch-all) 子包

#### D7. 7z @listfile 方式不稳定

- **现象**: 7z a archive.7z @listfile.txt 有时正常, 有时报 "Duplicate filename on disk: materials"
- **原因**: listfile 中多个目录都有同名子目录 (如 materials\), 7z 不保留父路径导致冲突
- **排查**: 尝试 -spf2 (保留完整路径) 可以解决 Duplicate 问题, 但 listfile 方式仍偶发失败
- **解决**: 放弃 listfile, 改为逐目录追加:
  ```bash
  7z a -t7z -mx=3 -spf2 archive.7z "dir1"   # 创建
  7z a -t7z -mx=3 -spf2 archive.7z "dir2"   # 追加
  7z a -t7z -mx=3 -spf2 archive.7z "dir3"   # 追加
  `
- **教训**: 7z 的 listfile 模式在有同名子目录时不可靠; 逐目录追加 + -spf2 最稳定

### E. 关联/映射类

#### E1. LOD mesh 无纹理

- **现象**: 大量 LOD (Level of Detail) mesh 没有关联纹理
- **原因**: LOD mesh 在文件中没有独立的材质/纹理引用, 运行时继承父 mesh 的纹理
- **解决**: 通过名称匹配找到父 mesh (LOD mesh 名 = 父 mesh 名 + "_lodX"), 继承父 mesh 的纹理
- **教训**: 无纹理 mesh 不一定是缺失; 可能是 LOD/shadow/proxy 等辅助几何

#### E2. 缺失纹理是运行时生成的

- **现象**: 少量纹理 hash 在所有 texpack 中都找不到
- **原因**: 这些是运行时生成的纹理 (noise map, dynamic material 等), 不存在于文件中
- **解决**: 标记为 "runtime generated", 不再尝试从文件提取
- **教训**: 不是所有纹理都能从文件提取; 预期有 ~1% 缺失是正常的

#### E3. 多纹理模糊匹配

- **现象**: 一个材质引用多个纹理, 但不是所有纹理都有精确 hash 匹配
- **解决**: 通过 TX base name 模糊匹配 word0=29 的 TX 条目, 找到多纹理引用
- **教训**: 纹理引用可能有多种方式 (精确 hash + 模糊名称); 需要多种匹配策略组合

### F. IDA/MCP 类

#### F1. IDA MCP batch rename 无效

- **现象**: `ida.rename(items=[...])` 的 batch 参数不生效
- **解决**: 改用 `ida.py_eval(code="idaapi.set_name(addr, name, flags)")` 直接调用
- **教训**: MCP 工具的 batch 参数可能有 bug; 优先用 py_eval 直接调 IDA API

#### F2. IDA MCP 参数名不匹配

- **现象**: `decompile(address=...)` 报错
- **解决**: 参数名是 `addr` 不是 `address`; `xrefs_to` 用 `addrs` (复数); `get_bytes` 用 `regions`
- **教训**: 查 MCP 工具的参数定义, 不要假设参数名

---

## 复用流程总结

```
1. 侦察: hex editor + 解压尝试 -> 找魔数和结构
2. 静态: IDA 字符串搜索 + xref 追踪 -> 找加载链
3. 动态: Frida spawn + hook 分发器 -> 确认数据流
4. 定格式: hook + 内存读取 + 交叉验证 -> entry 结构体
5. 提取: 按格式写脚本 -> 小批量测试 -> 全量跑
6. 关联: MESH->材质->纹理->DDS 引用链
7. 组织: 按 region/wad 层级整理目录
8. 打包: 分包压缩 + 逐包验证
9. 持久化: IDA 注释 + 格式文档 + 脚本版本管理
```

### 验证体系

```
Layer 1: IDA 静态 -> 理解结构, 形成假设
Layer 2: Frida 动态 -> hook 验证, 抓取运行时数据
Layer 3: 字节级/数学 -> 批量验证, 100% 匹配才算通过
```
