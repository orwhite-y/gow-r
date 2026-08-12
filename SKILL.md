# SKILL: 游戏资产逆向提取 (通用方法论)

> 从任意商业游戏的打包文件中提取 3D 模型、纹理、材质的通用技能。
> 核心: 静态分析(IDA) + 动态验证(Frida) + 字节级确认，三层验证体系。
> 不依赖任何游戏特定知识，所有字段通过逆向获取。

---

## 适用场景

- 游戏使用自定义打包格式 (非标准 zip/pak)
- 无官方 mod 工具或 SDK
- 目标: 从文件中提取 90%+ 可用模型/纹理 (文件级, 非内存级)
- 有可执行文件 + 逆向工具 (IDA/Frida/x64dbg/CE)

---

## 核心原则

```
1. 永远不要猜文件格式 — 用逆向验证
2. IDA 静态假设 -> Frida 动态确认 -> 字节级/数学验证收尾
3. 验证过的函数和偏移必须写入 IDA 注释 (持久化)
4. 每一步都要交叉验证: 假设值 vs 已知值
5. 不信未经验证的假设; 批量验证 (如 N/N 匹配才算通过)
6. 先小批量测试, 再全量跑
7. 特殊值 (0, -1, 0xFFFFFFFF) 可能有语义含义, 不是错误
8. 一个"模型"可能跨多个 TOC 条目; 用名称模式配对
```

---

## Phase 1: 侦察 — 文件级观察

### 目标
理解打包文件的总体结构: 压缩方式、魔数、条目布局。

### 步骤

1. **扫描游戏目录, 识别资产类型**
   ```
   .wad/.pak/.pkg/.archive/.cas  -> 资产清单/目录
   .*mesh/.lod/.stream/.vbuf     -> 顶点/索引数据仓库
   .*tex/.texture/.dds            -> 贴图像素仓库
   .*shader/.fx/.cfxb            -> 着色器仓库
   .*toc/.index/.manifest        -> 仓库的索引/目录
   ```
   按扩展名分组, 统计数量和大小, 初步判断哪种是"清单"、哪种是"数据仓库"。

2. **Hex editor 观察头部**
   - 文件头部是否明文? -> 否 = 压缩/加密
   - 尝试常见解压: LZ4 frame, zstd, zlib, Oodle, LZMA, Deflate
   - 解压后找魔数 (4-8 字节的 ASCII 或特征值)
   - 注意: 魔数可能不在字符串表里 (是二进制比较, 不是字符串搜索)

3. **解压验证**
   ```python
   import lz4.frame  # 或 zstandard, zlib, lzma
   with open("sample_file", "rb") as f:
       data = lz4.frame.decompress(f.read())
   print(data[:16])  # 看魔数
   ```

4. **结构模式识别**
   - 固定大小重复块 = TOC/entry table
     - 计算块大小: 文件大小 / 条目数 (如果能猜出条目数)
     - 常见 entry 大小: 64/96/128/144/256 字节
   - 偏移+大小对 = 数据索引
   - hash 值 (8/16 字节) = 资源标识
   - 字符串 (资源名/路径) = 可读的条目标识

### 产出
- [ ] 压缩方式确认
- [ ] 解压后魔数
- [ ] 初步结构假设 (header 大小, entry 大小, 数据段位置)

---

## Phase 2: 静态分析 — 找入口 (IDA)

### 目标
从可执行文件中找到游戏自己解析这些文件的代码。

### 步骤

1. **字符串搜索 (在 IDA 中)**
   ```
   搜索文件扩展名: ".wad", ".pak", ".lodpack", ".texpack"  (实际游戏用的)
   搜索加载相关词: "Async", "Load", "Stream", "Mount", "Register"
   搜索魔数: 尝试 ASCII 形式 (如文件头 4-8 字节对应的 ASCII)
   搜索 TOC 相关: ".toc", "lodpack.toc", "index"
   ```

2. **xref 追踪链**
   ```
   字符串 ".xxx"
     ^ 被引用于
   sub_A (路径构建函数)
     ^ 被调用于
   sub_B (注册/预缓存函数)
     ^ 被调用于
   sub_C (运行时查找函数)
     ^ 被调用于
   sub_D (消费函数 — 这里用数据)
   ```
   从字符串出发, 顺着 xref 链向上找注册器, 向下找消费者。

