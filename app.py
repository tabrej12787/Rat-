import os
import math
import duckdb
import duckdb_core_ext_httpfs
from fastapi import FastAPI, HTTPException, Query

PARQUET_URL = os.environ.get(
    "PARQUET_URL",
    "https://huggingface.co/datasets/tfqdeadlo/Inddatainonefile/resolve/main/users_data.parquet"
)

con = duckdb.connect(
    config={"extension_directories": [duckdb_core_ext_httpfs.get_extensions_dir()]}
)
try:
    con.execute("LOAD httpfs;")
    con.execute("LOAD parquet;")
    print("[+] extensions loaded")
except Exception as e:
    print(f"[!] load failed: {e}")
    con.execute("INSTALL httpfs; LOAD httpfs;")

app = FastAPI(title="Simple Search")

def clean(df):
    out = []
    for r in df.to_dict(orient="records"):
        c = {}
        for k, v in r.items():
            if isinstance(v, float) and math.isnan(v):
                c[k] = None
            elif hasattr(v, "item"):
                c[k] = v.item()
            else:
                c[k] = v
        out.append(c)
    return out

@app.get("/search")
async def search(phone: str = Query(...)):
    try:
        df = con.execute(
            f"SELECT * FROM read_parquet('{PARQUET_URL}') WHERE mobile = ? LIMIT 10",
            [phone],
        ).fetchdf()
        if df.empty:
            return {"message": "NO_DATA_FOUND", "phone": phone, "count": 0, "results": []}
        rows = clean(df)
        return {"phone": phone, "count": len(rows), "results": rows}
    except Exception as e:
        raise HTTPException(500, f"QUERY_FAILED: {e}")

@app.get("/")
async def root():
    return {"status": "ONLINE", "endpoints": ["/search", "/docs"]}
