import os, re, certifi
from dotenv import load_dotenv
load_dotenv()
from sqlalchemy import create_engine, text

url = os.getenv("TIDB_URL","").replace("mysql+aiomysql://","mysql+pymysql://")
url = re.sub(r"[&?]ssl_ca=[^&]*","",url)
url = re.sub(r"\?$","",url)
engine = create_engine(url, connect_args={"connect_timeout":30,"ssl":{"ca":certifi.where()}})

with engine.connect() as conn:
    rows = conn.execute(text(
        "SELECT id, name, badge_pdf_url FROM attendees WHERE status='checked_in' AND badge_pdf_url IS NOT NULL"
    )).fetchall()
    print(f"Found {len(rows)} checked-in attendees with badges:")
    for r in rows:
        print(f"  {r[1]:30s}  {r[0]}")
        print(f"    url: {r[2]}")