3. **反编译加载主链**
   - 找到异步加载线程入口 (搜 "Async", "Thread", "Worker")
   - 顺着调用链: 文件读取 -> 解压 -> 解析 -> 分发
   - 识别关键函数:
     - **parser**: 读 header / entries 的函数
     - **dispatcher**: type -> handler 的路由函数 (通常有 switch/vtable)
     - **handler**: 具体处理某类数据的函数

4. **确认结构体布局**
   ```c
   // 从反编译中提取:
   entryCount = *(int*)(data + OFFSET);           // entry count 在哪
   entry = data + HEADER_SIZE + ENTRY_SIZE * i;   // entry 怎么定位
   type = *(uint16_t*)(entry + 0);                // type 字段在哪
   // 记录每个字段偏移, 后面 Frida 验证
   ```

5. **识别 type -> handler 路由**
   - switch 语句: `switch(type) { case 1: handlerA; case 2: handlerB; ... }`
   - vtable 查找: `handler = vtable[type * 8 + offset]`
   - 记录: type code -> handler 函数地址

### 产出
- [ ] 加载调用链 (函数地址)
- [ ] header 结构假设 (大小, 字段偏移)
- [ ] entry 结构假设 (大小, 字段偏移)
- [ ] type -> handler 路由机制

---

## Phase 3: 动态验证 — 确认数据流 (Frida)

### 目标
在运行时确认 IDA 分析的假设, 抓取实际数据。

### 关键规则

```
- Frida spawn (-f) 启动, 不能 attach (很多游戏有反作弊/反调试)
- MemoryAccessMonitor 可能导致卡死, 优先用 Interceptor.attach
- v17 API: Process.getModuleByName("exe").base 获取基址
- hook 函数入口 (onEnter) 读参数/内存, 出口 (onLeave) 看返回值
- hook 要在资产加载之前下好, 不能事后补
- 游戏可能需要手动进关卡/场景才触发资产加载
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
    },
    onLeave: function(retval) {
        // 看返回值
    }
});
```

### 验证内容

| 验证项 | 方法 | 通过标准 |
|--------|------|----------|
| 函数用途 | hook + 调用计数 | 调用次数与预期一致 |
| entry 偏移 | 读内存 + 与已知值交叉验证 | 值与文件数据匹配 |
| type code 映射 | 抓取所有 dispatch | type -> handler 一一对应 |
| 数据编码 | hook memcpy/数据拷贝层 | 数据是纯拷贝还是有解码 |
| 数据流 | hook 链上多个函数 | 从读取到消费的数据连续 |

### 交叉验证技巧

```
entry 中的 size 字段    <-> memcpy/ReadFile 的长度参数
entry 中的 hash 字段    <-> 外部仓库二分搜索的 key
entry 中的 name 字段    <-> 文件名模式 (MESH_xxx <-> data_xxx)
entry 中的 data ptr     <-> 解压后数据中的对应内容
```
关键: 从文件读出的字节 vs Frida 从内存读出的字节, 逐字节比对一致才算确认。

### 产出
- [ ] 函数用途确认 (hook 调用计数合理)
- [ ] entry 偏移确认 (内存值 = 文件值)
- [ ] type code -> handler 确认
- [ ] 数据是否二次编码确认

---

## Phase 4: 格式规范定稿

### 目标
将验证过的假设整理成精确的格式文档, 供提取脚本使用。

### 文件格式文档模板

