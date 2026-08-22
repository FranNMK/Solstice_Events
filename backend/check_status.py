import os, re, certifi
from dotenv import load_dotenv
load_dotenv()
from sqlalchemy import create_engine, text

url = os.getenv("TIDB_URL","").replace("mysql+aiomysql://","mysql+pymysql://")
url = re.sub(r"[&?]ssl_ca=[^&]*","",url)
url = re.sub(r"\?$","",url)

engine = create_engine(url, connect_args={"connect_timeout":30,"ssl":{"ca":certifi.where()}})
with engine.connect() as conn:
    rows = conn.execute(text("SELECT id, name, status FROM attendees ORDER BY status")).fetchall()
    print("--- attendees ---")
    for r in rows:
        print(f"  {r[2]:12s}  {r[1]:30s}  {r[0]}")
    jobs = conn.execute(text("SELECT id, attendee_id, status FROM badge_jobs WHERE status != 'completed'")).fetchall()
    print("--- badge_jobs (non-completed) ---")
    for j in jobs:
        print(f"  {j[2]:12s}  {j[1]}  job={j[0]}")
    if not jobs:
        print("  (none)")
