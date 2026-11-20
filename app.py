import os, re, threading, time
import duckdb
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

HF = (os.getenv("ICMR_HF_INDEX_BASE") or
      "https://huggingface.co/buckets/godhosting/bakchodipromax/resolve/main").rstrip("/")

DUP_CAP = 2
NUMBER_FIELDS = ["phoneNumber", "aadharNumber", "otherNumber"]
ALL_FIELDS = ["name", "fathersName", "phoneNumber", "aadharNumber", "otherNumber",
              "address", "district", "pincode", "state", "town", "source"]
INDEXES = {k: [f"{HF}/idx_{k}.{i}.parquet" for i in range(7)] for k in ("phone", "aadhar")}

_lock, _conn = threading.Lock(), None
_status = {"phone_loaded": False, "aadhar_loaded": False, "error": None, "details": {}}


def init():
    global _conn
    if _conn:
        return _conn
    with _lock:
        if _conn:
            return _conn
        c = duckdb.connect(":memory:")
        c.execute("SET home_directory='/tmp'")
        c.execute("SET extension_directory='/tmp/duckdb_extensions'")
        try:
            c.execute("INSTALL httpfs")
            c.execute("LOAD httpfs")
            _status["details"]["httpfs"] = "ok"
        except Exception as e:
            try:
                c.execute("LOAD httpfs")
                _status["details"]["httpfs"] = "cached"
            except Exception as e2:
                _status["error"] = str(e2)[:200]
                _status["details"]["httpfs"] = str(e2)[:200]
        for kind, urls in INDEXES.items():
            try:
                c.execute(f"SELECT count(*) FROM read_parquet('{urls[0]}', union_by_name=true) LIMIT 1").fetchall()
                c.execute(
                    f"CREATE OR REPLACE VIEW people_{kind} AS "
                    f"SELECT * FROM read_parquet([{','.join(repr(u) for u in urls)}], union_by_name=true)"
                )
                _status[f"{kind}_loaded"] = True
                _status["details"][kind] = "ok"
            except Exception as e:
                _status["details"][kind] = str(e)[:200]
        _conn = c
        return c


def ready(kind):
    return bool(_status.get(f"{kind}_loaded"))


def person_key(r):
    ph = str(r.get("phoneNumber") or "").strip()
    ad = str(r.get("aadharNumber") or "").strip()
    return f"{ph}|{ad}" if (ph or ad) else f"{r.get('name')}|{r.get('fathersName')}"


def connected_numbers(r):
    seen, out = set(), []
    for f in NUMBER_FIELDS:
        v = str(r.get(f) or "").strip()
        if v and v not in seen:
            seen.add(v)
            out.append({"field": f, "value": v})
    return out


def cap(rows):
    seen, out = {}, []
    for r in rows:
        k = person_key(r)
        n = seen.get(k, 0)
        if n < DUP_CAP:
            seen[k] = n + 1
            r = dict(r)
            r["connected_numbers"] = connected_numbers(r)
            out.append(r)
    return out


def run_search(view, field, val, mode, limit):
    c = init()
    v = str(val).replace("'", "''")
    if mode == "exact":
        sql = f"SELECT * FROM {view} WHERE {field}='{v}' LIMIT {limit * DUP_CAP + 20}"
    else:
        v2 = v.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        sql = f"SELECT * FROM {view} WHERE {field} ILIKE '%{v2}%' ESCAPE '\\' LIMIT {limit * DUP_CAP + 20}"
    cur = c.execute(sql)
    cols = [d[0] for d in cur.description]
    return cap([dict(zip(cols, row)) for row in cur.fetchall()])[:limit]