```
## 容器格式 (xxx.wad / .pak / .archive)

压缩: LZ4 frame / zstd / zlib / none
解压后结构:
  Header: N 字节
    +0x00: magic (4 bytes ASCII)
    +0x08: entryCount (u32)
  Entry: M 字节/条 (固定大小)
    +0x00: typeCode (u16)
    +0x04: dataSize (u32)
    +0x08: hash (u64) — 0 = 内联数据, != 0 = 外部仓库查找
    +0x18: name (char[N])
    +0x6D: typeCode2 (u8) — 子类型
    +0x78: dataPtr (ptr) — 运行时填充
  Data: 紧跟在 entry table 之后, 按 entry 顺序排列

## 外部仓库格式 (xxx.lodpack / .datapack)

TOC: 每条 K 字节
  +0x00: groupIdx (u32)
  +0x08: hash (u64) — 二分搜索 key
  +0x10: blockSize (u32)
Data: 按 TOC offset 定位

## 顶点数据格式

布局: stream-based (位置/法线/UV 各一个 stream) 或 interleaved
属性表: 描述每个 stream 的格式 (component count, type, normalized)
索引: u16 或 u32, 三角形列表或 strip

## 纹理格式

头部: 魔数 + 宽高 + 格式码 + mip 数 + arraySize
格式码 -> DXGI 映射: (游戏特定, 通过逆向获取)
像素布局: 线性 或 Morton swizzle (平台相关)
```

### 产出
- [ ] 容器格式文档 (header + entry 布局)
- [ ] 外部仓库格式文档 (TOC + data 布局)
- [ ] 顶点数据格式文档
- [ ] 纹理格式文档

---

## Phase 5: 模型提取

### 管线

```
1. 解压容器文件 (LZ4/zstd/etc.)
2. 解析 header + entry table
3. 按 typeCode 筛选模型相关条目
4. 对每个模型条目:
   a. 解析 meshbuf 元数据 (属性表 + stream 表)
   b. 根据 hash 决定数据来源:
      - hash == 0: 顶点数据内联在当前文件 (直接读)
      - hash != 0: 去外部仓库 (lodpack/datapack) 二分搜索
   c. 读取顶点 buffer + 索引 buffer
   d. 按 stream 布局拆分属性 (position, normal, uv, tangent...)
   e. 组装成标准格式 (GLB / OBJ / FBX)
5. 小批量测试 (5-10 个) -> 验证可打开 -> 全量跑
```

### GLB 构建

```python
# 通用 GLB 构建流程
# 1. 收集 vertices (position, normal, texcoord, tangent...)
# 2. 收集 indices (triangle list)
# 3. 用 trimesh 或 pygltflib 构建
# 4. 验证: 用 Blender / gltf-validator 打开
```

### 验证
- [ ] 5-10 个样本能用 Blender 打开
- [ ] 顶点数合理 (不是 0 或荒谬值)
- [ ] 索引数 = 三角形数 × 3
- [ ] 全量跑: 成功率 > 95%

---

## Phase 6: 纹理提取

### 管线

```
1. 识别纹理仓库文件 (texpack / texture archive)
2. 解析纹理 TOC (hash -> offset + size)
3. 对每个纹理:
   a. 读取头部 (魔数 + 宽高 + 格式码 + mip 数)
   b. 格式码映射到标准格式 (BC1/BC4/BC6H/BC7/RGBA8...)
   c. 计算 rawSize (块压缩: 宽高 -> 块数 -> 字节数)
   d. 验证: 计算的 rawSize == 实际数据大小 (100% 匹配)
   e. 解码: 块压缩 -> RGBA, 或直接转 DDS
4. 输出: DDS (保留原始块压缩) 或 PNG/TGA (解码后)
```

### DDS 头部构建

```
DDS_MAGIC = "DDS " (0x20534444)
DDS_HEADER (124 bytes):
  +0x00: size = 124
  +0x04: flags = DDSD_CAPS | DDSD_HEIGHT | DDSD_WIDTH | DDSD_PIXELFORMAT | DDSD_LINEARSIZE
  +0x08: height
  +0x0C: width
  +0x14: mipMapCount
  +0x4C: pfFlags (四 = DDPF_FOURCC)
  +0x50: fourCC (BC1_TYPELESS / BC7_TYPELESS / etc.)
  +0x58: caps = DDSCAPS_TEXTURE
  +0x5C: caps2 = 0 (或 cubemap flag)
```

### 产出
- [ ] 纹理格式码 -> DXGI 映射表
- [ ] rawSize 计算公式 (含 mip 填充规则)
- [ ] 成功率 > 95%

---

## Phase 7: 材质提取

### 识别材质条目

