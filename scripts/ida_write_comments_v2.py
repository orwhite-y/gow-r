"""Write all verified function/offset comments to IDA via MCP.
Uses batch API: set_comments(items=[...]), rename(batch=[...])
"""
import json, urllib.request, urllib.error

URL = "http://127.0.0.1:13337/mcp"
SESSION = None

def _post(payload, accept="application/json, text/event-stream"):
    global SESSION
    data = json.dumps(payload).encode()
    req = urllib.request.Request(URL, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", accept)
    if SESSION:
        req.add_header("Mcp-Session-Id", SESSION)
    try:
        r = urllib.request.urlopen(req, timeout=30)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8","replace")
        sid = e.headers.get("Mcp-Session-Id")
        if sid and not SESSION: SESSION = sid
        return e.code, body
    except Exception as e:
        return -1, str(e)
    sid = r.headers.get("Mcp-Session-Id")
    if sid and not SESSION: SESSION = sid
    body = r.read().decode("utf-8","replace")
    return r.status, body

def _parse(resp):
    code, body = resp
    if "data:" in body:
        out = []
        for line in body.splitlines():
            if line.startswith("data:"):
                out.append(line[5:].strip())
        joined = "".join(out) if out else "{}"
        try: return json.loads(joined)
        except: return {"raw": body[:500]}
    try: return json.loads(body)
    except: return {"raw": body[:500]}

def call_tool(name, kwargs):
    payload = {"jsonrpc":"2.0","id":99,"method":"tools/call",
               "params":{"name":name,"arguments":kwargs}}
    code, body = _post(payload)
    if code < 0:
        return f"ERROR: {body}"
    res = _parse((code,body))
    if "result" in res:
        content = res["result"].get("content", [])
        texts = []
        for c in content:
            if c.get("type")=="text":
                texts.append(c["text"])
        return "\n".join(texts)
    return json.dumps(res)[:500]

def init():
    code, body = _post({"jsonrpc":"2.0","id":1,"method":"initialize","params":{
        "protocolVersion":"2024-11-05","capabilities":{},
        "clientInfo":{"name":"codex","version":"1.0"}}})
    if code < 0:
        print(f"init failed: {body}")
        return False
    _parse((code,body))
    _post({"jsonrpc":"2.0","method":"notifications/initialized"}, accept="application/json")
    return True

# All verified functions
RENAMES = [
    ("0x140393E20", "WadMultiEntryHandler"),
    ("0x1405F5F90", "WadMeshDataParser"),
    ("0x1405E4430", "InlineMeshHandler"),
    ("0x1405E4530", "LodpackMeshHandler"),
    ("0x1403B2D40", "WadEntryDataSetTls4848"),
    ("0x1405E5700", "VertexBufferSetup"),
    ("0x1405E3B70", "GetMeshbufSize"),
    ("0x1405E3B80", "GetSubMeshCount"),
    ("0x1405E3BB0", "GetMeshSubCount"),
    ("0x1405E3BC0", "WadVertexOffsetLookup"),
    ("0x1405E3BF0", "GetStreamCount"),
    ("0x1405E3C00", "GetIndexCount"),
    ("0x140391140", "WadDispatch"),
    ("0x140393A30", "WadBatchProcessInner"),
    ("0x1405FA610", "MeshLodpackResolver"),
    ("0x1405FAA30", "MeshLodpackAltPath"),
    ("0x140EBBD10", "GnfHeaderParser"),
    ("0x140ED9880", "DataFormatToGameIdx"),
    ("0x140EDE7F0", "GnfFormatToDxgi"),
    ("0x140ED9940", "GameIdxToDataFormat"),
    ("0x1403CC6D0", "GnfDataParser"),
    ("0x140ED9F80", "SubresourceOffsetCalc"),
    ("0x140EBAFF0", "TextureUploadHandler"),
]

COMMENTS = [
    ("0x140393E20", "WadMultiEntryHandler: Batch layout handler. 9 groups (b111:0=main,1=GPU vertex,2=index,8=other). batch_end=TOC byte114 bit0. word0==25=autopad(size=0). VERIFIED 0/19697 mismatch."),
    ("0x1405F5F90", "WadMeshDataParser: shift=si*4(365/365). base=sa+shift. vc@+68,tc@+72,idx_off@+48,mesh_idx@+80,ato@+96(=0x90),sto@+100,hash@+104(0=inline,!=0=lodpack),idx_fmt@+129,num_streams@+132. attr_table@base+ato, stream_table@base+sto."),
    ("0x1405E4430", "InlineMeshHandler: hash==0 path. VertexBufferSetup(basePtr+meshIndex*64). Inline mesh data within WAD."),
    ("0x1405E4530", "LodpackMeshHandler: hash!=0 path. Calls sub_1405FA330 for lodpack resolution."),
    ("0x1403B2D40", "WadEntryDataSetTls4848: memcpy entry->TLS+4848=basePtr."),
    ("0x1405E5700", "VertexBufferSetup: Reads vertex attrs. 8B/entry: b0=semantic(0=POS,3=TEXCOORD,4=TANGENT,6=NORMAL), b1=format(0/3=f32,6=f16), b2=components, b3=voff(packed), b4=stream_idx(0x0F=inactive)."),
    ("0x1405E3B70", "GetMeshbufSize: returns *(buf+28)"),
    ("0x1405E3B80", "GetSubMeshCount: returns *(buf+32)"),
    ("0x1405E3BB0", "GetMeshSubCount: returns *(buf+16)"),
    ("0x1405E3BC0", "WadVertexOffsetLookup: 2D(submesh,stream)->offset"),
    ("0x1405E3BF0", "GetStreamCount: returns *(buf+48)"),
    ("0x1405E3C00", "GetIndexCount: returns *(buf+52)"),
    ("0x140391140", "WadDispatch: dispatches via TLS+4464+8*type"),
    ("0x140393A30", "WadBatchProcessInner: iterates WTOC entries, processes batch groups"),
    ("0x1405FA610", "MeshLodpackResolver: hash!=0 resolution, traverses block chain"),
    ("0x1405FAA30", "MeshLodpackAltPath: alt lodpack path, traverses linked list"),
    ("0x140EBBD10", "GnfHeaderParser: a1=descriptor,a2=GNF header. PC magic=0x20464E47(uppercase N,PS4=0x20466E47). imageDataOffset=0xFF8(PC)/0xF8(PS4). fileSize=dataSize+0x1000(PC)/+0x100(PS4). VERIFIED."),
    ("0x140ED9880", "DataFormatToGameIdx: DataFormat(int)->game_idx(char). 16 comparisons. PC:0x29=BC1,0x2A=BC1_SRGB,0x2F=BC4,0x33=BC6H,0x35=BC7,0x36=BC7_SRGB. VERIFIED via IDA+ctypes."),
    ("0x140EDE7F0", "GnfFormatToDxgi: game_idx->DXGI. 47 cases. BC1->71,BC1_SRGB->72,BC4->80,BC6H->95,BC7->98,BC7_SRGB->99. VERIFIED."),
    ("0x140ED9940", "GameIdxToDataFormat: reverse mapping game_idx->DataFormat dword"),
    ("0x1403CC6D0", "GnfDataParser: top-level GNF parser. Does NOT call UnSwizzle/Morton - PC data is LINEAR. Calls sce::TextureTool::initializeWithTSharp then SubresourceOffsetCalc. arraySize=4(unk1 byte0=4). VERIFIED."),
    ("0x140ED9F80", "SubresourceOffsetCalc: a3=TSharp,a4=mip,a5=slice. Uses sce::TextureTool. v17=182 dwords(12/mip): [12*mip+0]=height,[12*mip+4]=QWORD offset,[12*mip+6]=QWORD per-slice size. Returns *a1=offset,*a2=size. VERIFIED."),
    ("0x140EBAFF0", "TextureUploadHandler: creates D3D12 resource descriptor, uploads texture to GPU"),
]

def main():
    if not init():
        return
    
    # Rename in batch
    print(f"=== Renaming {len(RENAMES)} functions ===")
    batch = [{"addr": a, "name": n} for a, n in RENAMES]
    result = call_tool("rename", {"batch": batch})
    print(f"  Result: {result[:300]}")
    
    # Set comments in batch
    print(f"\n=== Setting {len(COMMENTS)} comments ===")
    items = [{"addr": a, "comment": c} for a, c in COMMENTS]
    result = call_tool("set_comments", {"items": items})
    print(f"  Result: {result[:300]}")
    
    # Save
    print("\n=== Saving IDB ===")
    result = call_tool("idb_save", {})
    print(f"  Result: {result[:200]}")
    print("\nDone!")

if __name__ == "__main__":
    main()