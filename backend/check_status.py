import os, re, certifi
from dotenv import load_dotenv
load_dotenv()
from sqlalchemy import create_engine, text

url = os.getenv("TIDB_URL","").replace("mysql+aiomysql://","mysql+pymysql://")
url = re.sub(r"[&?]ssl_ca=[^&]*","",url)
url = re.sub(r"\?$","",url)

engine = create_engine(url, connect_args={"connect_timeout":30,"ssl":{"ca":certifi.where()}})
with engine.connect() as conn:
    print("=== ATTENDEES WITH COMPLETED JOBS BUT WRONG STATUS ===")
    # Jobs completed but attendee not checked_in — the exact broken state
    rows = conn.execute(text("""
        SELECT a.id, a.name, a.status, a.badge_pdf_url,
               j.id as job_id, j.status as job_status, j.completed_at
        FROM attendees a
        JOIN badge_jobs j ON j.attendee_id = a.id
        WHERE j.status = 'completed'
          AND a.status != 'checked_in'
        ORDER BY j.completed_at DESC
    """)).fetchall()
    for r in rows:
        print(f"  attendee_id : {r[0]}")
        print(f"  name        : {r[1]}")
        print(f"  status      : {r[2]}  (should be checked_in)")
        print(f"  badge_url   : {r[3]}")
        print(f"  job_id      : {r[4]}")
        print(f"  job_status  : {r[5]}")
        print(f"  completed_at: {r[6]}")
        print()
    if not rows:
        print("  None found - everything is consistent")

    print("=== BADGE_PDF_URL for all badge-job-completed attendees ===")
    rows2 = conn.execute(text("""
        SELECT a.id, a.name, a.badge_pdf_url
        FROM attendees a
        WHERE a.id IN (SELECT attendee_id FROM badge_jobs WHERE status='completed')
    """)).fetchall()
    for r in rows2:
        print(f"  {r[1]:30s} badge_url={r[2]}")