```
1. 在 entry table 中找材质相关 typeCode (通过 Frida dispatch 验证)
2. 材质条目通常包含:
   - 材质名 (字符串)
   - 参数数据 (float 数组: 颜色、粗糙度、金属度等)
   - 着色器引用 (预编译字节码或名称)
   - 纹理引用列表 (hash 或名称)
3. 提取为 .mat / .json 文件, 保留原始参数
```

### 产出
- [ ] 材质条目 typeCode 确认
- [ ] 材质参数提取
- [ ] 着色器/纹理引用解析

---

## Phase 8: 关联 (模型 <-> 纹理 <-> 材质)

### 关联链

```
MESH 条目
  -> 通过嵌入 hash 或相邻条目引用 -> MAT 材质定义
    -> MAT 定义中包含 -> TX 纹理引用条目
      -> TX 名称/hash -> DDS 纹理文件
```

### 关联策略

1. **精确 hash 匹配**: MAT 中的纹理 hash == DDS 文件名 hash
2. **名称模式匹配**: MESH_xxx <-> MG_xxx (同一前缀配对)
3. **LOD 继承**: LOD mesh 名 = 父 mesh 名 + "_lodX", 继承父纹理
4. **模糊匹配**: 通过 base name 模糊匹配多纹理引用
5. **引用解析**: 缺失纹理通过引用数据中的间接引用解析到已有文件

### 输出: mapping JSON

```json
{
  "mesh": "MESH_name",
  "mats": ["MAT_hash"],
  "textures": [
    {"hash": "abc123", "type": "primary", "found": true, "dds": "abc123.dds"},
    {"hash": "def456", "type": "normal",  "found": true, "dds": "def456.dds"}
  ]
}
```

### 预期覆盖率
- 模型提取: 95-100%
- 纹理提取: 95-99% (1-5% 可能是运行时生成, 无法从文件提取)
- 纹理关联: 80-90% (无纹理的 mesh 可能是 shadow/LOD/proxy 等辅助几何)

---

## Phase 9: 目录组织

### 输出结构

```
output/
  {region}/                    # 按游戏区域/章节分
    {wad_name}/                # 按源文件分
      {wad_name}_mesh_{name}_{sub}_{idx}.glb
      materials/
        {MAT_name}.mat
      textures/
        {HASH}.dds
      material_mapping.json    # 该文件的完整关联映射
```

### 区域分类规则
- 按文件名前缀分类 (如 c_ = cutscene, val_ = valhalla, base_ = base)
- 前缀不明确的归入 misc / unsorted
- 每个区域独立可验证 (文件数 = 模型数 + 材质数 + 纹理数)

---

## Phase 10: 压缩打包

### 策略
- 按区域分包 (每个 < 10GB, 便于上传/拷贝)
- 大区域按子前缀拆分成多个子包
- 压缩级别: mx=3 (速度/压缩率平衡, 游戏资产已压缩, 高级别收益小)

### 压缩命令 (7z)

```bash
# 创建新包 (单目录)
7z a -t7z -mx=3 -spf2 archive.7z "dir1"

# 追加目录到已有包
7z a -t7z -mx=3 -spf2 archive.7z "dir2"

# 注意: -spf2 保留完整路径, 避免同名子目录冲突
```

### 验证 (必须)
```bash
# 列出包内文件数
7z l archive.7z | findstr /c:"files"

# 与磁盘文件数对比
(Get-ChildItem "dir1" -Recurse -File).Count
```
包内文件数 == 磁盘文件数 才算通过。

---

## Phase 11: IDA 注释持久化

### 通过 MCP 写入

```python
# 写注释
ida.set_comments(items=[{"addr": "0xADDR", "comment": "DISPATCH: ...VERIFIED frida"}])

# 重命名函数 (batch 参数可能无效, 用 py_eval)
ida.py_eval(code="idaapi.set_name(0xADDR, 'FunctionName', idaapi.SN_NOWARN|idaapi.SN_FORCE)")

# 保存 IDB
ida.idb_save({})
```

### 注释格式

```
函数地址 | 函数名 | 用途 | 验证方法
0xADDR   | WadDispatch | type->handler 路由 | VERIFIED frida+IDA
0xADDR   | ContainerParser | 读 header+entries | VERIFIED frida+IDA
```

