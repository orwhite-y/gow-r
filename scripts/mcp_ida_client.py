"""Reusable MCP-over-HTTP (streamable) client for IDA at 127.0.0.1:13337.
Usage: python mcp_ida_client.py <action> [args...]
  init            -> initialize + list tools
  call <tool> [k=v ...] -> call a tool with kwargs
"""
import sys, json, urllib.request, urllib.error, uuid

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
        r = urllib.request.urlopen(req, timeout=60)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8","replace")
        # capture session id from error response headers too
        sid = e.headers.get("Mcp-Session-Id")
        if sid and not SESSION:
            SESSION = sid
        return e.code, body
    sid = r.headers.get("Mcp-Session-Id")
    if sid and not SESSION:
        SESSION = sid
    body = r.read().decode("utf-8","replace")
    return r.status, body

def _parse(resp):
    """Parse SSE or plain JSON into the result dict."""
    code, body = resp
    if body.startswith("event:") or "data:" in body:
        # SSE stream - collect data: lines
        out = []
        for line in body.splitlines():
            if line.startswith("data:"):
                out.append(line[5:].strip())
        joined = "".join(out) if out else "{}"
        try:
            return json.loads(joined)
        except Exception:
            return {"raw_sse": body[:500]}
    try:
        return json.loads(body)
    except Exception:
        return {"raw": body[:500]}

def initialize():
    payload = {"jsonrpc":"2.0","id":1,"method":"initialize","params":{
        "protocolVersion":"2024-11-05",
        "capabilities":{},
        "clientInfo":{"name":"codex","version":"1.0"}}}
    code, body = _post(payload)
    print("initialize status:", code)
    res = _parse((code,body))
    print(json.dumps(res, indent=2)[:1500])
    # send initialized notification
    _post({"jsonrpc":"2.0","method":"notifications/initialized"}, accept="application/json")
    # list tools
    code, body = _post({"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}})
    res = _parse((code,body))
    if "result" in res and "tools" in res["result"]:
        tools = res["result"]["tools"]
        print(f"\n=== {len(tools)} TOOLS ===")
        for t in tools:
            desc = t.get("description","")[:70].replace("\n"," ")
            print(f"  {t['name']:32} {desc}")
    else:
        print("tools/list raw:", json.dumps(res)[:1000])

def call_tool(name, kwargs):
    payload = {"jsonrpc":"2.0","id":99,"method":"tools/call",
               "params":{"name":name,"arguments":kwargs}}
    code, body = _post(payload)
    res = _parse((code,body))
    # extract text content
    if "result" in res:
        content = res["result"].get("content", [])
        for c in content:
            if c.get("type")=="text":
                print(c["text"])
            else:
                print(json.dumps(c)[:500])
    else:
        print(json.dumps(res, indent=2)[:2000])

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv)>1 else "init"
    if action == "init":
        initialize()
    elif action == "call":
        name = sys.argv[2]
        kwargs = {}
        for a in sys.argv[3:]:
            if "=" in a:
                k,v = a.split("=",1)
                # try int
                if v.startswith("0x") or v.startswith("-0x"):
                    kwargs[k]=v  # keep hex address as string (IDA MCP wants str)
                else:
                    try: kwargs[k]=int(v)
                    except: kwargs[k]=v
            else:
                kwargs[a]=True
        call_tool(name, kwargs)