app = FastAPI(title="Info Search API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


CSS = """
<style>
  * { box-sizing: border-box; }
  body { font-family: -apple-system, system-ui, sans-serif; background: #0f172a; color: #e2e8f0; margin: 0; padding: 20px; }
  .container { max-width: 1000px; margin: 0 auto; }
  h1 { margin: 0 0 6px 0; font-size: 24px; }
  .sub { color: #94a3b8; font-size: 13px; margin-bottom: 20px; }
  .sub a { color: #60a5fa; text-decoration: none; margin-right: 10px; }
  .card { background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 20px; margin-bottom: 16px; }
  h2 { margin-top: 0; font-size: 16px; }
  .status { display: inline-flex; align-items: center; gap: 8px; padding: 6px 14px; border-radius: 999px; font-weight: 600; font-size: 13px; }
  .dot { width: 10px; height: 10px; border-radius: 50%; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; }
  .stat { background: #0f172a; padding: 12px; border-radius: 8px; border: 1px solid #334155; }
  .stat-label { font-size: 11px; color: #94a3b8; text-transform: uppercase; margin-bottom: 4px; letter-spacing: 0.5px; }
  .stat-value { font-size: 14px; font-weight: 600; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th, td { padding: 10px; text-align: left; border-bottom: 1px solid #334155; vertical-align: top; }
  th { color: #94a3b8; font-size: 11px; text-transform: uppercase; }
  tr:last-child td { border-bottom: none; }
  a { color: #60a5fa; text-decoration: none; }
  a:hover { text-decoration: underline; }
  code { background: #0f172a; padding: 2px 6px; border-radius: 4px; font-size: 12px; color: #fbbf24; }
  .err { background: #7f1d1d; border: 1px solid #ef4444; color: #fecaca; padding: 12px; border-radius: 8px; margin-top: 12px; font-size: 13px; word-break: break-word; }
  input { background: #0f172a; border: 1px solid #334155; color: #e2e8f0; padding: 10px; border-radius: 6px; font-size: 14px; width: 100%; }
  button { background: #3b82f6; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-weight: 600; white-space: nowrap; }
  button:hover { background: #2563eb; }
  pre { background: #0f172a; padding: 12px; border-radius: 6px; overflow-x: auto; font-size: 12px; margin: 0; max-height: 400px; overflow-y: auto; }
  .row { display: flex; gap: 8px; }
</style>
"""

SCRIPT = """
<script>
async function testSearch() {
  const q = document.getElementById('q').value.trim();
  if (!q) return;
  const out = document.getElementById('out');
  out.textContent = 'Searching...';
  try {
    const r = await fetch('/search?q=' + encodeURIComponent(q));
    const d = await r.json();
    out.textContent = JSON.stringify(d, null, 2);
  } catch (e) {
    out.textContent = 'Error: ' + e.message;
  }
}
document.getElementById('q').addEventListener('keydown', function(e) {
  if (e.key === 'Enter') testSearch();
});
</script>
"""


@app.get("/", response_class=HTMLResponse)
def root():
    try:
        init()
    except Exception:
        pass

    phone_ok = ready("phone")
    aadhar_ok = ready("aadhar")
    err = _status.get("error")
    details = _status.get("details", {})

    if err:
        status_bg, status_fg, status_text = "#7f1d1d", "#fca5a5", "ERROR"
    elif phone_ok and aadhar_ok:
        status_bg, status_fg, status_text = "#064e3b", "#6ee7b7", "HEALTHY"
    else:
        status_bg, status_fg, status_text = "#78350f", "#fcd34d", "DEGRADED"

    error_html = f'<div class="err"><strong>⚠️ Error:</strong> {err}</div>' if err else ""
    phone_badge = "✅ Loaded" if phone_ok else "❌ Not loaded"
    aadhar_badge = "✅ Loaded" if aadhar_ok else "❌ Not loaded"
    httpfs_status = details.get("httpfs", "unknown")
    extra = "".join(
        f'<tr><td><code>{k}</code></td><td>{v}</td></tr>'
        for k, v in details.items() if k not in ("httpfs", "phone", "aadhar")
    ) or '<tr><td colspan="2" style="color:#64748b;">no extra details</td></tr>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Info Search API — Dashboard</title>
{CSS}
</head>
<body>
<div class="container">
  <h1>🔍 Info Search API</h1>
  <div class="sub">
    Develop by Tridev Cyber Warrior &middot;
    <a href="/health" target="_blank">/health</a>
    <a href="/warmup" target="_blank">/warmup</a>
    <a href="/fields" target="_blank">/fields</a>
  </div>

  <div class="card">
    <div class="status" style="background: {status_bg}; color: {status_fg};">
      <span class="dot" style="background: {status_fg};"></span>
      {status_text}
    </div>
    {error_html}
  </div>

  <div class="card">
    <h2>Index Load Status</h2>
    <div class="grid">
      <div class="stat">
        <div class="stat-label">Phone Index</div>
        <div class="stat-value">{phone_badge}</div>
      </div>
      <div class="stat">
        <div class="stat-label">Aadhar Index</div>
        <div class="stat-value">{aadhar_badge}</div>
      </div>
      <div class="stat">
        <div class="stat-label">httpfs Extension</div>
        <div class="stat-value">{httpfs_status}</div>
      </div>
    </div>
    <table style="margin-top:16px;">
      <tr><th>Detail</th><th>Value</th></tr>
      {extra}
    </table>
  </div>

  <div class="card">
    <h2>📋 All Commands / Endpoints</h2>
    <table>
      <tr><th>Method</th><th>Endpoint</th><th>Description</th></tr>
      <tr><td>GET</td><td><a href="/" target="_blank"><code>/</code></a></td><td>This dashboard</td></tr>
      <tr><td>GET</td><td><a href="/health" target="_blank"><code>/health</code></a></td><td>Health check (JSON)</td></tr>
      <tr><td>GET</td><td><a href="/warmup" target="_blank"><code>/warmup</code></a></td><td>Force init indexes (first time slow)</td></tr>
      <tr><td>GET</td><td><a href="/fields" target="_blank"><code>/fields</code></a></td><td>List searchable fields</td></tr>
      <tr><td>GET</td><td><a href="/search?q=6290593159" target="_blank"><code>/search?q=...</code></a></td><td>Unified search (phone → aadhar fallback)</td></tr>
      <tr><td>GET</td><td><a href="/search?field=phoneNumber&q=6290593159&mode=exact" target="_blank"><code>/search?field=...&amp;q=...</code></a></td><td>Field search (exact or like)</td></tr>
    </table>
  </div>

  <div class="card">
    <h2>🧪 Quick Search Test</h2>
    <div class="row">
      <input id="q" placeholder="Enter phone / aadhar (10+ digits)..." />
      <button onclick="testSearch()">Search</button>
    </div>
    <pre id="out" style="margin-top:12px;">Result will appear here...</pre>
  </div>
</div>
{SCRIPT}
</body>
</html>"""
    return HTMLResponse(html)


@app.get("/health")
def health():
    try:
        init()
    except Exception as e:
        return JSONResponse({"status": "error", "error": str(e)}, 500)
    return {
        "status": "degraded" if _status["error"] else "healthy",
        "indexes": {"phone": ready("phone"), "aadhar": ready("aadhar")},
        "load_status": _status,
        "timestamp": time.time(),
    }


@app.get("/warmup")
def warmup():
    try:
        init()
    except Exception as e:
        return JSONResponse({"error": str(e)}, 500)
    return {
        "status": "warmed up",
        "indexes": {"phone": ready("phone"), "aadhar": ready("aadhar")},
        "load_status": _status,
    }


@app.get("/fields")
def fields():
    return {"fields": ALL_FIELDS, "number_fields": NUMBER_FIELDS}


@app.get("/search")
def search(q: str = Query(None), mobile: str = Query(None), field: str = Query(None),
           mode: str = "exact", limit: int = 10):
    val = (q or mobile or "").strip()
    if not val:
        return JSONResponse({"error": "Provide 'q' or 'mobile'"}, 422)
    if field and field not in ALL_FIELDS:
        return JSONResponse({"error": f"Unknown field: {field}"}, 422)
    limit = max(1, min(200, limit))

    try:
        rows = []
        if field == "phoneNumber" and ready("phone"):
            rows = run_search("people_phone", "phoneNumber", val, mode, limit)
        elif field == "aadharNumber" and ready("aadhar"):
            rows = run_search("people_aadhar", "aadharNumber", val, mode, limit)
        elif re.fullmatch(r"\d{8,}", val):
            if ready("phone"):
                rows = run_search("people_phone", "phoneNumber", val, mode, limit)
            if not rows and ready("aadhar"):
                rows = run_search("people_aadhar", "aadharNumber", val, mode, limit)
    except Exception as e:
        return JSONResponse({"error": str(e), "query": val}, 500)

    return {
        "success": len(rows) > 0,
        "query": val,
        "count": len(rows),
        "results": rows,
        "author": "Develop by Tridev Cyber Warrior",
    }