所有验证过的发现必须写入 IDA 注释, 上下文压缩后不丢。

---

## 踩过的坑与解决方案 (实战总结)

> 以下是实际项目中遇到的所有坑, 按类别整理。
> 虽然具体值来自某个游戏, 但教训是通用的。

### A. Frida / 动态分析类

#### A1. Frida attach 导致游戏崩溃

- **现象**: 游戏运行后 `frida -p <PID>` 附加, 游戏立即崩溃
- **原因**: 游戏有反作弊/反调试检测, 检测到调试器附加就终止
- **解决**: 用 `frida -f` spawn 模式启动游戏, Frida 在进程创建时就注入
- **教训**: 优先用 spawn, 不要 attach

#### A2. MemoryAccessMonitor 导致游戏卡死

- **现象**: 在 buffer 地址范围下 MemoryAccessMonitor 内存访问断点, 游戏立即卡住
- **原因**: MemoryAccessMonitor overhead 极大, 渲染线程每帧访问大量内存, 全部触发回调导致阻塞
- **解决**: 放弃 MemoryAccessMonitor, 改用 `Interceptor.attach` hook 函数入口/出口
- **教训**: 内存访问断点对实时渲染的游戏不实用; 函数级 hook 足够

#### A3. Frida v17 API 变化

- **现象**: `Module.getExportByName("exe", "xxx")` 报错 "函数不存在"
- **原因**: Frida v17 改了 API, 旧写法废弃
- **解决**: 改用 `Process.getModuleByName("exe").getExportByName("xxx")`
- **教训**: 升级 Frida 前查 changelog, API 可能 breaking change

#### A4. 游戏需要手动进关卡才触发资产加载

- **现象**: Frida hook 分发器后, 到游戏主界面没有 dispatch 触发
- **原因**: 资产在进关卡时才按需加载, 主界面不加载关卡资产
- **解决**: spawn 启动到主界面 -> 通知手动进关卡 -> hook 开始捕获
- **教训**: 提前规划需要 hook 什么, 进哪个关卡能触发

#### A5. 进关卡后 hook 数据已跑过

- **现象**: 想抓某个 buffer 的解析过程, 但进关卡后游戏已经解析完了
- **原因**: 游戏在加载关卡时一次性解析所有资产, 等手动操作时已结束
- **解决**: 在主界面就下好 hook 然后进关卡 (捕获加载过程); 或重启游戏
- **教训**: hook 要在资产加载之前下好, 不能事后补

### B. 格式逆向类

#### B1. Sentinel 值误判为魔数

- **现象**: 在数据中发现某值重复出现, 用它做字段定位锚点, 部分有效但很多不匹配
- **原因**: 这个值不是固定魔数, 是变量字段, 随其他字段变化
- **排查**: dump 多个不同样本, 对比该位置的值 -> 发现值会变
- **解决**: 放弃用 sentinel 定位, 改用 offset_array + shift 规则定位
- **教训**: 不要用单个样本的特征值做定位; 至少对比 5+ 个样本确认值是否固定

#### B2. hash==0 误判为数据缺失

- **现象**: 大量条目 hash=0, 最初以为数据缺失或格式错误
- **原因**: hash=0 实际表示静态/基础模型, 顶点数据内联在当前文件中, 不需要外部仓库查找
- **排查**: 对比 hash=0 和 hash!=0 的条目, 发现 hash=0 的数据更大 (包含顶点数据)
- **解决**:
  - hash==0: 直接从当前文件读 (内联数据)
  - hash!=0: 去外部仓库 TOC 二分搜索
- **教训**: 特殊值 (0, -1, 0xFFFFFFFF) 可能有语义含义, 不是错误

#### B3. 数据二次编码误判

- **现象**: 从容器解压后的数据, 不确定是否还有二次编码层
- **排查**: hook 数据拷贝层 (memcpy), 发现是纯 memcpy, 无解码
- **解决**: 确认解压后就是最终格式, 可以直接按字节解析
- **教训**: 不确定数据是否解码过时, hook memcpy 层, 看源数据 vs 目标数据是否一致

#### B4. 容器内嵌纹理是引用而非独立纹理

