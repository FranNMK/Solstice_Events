import os, re, certifi
from dotenv import load_dotenv
load_dotenv()
from sqlalchemy import create_engine, text

url = os.getenv("TIDB_URL","").replace("mysql+aiomysql://","mysql+pymysql://")
url = re.sub(r"[&?]ssl_ca=[^&]*","",url)
url = re.sub(r"\?$","",url)

engine = create_engine(url, connect_args={"connect_timeout":30,"ssl":{"ca":certifi.where()}})
with engine.connect() as conn:
    # Reset stuck attendees
    r1 = conn.execute(text("UPDATE attendees SET status = 'registered' WHERE status = 'pending'"))
    print(f"Reset {r1.rowcount} attendees: pending -> registered")

    # Fail any stuck badge_jobs (queued or processing)
    r2 = conn.execute(text("UPDATE badge_jobs SET status = 'failed' WHERE status IN ('queued','processing')"))
    print(f"Marked {r2.rowcount} badge_jobs as failed")

    conn.commit()
    print("Done - committed.")
