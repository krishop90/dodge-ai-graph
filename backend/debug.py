import os
import json
import sys

# Load .env from the parent folder (backend/)
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

print("=" * 55)
print("  SAP O2C — Diagnostic Check")
print("=" * 55)

# 1. Env vars
print("\n[1] Environment variables")
uri      = os.getenv("NEO4J_URI")
user     = os.getenv("NEO4J_USER")
password = os.getenv("NEO4J_PASSWORD")
groq_key = os.getenv("GROQ_API_KEY")
print(f"  NEO4J_URI      = {uri      or '❌ NOT SET'}")
print(f"  NEO4J_USER     = {user     or '❌ NOT SET'}")
print(f"  NEO4J_PASSWORD = {'✅ set'  if password else '❌ NOT SET'}")
print(f"  GROQ_API_KEY   = {'✅ set'  if groq_key  else '❌ NOT SET'}")

if not all([uri, user, password]):
    print("\n  ⛔ Fix your .env file first.")
    sys.exit(1)

# 2. Neo4j connection
print("\n[2] Neo4j connection")
try:
    sys.path.insert(0, str(Path(__file__).parent))
    from database import db
    result = db.query("RETURN 1 AS ping")
    print(f"  ✅ Connected! {result}")
except Exception as e:
    print(f"  ❌ FAILED: {e}")
    sys.exit(1)

# 3. Dataset folder
print("\n[3] Dataset folder")
DATA_DIR = r"D:\DodgeAI\dataset\sap-o2c-data"
if os.path.exists(DATA_DIR):
    folders = sorted([f for f in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, f))])
    print(f"  ✅ Found {len(folders)} folders")
    for f in folders:
        print(f"     - {f}")
else:
    print(f"  ❌ Not found: {DATA_DIR}")
    sys.exit(1)

# 4. Sample record from each folder
print("\n[4] Sampling one record per folder")
for folder in folders:
    fp = os.path.join(DATA_DIR, folder)
    jsonl_files = sorted([f for f in os.listdir(fp) if f.endswith(".jsonl")])
    if not jsonl_files:
        print(f"  ⚠️  {folder}: no .jsonl files")
        continue
    with open(os.path.join(fp, jsonl_files[0]), encoding="utf-8") as f:
        line = f.readline().strip()
    try:
        record = json.loads(line)
        print(f"  ✅ {folder}: {list(record.keys())[:4]}")
    except Exception as e:
        print(f"  ❌ {folder}: {e}")

# 5. Test write/read/delete
print("\n[5] Test write to Neo4j")
try:
    db.query("MERGE (t:_Test {id: 'probe'}) SET t.ok = true")
    check = db.query("MATCH (t:_Test {id: 'probe'}) RETURN t.ok AS ok")
    db.query("MATCH (t:_Test {id: 'probe'}) DELETE t")
    print(f"  ✅ Write/Read/Delete passed: {check}")
except Exception as e:
    print(f"  ❌ Write failed: {e}")

print("\n✅ All checks passed — ready for ingest.py\n")