- **现象**: 容器中发现纹理数据, 以为是独立纹理, 提取后发现尺寸/格式不对
- **原因**: 容器中的纹理是引用条目, 指向外部纹理仓库中的实际纹理
- **解决**: 通过材质条目解析引用关系, 从外部仓库提取真正的纹理
- **教训**: 打包文件中的"纹理"可能只是引用; 检查数据大小是否合理 (引用条目通常很小)

#### B5. 模型跨多个 TOC 条目

- **现象**: 最初只解析模型条目, 发现缺少顶点数据
- **原因**: 模型条目只有元数据 (属性表/流表), 顶点数据在另一个条目中, 模型定义在第三个条目中
- **排查**: Frida 抓取发现多个条目总是成组出现, 名称有对应关系
- **解决**: 名称配对 (如 MESH_x <-> DATA_x), 一个提供布局, 另一个提供数据
- **教训**: 一个"模型"可能跨多个 TOC 条目; 用名称模式配对

#### B6. sub-mesh shift 规则发现

- **现象**: 用 offset_array[i] 定位 sub-mesh, 字段值不对 (vertex count 出现荒谬值)
- **原因**: sub-mesh 字段位置不是简单的 offset_array[i], 还需要一个 shift
- **排查**: dump 多个 sub-mesh, 对比 si=0/1/2 的字段位置 -> 发现 shift = si * 4
- **解决**: `base = sa + offset_array[i] + si * shift_value`, 所有字段相对 base 计算
- **验证**: N/N sub-meshes 全部字段合理 -> 100% 匹配
- **教训**: 字段定位要批量验证, 不能只看一个样本; shift/stride 规则要数学确认

#### B7. 块压缩纹理 mip 填充规则 (最耗时的坑)

- **现象**: 纹理提取后, 像素数据大小与 rawSize 不匹配
- **原因**: 块压缩纹理的 mip 数据有复杂的填充对齐规则, 不是简单的 mip 链
- **排查过程** (耗时最长):
  1. 尝试标准 mip 链计算 -> 不匹配
  2. 发现需要 next_pow2 参考维度 -> 部分匹配
  3. 发现每 mip 块数需要对齐到 8 -> 更多匹配
  4. 发现总块数需要对齐到 16 -> 100% 匹配
- **最终规则** (通用思路):
  ```python
  ref_w = next_pow2(W); ref_h = next_pow2(H)
  每 mip: blocks_w = max(8, ceil(mw/pixbl)); blocks_w = align16(blocks_w)
  每 mip: blocks_h = max(8, ceil(mh/pixbl))
  total = sum(blocks_w * blocks_h for each mip)
  # BC1/BC4: total * 8 == rawSize
  # BC7/BC6H: total * 16 == rawSize
  ```
- **教训**: 块压缩纹理的 mip 填充可能有非标准对齐; 逐个变量试, 用 rawSize 做验证锚点

#### B8. 立方体贴图 arraySize 陷阱

- **现象**: 立方体贴图提取后, 面数不对, 解码结果错乱
- **原因**: 头部 depth=6 (6 个立方体面), 但实际 arraySize 可能是 depth 的倍数 (如 4 arrays x 6 faces = 24)
- **解决**: 解码时按实际 arraySize 处理; 交叉验证 rawSize / (面数 x 块大小)
- **教训**: 立方体贴图的 arraySize 可能是 depth 的倍数; 不能只看 depth 字段

#### B9. 像素布局平台差异 (线性 vs Morton swizzle)

- **现象**: 按 Morton/Z-order 曲线解码像素, 结果完全错乱
- **原因**: 同一格式在不同平台可能有不同像素布局 (如主机版用 Morton swizzle, PC 版用线性)
- **解决**: 先确认平台, PC 版通常是线性布局, 不需要 deswizzle
- **教训**: 同一格式在不同平台可能有不同像素布局; 先确认平台再选解码策略

#### B10. batch/group 边界处理

