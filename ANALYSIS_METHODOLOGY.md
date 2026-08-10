# 逆向分析流程：如何找到关键函数与偏移

> 本文档记录了 GoWR WAD 拆包过程中，从零开始逆向找到所有关键函数和结构体偏移的完整分析路径。
> 不是事后总结，是实际走过的路，包括弯路和验证方法。

---

## 目录

1. [分析起点](#1-分析起点)
2. [Phase 1: IDA 静态分析 - 找入口](#2-phase-1-ida-静态分析---找入口)
3. [Phase 2: Frida 动态验证 - 确认数据流](#3-phase-2-frida-动态验证---确认数据流)
4. [Phase 3: Entry 结构体偏移逆向](#4-phase-3-entry-结构体偏移逆向)
5. [Phase 4: Mesh 管线追踪](#5-phase-4-mesh-管线追踪)
6. [Phase 5: Lodpack 系统逆向](#6-phase-5-lodpack-系统逆向)
7. [Phase 6: meshbuf 字段定位](#7-phase-6-meshbuf-字段定位)
8. [Phase 7: 纹理格式逆向](#8-phase-7-纹理格式逆向)
9. [验证方法论总结](#9-验证方法论总结)
10. [踩过的坑](#10-踩过的坑)

---

## 1. 分析起点

### 1.1 已知信息

```
format.txt (早期 GoW 格式参考):
  .wad       = 资产清单 + mesh/rig 定义
  .lodpack   = 网格顶点/索引缓冲 (分 LOD)
  .texpack   = 贴图像素 (GNF 格式)
  .toc       = 仓库的货架清单
  .shaderpack = 预编译着色器
```

> **注意**：format.txt 是早期游戏的格式，只能参考。具体字段必须靠逆向验证。

### 1.2 第一步：文件级观察

用 hex editor 打开一个 `.wad` 文件，观察到：
- 文件头部不是明文 → 压缩过的
- 尝试 LZ4 解压 → 成功
- 解压后开头 4 字节 = `WTOC` → 这就是 WAD 的魔数

```python
import lz4.frame
with open("r_perm.wad", "rb") as f:
    data = lz4.frame.decompress(f.read())
print(data[:4])  # b'WTOC'
```

### 1.3 关键决策

从这里开始，不靠猜文件格式，而是去 **逆向游戏可执行文件**，看游戏自己怎么解析这些数据。

---

## 2. Phase 1: IDA 静态分析 - 找入口

### 2.1 字符串搜索

在 IDA 中打开 `GoWR.exe`，搜索关键字符串：

| 搜索字符串 | 命中 | 意义 |
|-----------|------|------|
| `"WTOC"` | 无直接命中 | 魔数不在字符串表里（是二进制数据） |
| `".wad"` | 多处命中 | 文件扩展名引用 |
| `".lodpack"` | 多处命中 | → 找到 lodpack 加载代码 |
| `".texpack"` | 多处命中 | → 找到纹理加载代码 |
| `"WadAsync"` | 命中 | → WAD 异步加载线程入口 |
| `"lodpack.toc"` | 命中 | → lodpack TOC 加载器 |

### 2.2 从字符串到函数

通过 `.lodpack` 字符串的交叉引用（xref），找到引用它的函数：

```
IDA xref 追踪链:
  ".lodpack" 字符串
    ↑ 被引用于
  sub_1403A1DD0  ← Lodpack TOC 加载器
    ↑ 被调用于
  sub_1403A15F0  ← 注册 lodpack + 预缓存
    ↑ 被调用于
  sub_1403A1820  ← 运行时 lodpack 查找
    ↑ 被调用于
  sub_1405FA610  ← Mesh lodpack resolver
```

### 2.3 找到 WAD 加载主链

从 `"WadAsync"` 字符串的 xref，找到异步加载线程，然后顺着调用链向下：

```
WadAsyncLoadingThread
  ↓
sub_140393E20 (0x140393E20)  ← WAD 多条目处理器
  ↓ 调用
sub_1403B3980 (0x1403B3980)  ← WTOC parser
  ↓ 读取
  64B header + N × 144B entries
  ↓ 返回
sub_140393E20 继续处理
  ↓ 调用
WadBatchProcessInner (内部循环)
  ↓ 每个条目调用
WadTypeHandlerLookup(entry[0])  ← 查找 handler
  ↓ 调用
WadDispatch (0x140391140)  ← 分发器
  ↓ 通过
  vtable+120 → 具体 handler
```

### 2.4 分析 WTOC Parser (sub_1403B3980)

反编译 `sub_1403B3980`，观察它读取数据的模式：

```c
// IDA 反编译 (简化)
__int64 WtocParser(__int64 a1, ...) {
    // 读 64 字节 header
    entryCount = *(int*)(data + 8);     // +0x08: 条目数
    
    // 读 144 字节/条目的 TOC
    for (i = 0; i < entryCount; i++) {
        entry = data + 64 + 144 * i;   // 每条目 144B
        type = *(uint16_t*)(entry + 0); // +0x00: 类型
        // ...
    }
}
```

**关键发现**：
- Header = 64 字节，entryCount 在 +0x08
- 每条目 = 144 字节（从 `144LL * n64` 确认）
- 数据段起始 = `64 + 144 * entryCount`

### 2.5 分析分发器 (WadDispatch, 0x140391140)

```c
// IDA 反编译
__int64 WadDispatch(__int64 entry, unsigned int type_code, __int64 data_ptr) {
    v3 = (unsigned __int8)type_code;  // 取低字节作为 handler 索引
    
    // 从 TLS 查 handler
    v8 = *(QWORD*)(TLS[TlsIndex] + 4464 + 8 * v3);
    if (!v8) {
        if (qword_143A0CD58)
            v8 = *(QWORD*)(8 * v3 + qword_143A0CD58);  // fallback: 全局表
    }
    
    // 通过 vtable+120 调用 handler
    return (*(handler_obj + 120))(handler_obj, entry, type_code, data_ptr);
}
```

**关键发现**：
- `type_code` 的低字节 = handler 索引
- handler 存在 TLS (Thread Local Storage) 中
- 通过 vtable+120 调用
- 这是一个**分发器模式**：一个入口，根据 type 路由到不同 handler

### 2.6 分析批量处理器 (WadBatchProcessInner)

```c
// IDA 反编译 (简化)
char WadBatchProcessInner(__int64 ctx, int start, uint64 end) {
    v6 = (uint16_t*)(*(QWORD*)(ctx + 72) + 144LL * start);  // 指向 TOC 条目
    do {
        n33 = *v6;  // entry[0] = type code
        
        if (n33 == 19) {
            sub_1405AF720(v6);  // type 19 特殊处理
        } else if (n33 != 21) {  // type 21 跳过
            // 检查 entry[111] (b111): sub-type
            // 如果 (b111 - 5) > 2，即 b111 不在 {5,6,7} 范围，则处理
            if ((*(BYTE*)(v6 + 111) - 5) > 2) {
                v16 = WadTypeHandlerLookup(*v6);  // 查 handler
                if (v16) v16(v6);  // 调用
            }
        }
        
        v6 += 72;  // u16* += 72 = 144 字节，下一条目
    } while (++n64_1 < end);
}
```

**关键发现**：
- `v6 += 72`（u16 指针），即 144 字节/条目 → 确认条目大小
- `entry[0]` (u16) = type code
- `entry[111]` (byte) = sub-type，值 5/6/7 时跳过
- `entry[2]` (u16) = flags，bit 10 (0x400) 有特殊含义

---

## 3. Phase 2: Frida 动态验证 - 确认数据流

### 3.1 为什么需要 Frida

IDA 静态分析能看出代码结构，但看不到：
- **运行时实际传了什么 type_code**
- **entry 结构体在内存里长什么样**
- **数据从哪来到哪去**
- **哪些函数实际被调用了，调了多少次**

### 3.2 Frida 启动方式

```bash
# 必须 spawn，不能 attach
# attach 会导致游戏反作弊检测，直接崩溃
frida -f "E:\God of War Ragnarok\GoWR.exe" -l hook_wad.js
```

### 3.3 Hook 分发器 (WadDispatch)

```javascript
// hook_wad.js
var base = Process.getModuleByName("GoWR.exe").base;
var dispatchAddr = base.add(0x391140);  // 0x140391140 - 0x140000000

Interceptor.attach(dispatchAddr, {
    onEnter: function(args) {
        var entry = args[0];
        var typeCode = args[1].toInt32();
        var dataPtr = args[2];
        
        // 读 entry 内存
        var word0 = entry.readU16();        // +0x00: type
        var size = entry.add(4).readU32();   // +0x04: size
        var name = entry.add(0x18).readUtf8String();  // +0x18: name
        var hash = entry.add(8).readU64();   // +0x08: hash
        
        console.log(
            "type=" + typeCode.toString(16) +
            " word0=" + word0.toString(16) +
            " size=" + size +
            " hash=" + hash.toString(16) +
            " name=" + name
        );
    }
});
```

### 3.4 Frida 抓到的关键数据

**Type Code -> Handler 映射**（5351 次 dispatch 确认）：

```
type_code=0x0c  → handler=base+0x3D7730  (COMMON, MESH/MG/MDL 组)
type_code=0x0a  → handler=base+0x3D7730  (mesh)
type_code=0x02  → handler=base+0x3D7730  (common)
type_code=0x01  → handler=base+0x597600  (未知)
type_code=0x10  → handler=base+0x4AD130  (未知)
type_code=0x1a  → handler=base+0x4B50F0  (未知)
```

**Type 0x0c 子类型确认**（MESH/MG/MDL 三件套）：

```
抓到的数据起始字节:
  0c 00 0a 00 ...  → typeCode=0xa000c  → MESH_ 前缀  (如 MESH_snowchunks_0, 328B)
  0c 00 01 00 ...  → typeCode=0x1000c  → MG_ 前缀    (如 MG_snowchunks_0, 188B)
  0c 00 02 10 ...  → typeCode=0x1002000c → MDL_ 前缀  (如 MDL_snowchunks, 56B)
```

**Dispatch 数据格式确认**：

```
到达 sub_1403D7730 (common handler) 时:
  0c 00 00 80 00 00 00 00 ...  → typeCode=0x8000000c
  → 数据已解码（不再是压缩态）
```

### 3.5 关键验证：数据无二次编码

通过 hook WadReadCallback (0x140393940)：

```javascript
Interceptor.attach(base.add(0x393940), {
    onEnter: function(args) {
        var dst = args[0];  // entry+120
        var src = args[1];  // read_buf
        var size = args[2].toInt32();
        
        console.log("memcpy: dst=" + dst + " src=" + src + " size=" + size);
        // 读 src 前 16 字节
        console.log("  data: " + hexdump(src, {length: 16}));
    }
});
```

**结果**：`memcpy(entry+120, read_buf, entry+4_size)` — 纯拷贝，无解码。
WAD 解压后的数据就是最终格式，没有二次编码层。

---

## 4. Phase 3: Entry 结构体偏移逆向

### 4.1 方法：Hook + 内存读取

Hook `sub_1405AF220`（Entry 处理函数），参数 `a1` 就是 entry 指针：

```javascript
Interceptor.attach(base.add(0x5AF220), {
    onEnter: function(args) {
        var entry = args[0];
        
        // 系统性地读不同偏移，看哪个有意义
        console.log("=== Entry at " + entry + " ===");
        console.log("+0x00 word0:  " + entry.readU16());
        console.log("+0x04 size:   " + entry.add(4).readU32());
        console.log("+0x08 hash:   " + entry.add(8).readU64());
        console.log("+0x18 name:   " + entry.add(0x18).readUtf8String());
        console.log("+0x64 flag:   " + entry.add(0x64).readU32());
        console.log("+0x6C t108:   " + entry.add(0x6C).readU8().toString(16));
        console.log("+0x6D t109:   " + entry.add(0x6D).readU8().toString(16));
        console.log("+0x6E t110:   " + entry.add(0x6E).readU8().toString(16));
        console.log("+0x78 dataptr:" + entry.add(0x78).readPointer());
    }
});
```

### 4.2 偏移验证过程

不是一次读对的，是逐步试出来的：

```
第 1 轮: 猜 +0x00 是 type → 确认 (u16, 值=1=MESH, 29=MG_)
第 2 轮: 猜 +0x04 是 size → 确认 (与 WadReadCallback 的 size 参数一致)
第 3 轮: 猜 +0x08 是 hash → 确认 (0=内联, ≠0=lodpack 查找 key)
第 4 轮: 试 +0x18 读字符串 → 确认是资源名 (如 "MESH_snowchunks_0")
第 5 轮: 试 +0x6C → 0x0a=MESH, 0x01=MG, 0x02=MDL
第 6 轮: 试 +0x6D → type_code (0x0a=mesh, 0x0c=组)
第 7 轮: 试 +0x78 → 数据指针 (指向 WAD raw 数据)
```

每个偏移都通过与 **已知值** 交叉验证：
- `+0x04 size` ↔ WadReadCallback 的 memcpy 长度
- `+0x08 hash` ↔ lodpack 二分搜索的 key
- `+0x18 name` ↔ 文件名模式（MESH_xxx ↔ MG_xxx_gpu）
- `+0x78 dataptr` ↔ 解压后 WAD 数据中的位置

### 4.3 最终确认的 Entry 结构

```
Entry (144 字节, frida 全部验证):
  +0x00  u16   word0 (类型码: 1=MESH, 29=MG_)
  +0x02  u16   flags (bit10=0x400)
  +0x04  u32   size (数据大小)
  +0x08  u64   hash (0=内联, ≠0=外部 lodpack)
  +0x18  char  name[80] (资源名)
  +0x68  u32   align (对齐)
  +0x6C  u8    t108 (子类型高字节)
  +0x6D  u8    t109 (type_code)
  +0x6E  u8    t110
  +0x6F  u8    b111 (sub-type: 5/6/7=跳过)
  +0x72  u16   byte114 (bit0=batch_end)
  +0x78  ptr   data_ptr (→ WAD raw 数据)
```

---

## 5. Phase 4: Mesh 管线追踪

### 5.1 从分发器到 mesh 处理

已知 type 0x0c 的 MESH/MG/MDL 组都走 common handler (0x1403D7730)。
需要找到 common handler 内部如何路由到 mesh-specific 处理。

```c
// sub_1403D7730 (common handler, 简化)
// 到达时数据已解码，以 type_code+00 00 80 开头
// 二次分发到 type-specific handler
```

通过 IDA 分析 sub_1403D7730 的内部调用，找到它调用的 mesh 处理函数链：

```
sub_1403D7730 (common handler)
  ↓ 内部分发
sub_1405E4920 (mesh data processor)  ← 处理 mesh 数据
  ↓ 调用
sub_1405E5090 (per-LOD mesh setup)   ← 每个 LOD 级别设置
  ↓ 调用
sub_1405E5700 (vertex buffer setup)  ← 顶点缓冲初始化
```

### 5.2 分析 mesh data processor (sub_1405E4920)

```c
// IDA 反编译 (简化)
__int64 sub_1405E4920(__int64 a1, __int64 a2, __int64 a3, __int64 a4) {
    v4 = *(uint16_t*)(a3 + 80);  // mesh index
    
    // 位图操作: 清除 mesh 在位图中的占用位
    v7 = (_DWORD*)(*(QWORD*)(a1 + 208) + 4 * (v4 >> 5));
    *v7 &= ~(1 << (*(_WORD*)(a3 + 80) & 0x1F));
    
    // 存储 mesh 对象指针
    *(QWORD*)(*(QWORD*)(a1 + 224) + 8 * v4) = a2;
    
    // 调用 vertex buffer setup
    sub_1405E5700(a3, a4, *(QWORD*)(a1 + 16) + (v4 << 6), a2);
    
    // LOD 循环
    v9 = *(uint32_t*)(a1 + 88) / *(int*)(a1 + 24);  // LOD count
    do {
        // 对每个 LOD 级别:
        // v12 = stream index (从 a1+80 表读取)
        // v13 = stream data offset
        // 调用 per-LOD setup
        result = sub_1405E5090(
            *(QWORD*)(a1 + 48) + 960LL * v12,  // stream object
            a3,                                  // mesh entry
            v13,                                 // stream data
            *(QWORD*)(a1 + 16) + (v11 << 6),   // mesh slot
            *(BYTE*)(a3 + 131),                 // flags
            a1 + 96                              // context
        );
    } while (++v8 < v9);
}
```

**关键发现**：
- `a3 + 80` (u16) = mesh index
- `a3 + 131` (u8) = mesh flags
- `a1 + 88 / a1 + 24` = LOD count
- `960 * v12` = 每个 stream 对象大小 960 字节
- `v4 << 6` (×64) = 每个 mesh slot 64 字节

### 5.3 分析 vertex buffer setup (sub_1405E5700 / vbsetup)

这个函数设置顶点缓冲，从中可以提取：
- 顶点属性表的位置和格式
- 流（stream）表的结构
- 语义码到属性槽的映射

```c
// vbsetup_decomp.c 中的关键模式:
// v7 = *(QWORD*)(a2 + 112)  ← 属性位掩码 (64-bit, 每 4 bit 一个属性)
// 遍历 v7 的每个 nibble:
//   如果 nibble != 0xF → 有效属性
//   属性索引 = a2 + 96 + 8 * nibble  ← 属性描述符位置
//   属性数据 = v6 + 40 * *(uint8_t*)(attr_desc + 4)  ← 属性数据位置
```

**关键发现**：
- `a2 + 112` (u64) = 属性位掩码，每 4 bit 代表一个属性槽
- `0xF` = 空槽（无效属性）
- 属性描述符在 `a2 + 96 + 8 * index`
- 属性数据在 `v6 + 40 * attr_desc[4]`

### 5.4 分析 vdeclbinder (顶点声明绑定器)

```c
// vdeclbinder_decomp.c
// 将语义码 + 格式码绑定为顶点声明
// 语义: POSITION(0), BLENDWEIGHT(1), BLENDINDICES(2), TEXCOORD(3),
//        TANGENT(4), BINORMAL(5), NORMAL(6), COLOR(9)
// 格式: 0/2/3=4B, 1/4/5/6/7=2B, 8/9/A/B=1B
```

---

## 6. Phase 5: Lodpack 系统逆向

### 6.1 从 IDA xref 追踪

从 `.lodpack` 字符串开始：

```
IDA xref 链:
  ".lodpack" 字符串
    ↑ sub_1403A1DD0 引用 (构建 .lodpack.toc 路径, type 7)
    ↑ sub_1403A15F0 调用 (注册 lodpack + 预缓存)
    ↑ sub_1403A1820 调用 (运行时 lodpack 查找)
    ↑ sub_1405FA610 调用 (Mesh lodpack resolver)
```

### 6.2 分析 Mesh lodpack resolver (sub_1405FA610)

```c
// IDA 反编译 (简化)
__int64 sub_1405FA610(__int64 a1) {
    v2 = sub_1403A60C0();  // 获取 lodpack 上下文
    sub_1403A1100(v2, *(QWORD*)a1);  // 设置 group
    
    // 遍历 mesh 对象列表
    v4 = 0;
    while (v4 != v9 || v3) {
        // v10 = mesh 对象指针
        v11 = *v10;  // mesh data
        
        // ★ 关键: 从 mesh 对象取 hash
        v39 = *(QWORD*)(*(QWORD*)(v11 + 40) + 104);  // hash at +0x68
        
        // ★ 用 hash 查 lodpack
        v13 = sub_1403A1820(v2, v35, v12, &v39);
        
        // 设置 mesh 数据
        v14 = *(QWORD*)(v11 + 32);
        *(OWORD*)(v11 + 16) = *v13;  // 写入 lodpack 查找结果
        sub_1405E4550(v14, v16, v11 + 16);
    }
}
```

**关键发现**：
- `mesh_obj + 40` → 指向 mesh data 结构
- `mesh_data + 0x68` (104) → hash (u64)，用于 lodpack 查找
- 这就是 hash != 0 时的数据来源路径

### 6.3 分析 Lodpack 查找 (sub_1405F0910)

```c
// IDA 反编译 (简化)
// 二分搜索: member 数组, hash 在 +8, 24B/条目, 已排序
__int64 sub_1405F0910(__int64 lodpack_obj, __int64 hash) {
    members = *(QWORD*)(lodpack_obj + 0);   // TOC 数组指针
    count = *(int*)(lodpack_obj + 8);        // 条目数
    
    // 二分搜索
    lo = 0; hi = count - 1;
    while (lo <= hi) {
        mid = (lo + hi) / 2;
        member = members + 24 * mid;        // 24 字节/条目
        member_hash = *(QWORD*)(member + 8); // hash at +8
        
        if (member_hash == hash) return member;
        if (member_hash < hash) lo = mid + 1;
        else hi = mid - 1;
    }
    return 0;  // not found
}
```

### 6.4 Lodpack TOC 结构确认

```c
// sub_1405F1110 (hash 二分搜索, 确认 24B/条目)
// 每条目 24 字节:
  +0x00  u32  groupIdx
  +0x04  u32  offsetter
  +0x08  u64  hash    ← 二分搜索 key (已排序)
  +0x10  u32  blockSize
  +0x14  u32  skip
```

### 6.5 Lodpack 构造函数 (sub_1405F0580)

```c
// 确认 lodpack 对象布局:
  obj + 0     → TOC 数组指针
  obj + 8     → name 字符串
  obj + 0x20C → group table
```

---

## 7. Phase 6: meshbuf 字段定位

### 7.1 这是最难的部分

meshbuf 是 MESH 条目的数据体。需要在内存中解析出：
- 顶点数 (vertex count)
- 三角形数 (triangle count)
- 属性表 (attribute table)
- 流表 (stream table)
- hash（用于 lodpack 查找）

### 7.2 方法：Frida hook + 内存 dump

Hook mesh 处理函数，在数据到达时 dump meshbuf 内存：

```javascript
// Hook mesh data processor, dump meshbuf
Interceptor.attach(base.add(0x5E4920), {
    onEnter: function(args) {
        var meshEntry = args[2];  // a3 = mesh entry
        
        // Dump meshbuf 前 256 字节
        console.log("=== meshbuf dump ===");
        console.log(hexdump(meshEntry, {length: 256}));
        
        // 读关键字段
        var meshIdx = meshEntry.add(80).readU16();
        console.log("mesh index: " + meshIdx);
    }
});
```

### 7.3 字段定位过程

**第 1 步**：找到 offset_array

```
meshbuf (mb) 结构:
  mb[12 + off_arr_off] → offset_array
  meshSub[i] = arr_pos + offset_array[i]
```

通过 dump 多个 meshbuf，对比数据模式，发现 `mb + 12` 处有一个偏移量，
指向一个 u32 数组，每个元素是一个 sub-mesh 的偏移。

**第 2 步**：发现 shift 规则

```
最初尝试: 直接用 offset_array[i] 定位 meshSub
  → 字段值不对，vertex count 出现荒谬值

调整: 尝试加偏移
  meshSub = sa + offset_array[i] + ???

关键突破: 注意到 si (sub-mesh index) 和字段位置的关系
  si=0: fields at sa + 0
  si=1: fields at sa + 4
  si=2: fields at sa + 8
  
  → shift = si * 4
  → base = sa + shift
```

**第 3 步**：验证 shift 规则

```javascript
// Frida: 验证 365 个 meshSub
var validCount = 0;
var totalCount = 0;

for (var wad of wads) {
    var mb = parseMeshbuf(wad);
    for (var si = 0; si < mb.subCount; si++) {
        totalCount++;
        var base = mb.sa + si * 4;
        
        // 读 vc (vertex count) at base+68
        var vc = readU32(base + 68);
        // 读 tc (triangle count) at base+72
        var tc = readU32(base + 72);
        
        // 验证: vc 和 tc 应该是合理值
        if (vc > 0 && vc < 1000000 && tc > 0 && tc < 2000000) {
            validCount++;
        }
    }
}

console.log("Valid: " + validCount + "/" + totalCount);
// 输出: Valid: 365/365  ← 100% 匹配
```

**第 4 步**：定位所有字段

在 `base = sa + si * 4` 的基础上，逐字段试探：

```
base + 68  → vc (vertex count)     ← 与顶点缓冲大小交叉验证
base + 72  → tc (triangle count)   ← 与索引缓冲大小交叉验证
base + 96  → ato (attr table offset, 始终=0x90=144)
base + 100 → sto (stream table offset, 值=224/240/256/272/288)
base + 104 → hash (lodpack 查找 key)
```

**第 5 步**：解析属性表和流表

```
attr table: base + ato, 条目数 = (sto - ato) / 8
  每条目 8 字节: semantic(1B) + format(1B) + stream_idx(1B) + ...

stream table: base + sto
  每条目描述一个顶点数据流
  
attr active filter: stream_idx < num_streams
  (只处理 stream_idx 在有效范围内的属性)
```

### 7.4 Sentinel 值的排除

```
meshbuf 中有一个值: 0xFFFFFFFFFFFF2310
最初以为是魔数，用来定位字段
  → 错误！分析多个 meshbuf 后发现这个值会变
  → 它是一个变量字段，根据 attr count 不同而不同
  → 不能用作字段定位的锚点
```

---

## 8. Phase 7: 纹理格式逆向

### 8.1 识别 GNF 格式

```
.texpack 文件 → hex editor 查看
  发现 magic = 0x20466E47 = "GnF " (反向)
  → 这是 Sony 的 GNF (GNF Texture Format)
```

### 8.2 IDA 追踪纹理加载

从 `.texpack` 字符串 xref 找到纹理加载代码，分析 GNF header 解析：

```c
// 纹理加载函数 (简化)
magic = *(uint32_t*)(data + 0);      // 0x20466E47
fmt_field = *(uint32_t*)(data + 20); // 格式+标志
dim_field = *(uint32_t*)(data + 24); // 维度
mip_field = *(uint32_t*)(data + 28); // mip 数
dp_field = *(uint32_t*)(data + 32);  // depth

// 位域提取:
format = (fmt_field >> 20) & 0x3F;   // bits[25:20]
width = (dim_field & 0x3FFF) + 1;    // bits[13:0]
height = ((dim_field >> 14) & 0x3FFF) + 1;  // bits[27:14]
mips = ((mip_field >> 16) & 0xF) + 1;       // bits[19:16]
depth = (dp_field & 0x1FFF) + 1;            // bits[12:0]
```

### 8.3 格式码映射

通过 IDA 分析 + texture2ddecoder 解码验证：

```
PC 格式码 → DXGI 格式:
  0x29 → BC1_TYPELESS     (71)
  0x2A → BC1_UNORM_SRGB   (72)
  0x2F → BC4_TYPELESS     (80)
  0x33 → BC6H_TYPELESS_UF16 (95)
  0x35 → BC7_TYPELESS     (98)
  0x36 → BC7_UNORM_SRGB   (99)
```

### 8.4 Mip 填充规则验证

这是最耗时的部分。需要计算每个 mip 级别的块数，然后验证总数据量与 rawSize 匹配。

```python
# 验证方法:
ref_w = next_pow2(width)
ref_h = next_pow2(height)

total_blocks = 0
for mip in range(mips):
    mw = max(1, ref_w >> mip)
    mh = max(1, ref_h >> mip)
    blocks_w = max(8, (mw + pixbl - 1) // pixbl)  # 对齐到 8
    blocks_w = ((blocks_w + 15) // 16) * 16        # 总对齐到 16
    blocks_h = max(8, (mh + pixbl - 1) // pixbl)
    total_blocks += blocks_w * blocks_h

calculated_size = total_blocks * bytes_per_block
assert calculated_size == rawSize  # 100% match
```

**验证结果**：
- BC1/BC4 10 mips: rawSize=176,128 ✅
- BC7/BC6H 9 mips: rawSize=90,112 ✅

---

## 9. 验证方法论总结

### 9.1 三层验证体系

```
Layer 1: IDA 静态分析
  → 理解代码结构、调用链、数据流
  → 识别函数用途、结构体布局
  → 形成假设

Layer 2: Frida 动态验证
  → hook 关键函数，抓取运行时数据
  → 验证 IDA 分析的假设
  → 确认偏移、type code 映射、数据格式

Layer 3: 字节级/数学验证
  → 文件字节级匹配 (entry 偏移 vs WAD 数据)
  → 数学验证 (mip 块数 vs rawSize)
  → 批量验证 (365/365 meshSubs, 0/19697 offset mismatch)
```

### 9.2 验证策略

| 验证类型 | 方法 | 示例 |
|----------|------|------|
| 函数用途 | frida hook + 调用计数 | dispatch 5351 次确认 |
| 偏移正确性 | 读内存 + 与已知值交叉验证 | entry+0x04 ↔ memcpy size |
| 数据格式 | 字节级 dump + 模式匹配 | typeCode 字节序列 |
| 数学规则 | 批量验证 + 100% 匹配 | shift=si*4 (365/365) |
| 文件格式 | 解压 + 字节匹配 | LZ4 → WTOC magic |

### 9.3 IDA 注释写入

所有验证过的发现都写入 IDA 注释，使用 MCP：

```python
# 通过 IDA MCP 写入注释
ida.set_comments(items=[
    {"addr": "0x140391140", "comment": "DISPATCH: v3=(u8)type_code, TLS[4464+8*v3]->handler, vtable+120(handler,entry,type,data). VERIFIED frida"},
    {"addr": "0x140393E20", "comment": "WAD multi-entry handler. WTOC parser + 144B iter. VERIFIED frida+IDA"},
    {"addr": "0x1403B3980", "comment": "WTOC parser: 64B header + 144B entries. entry+0x78=data_ptr. VERIFIED frida+IDA"},
    # ... 14 个函数全部写入
])
```

---

## 10. 踩过的坑

### 10.1 MemoryAccessMonitor 导致游戏卡死

```
尝试: 用 MemoryAccessMonitor 在 meshbuf buffer 上下内存访问断点
结果: 游戏立即卡死，无法操作
原因: MemoryAccessMonitor 的 overhead 太大，游戏渲染线程被阻塞
解决: 改用 Interceptor.attach，只 hook 函数入口/出口
```

### 10.2 Frida attach 导致崩溃

```
尝试: 游戏运行后 frida -p <PID> 附加
结果: 游戏立即崩溃
原因: 游戏有反作弊检测，检测到调试器附加就退出
解决: 用 frida -f spawn 模式启动游戏
```

### 10.3 Sentinel 值误判

```
尝试: 用 0xFFFFFFFFFFFF2310 作为字段定位锚点
结果: 对部分 meshbuf 有效，但很多不匹配
原因: 这个值不是魔数，是变量字段，随 attr count 变化
解决: 放弃用 sentinel 定位，改用 offset_array + shift 规则
```

### 10.4 Frida v17 API 变化

```
尝试: Module.getExportByName("GoWR.exe", "xxx")
结果: 报错，函数不存在
原因: Frida v17 改了 API
解决: 改用 Process.getModuleByName("GoWR.exe").getExportByName("xxx")
```

### 10.5 E:->D: 直接拷贝极慢

```
尝试: Python 直接从 E: 拷贝 GLB 到 D:
结果: 4.6 files/s，127K 文件需要 7.7 小时
原因: E: 和 D: 在同一物理 HDD，磁头在两个分区间反复寻道
解决: 两阶段拷贝 E:->F:SSD->D:HDD，快 7 倍
```

### 10.6 hash==0 的含义

```
最初假设: hash=0 表示数据缺失或错误
实际发现: hash=0 表示静态/基础模型，顶点数据内联在 MG_ 条目中
  → 不需要 lodpack 查找
  → basePtr = MG_ 条目的文件偏移
hash≠0 才需要去 lodpack 二分搜索
```

### 10.7 batch 边界处理

```
问题: WAD 数据按 batch 组织，文件偏移计算需要考虑 batch 边界
解决: 通过 entry byte114 bit0 (batch_end) 标记 batch 边界
验证: batch 模拟计算文件偏移，0/19697 不匹配 → 100% 正确
```

---

## 附录: 分析工具配置

### MCP Server 配置

| 工具 | 传输方式 | 地址 | 状态 |
|------|----------|------|------|
| IDA | HTTP | `http://127.0.0.1:13337/mcp` | ✅ 66 工具 |
| x64dbg | HTTP | `http://127.0.0.1:3000/mcp` | ✅ 80 工具 |
| CE | stdio bridge | `ce_mcp_bridge.py` | ✅ 12 工具 |
| Frida | stdio bridge | `frida_mcp_bridge.py` | ✅ 14 工具 |

### IDA MCP 关键 API

```python
# 写注释 (items 是列表)
ida.set_comments(items=[{"addr": "0x140391140", "comment": "..."}])

# 重命名 (batch 参数无效，用 py_eval)
ida.py_eval(code="idaapi.set_name(0x140391140, 'WadDispatch', idaapi.SN_NOWARN|idaapi.SN_FORCE)")

# 反编译 (用 addr 不是 address)
ida.decompile(addr="0x140391140")

# 读字节 (需要 regions 参数)
ida.get_bytes(regions=[{"addr": "0x140391140", "size": 64}])

# 交叉引用 (需要 addrs 复数)
ida.xrefs_to(addrs=["0x140391140"])

# 保存 IDB
ida.idb_save({})
```