- **现象**: 计算文件内偏移时, 部分条目偏移错误
- **原因**: 数据按 batch/group 组织, 文件偏移计算需要考虑 batch 边界
- **解决**: 找到 batch_end 标记位 (通常是 entry 某字节的 bit0), 模拟 batch 遍历计算偏移
- **验证**: batch 模拟计算文件偏移, 0/N 不匹配 -> 100% 正确
- **教训**: 打包格式可能有内部 batch/group 分组; 偏移计算要模拟游戏自己的遍历逻辑

#### B11. 解压后数据无二次编码

- **现象**: 从容器解压后的数据, 怀疑还有二次编码层 (如 Oodle/zstd 再压缩)
- **排查**: frida hook dispatch 层, 发现数据已是明文结构 (类型码开头)
- **解决**: 确认容器解压后就是最终 RAW 格式, handler 直接按字节解析, 无解码
- **教训**: 不确定是否有二次编码时, hook 数据拷贝层 (memcpy), 看源 vs 目标是否一致

### C. 磁盘 I/O 类

#### C1. 同物理 HDD 两分区互拷极慢

- **现象**: 从 A: 拷贝到 B: (同一物理 HDD), 速度只有 ~5 files/s
- **原因**: 同一物理磁盘, 磁头在两个分区间反复寻道, 随机 I/O 瓶颈
- **解决**: 两阶段拷贝: A: -> SSD -> B:, 快 7 倍
- **备选**: `robocopy /MT:16 /J` (多线程+无缓冲) 比 Python 快很多
- **教训**: 拷贝大量小文件时, 注意物理磁盘布局; SSD 做中转

#### C2. 硬链接跨电脑不可用

- **现象**: 用硬链接节省磁盘空间 (同卷不占额外空间), 但拷贝到其他电脑后链接失效
- **原因**: 硬链接只在同一卷内有效, 跨卷/跨电脑拷贝时链接关系丢失
- **解决**: 最终打包时用 7z 压缩 (7z 自动将硬链接转为独立文件); 或直接 copy 而非 link
- **教训**: 中间过程可以用硬链接省空间; 最终输出必须是独立文件

#### C3. robocopy /MT:16 /J 比 Python 拷贝快很多

- **现象**: Python shutil.copy 拷贝 100K+ 文件极慢 (~5 files/s)
- **原因**: Python 单线程 + 频繁系统调用, 小文件 I/O 瓶颈
- **解决**: `robocopy /MT:16 /J` (16 线程 + 无缓冲 I/O) 速度提升数倍
- **备选**: 如果必须用 Python, 用 multiprocessing.Pool 并行拷贝
- **教训**: 批量文件操作优先用系统级工具 (robocopy/xcopy); Python 只做逻辑不做 I/O

### D. 压缩打包类

#### D1. 7z Duplicate filename 错误

- **现象**: `7z a archive.7z @listfile` 报错 "Duplicate filename on disk: materials"
- **原因**: listfile 中多个目录都有同名子目录, 7z 不保留父路径导致冲突
- **解决**: 逐目录追加到同一 archive, 每次用 `-spf2`:
  ```bash
  7z a -t7z -mx=3 -spf2 archive.7z "dir1"   # 创建
  7z a -t7z -mx=3 -spf2 archive.7z "dir2"   # 追加
  ```
- **教训**: 7z 默认不保留父路径; 多目录有同名子目录时必须用 `-spf2`

#### D2. 压缩时机错误导致包与磁盘不一致

- **现象**: 压缩跑完后做了目录整理, 导致压缩包内容与磁盘不一致
- **原因**: 压缩和目录整理交叉进行, 先压的包缺文件, 后整理的目录多了文件
- **解决**: 删除不一致的包, 确认磁盘稳定后重新压缩; 压后逐包验证文件数
- **教训**: 压缩必须是最后一步; 压后必须验证 (包内文件数 vs 磁盘文件数)

#### D3. 大区域单包太大

- **现象**: 最大区域 (30K+ 文件) 压成单包 30GB+, 上传/拷贝不便
- **解决**: 按子区域前缀拆分成多个子包 (如 4-5 个, 每个 < 10GB)
- **注意**: 拆分时要覆盖所有子目录, 避免遗漏
- **验证**: 所有子包的文件数之和 = 磁盘总文件数
- **教训**: 拆分后做一次全量验证, 确认没有遗漏的目录

#### D4. 7z 进程卡死产生 0 字节文件

- **现象**: 某个区域的 7z 压缩进程卡死 (运行数小时), 产出 0 字节文件
- **原因**: 可能是磁盘 I/O 超时或内存不足
- **解决**: kill 卡死的 7z 进程, 删除 0 字节文件, 重新压缩
- **教训**: 压缩脚本要支持断点续传 (skip 已完成的); 监控进程状态

#### D5. 前缀匹配特异性

- **现象**: 按区域前缀拆分压缩包, 用 "region_zoo" 作为前缀, 但 "region_architecture_zoo" 目录没被匹配到
- **原因**: 前缀匹配是精确字符串前缀, "region_zoo" 不是 "region_architecture_zoo" 的前缀
- **解决**: 用更宽泛的前缀 "region_" 匹配所有子目录; 或显式列出所有目录名
- **教训**: 前缀匹配要验证覆盖率; 拆分后做全量审计 (磁盘文件数 = 所有子包文件数之和)

#### D6. 分包时遗漏特殊目录

- **现象**: 按区域前缀拆分后, 审计发现部分目录没有被任何子包覆盖
- **原因**: 拆分逻辑只考虑了主要子区域前缀, 漏掉了 zoo/misc/textures 等次要目录
- **解决**: 拆分后立即做全量审计: 磁盘文件数 vs 所有子包文件数之和; 发现遗漏后补一个 misc 子包
- **教训**: 拆分逻辑要覆盖所有目录; 不能只按已知前缀, 要有 fallback (catch-all) 子包

#### D7. 7z @listfile 方式不稳定

- **现象**: `7z a archive.7z @listfile.txt` 有时正常, 有时报 "Duplicate filename"
- **原因**: listfile 中多个目录有同名子目录, 7z 不保留父路径导致冲突
- **解决**: 放弃 listfile, 改为逐目录追加 + `-spf2`
- **教训**: 7z 的 listfile 模式在有同名子目录时不可靠; 逐目录追加最稳定

### E. 关联/映射类

#### E1. LOD mesh 无纹理

- **现象**: 大量 LOD (Level of Detail) mesh 没有关联纹理
- **原因**: LOD mesh 在文件中没有独立的材质/纹理引用, 运行时继承父 mesh 的纹理
- **解决**: 通过名称匹配找到父 mesh (LOD mesh 名 = 父 mesh 名 + "_lodX"), 继承父 mesh 的纹理
- **教训**: 无纹理 mesh 不一定是缺失; 可能是 LOD/shadow/proxy 等辅助几何

#### E2. 缺失纹理是运行时生成的

- **现象**: 少量纹理 hash 在所有纹理仓库中都找不到
- **原因**: 这些是运行时生成的纹理 (noise map, dynamic material 等), 不存在于文件中
- **解决**: 标记为 "runtime generated", 不再尝试从文件提取
- **教训**: 不是所有纹理都能从文件提取; 预期有 ~1% 缺失是正常的

#### E3. 多纹理模糊匹配

- **现象**: 一个材质引用多个纹理, 但不是所有纹理都有精确 hash 匹配
- **解决**: 通过 base name 模糊匹配纹理引用条目, 找到多纹理引用
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
1. 侦察:     hex editor + 解压尝试 -> 找魔数和结构
2. 静态:     IDA 字符串搜索 + xref 追踪 -> 找加载链
3. 动态:     Frida spawn + hook 分发器 -> 确认数据流
4. 定格式:   hook + 内存读取 + 交叉验证 -> entry 结构体
5. 提取:     按格式写脚本 -> 小批量测试 -> 全量跑
6. 关联:     MESH -> 材质 -> 纹理 -> DDS 引用链
7. 组织:     按 region/wad 层级整理目录
8. 打包:     分包压缩 + 逐包验证
9. 持久化:   IDA 注释 + 格式文档 + 脚本版本管理
```

### 验证体系

```
Layer 1: IDA 静态  -> 理解结构, 形成假设
Layer 2: Frida 动态 -> hook 验证, 抓取运行时数据
Layer 3: 字节级/数学 -> 批量验证, 100% 匹配才算通过
```
