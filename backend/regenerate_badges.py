"""
regenerate_badges.py
Deletes existing Cloudinary badge assets (both authenticated and upload types)
then re-uploads fresh PDFs as public (type=upload). Updates badge_pdf_url in DB.
"""
import os, sys, re, certifi
from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine, text
url = os.getenv("TIDB_URL","").replace("mysql+aiomysql://","mysql+pymysql://")
url = re.sub(r"[&?]ssl_ca=[^&]*","",url)
url = re.sub(r"\?$","",url)
engine = create_engine(url, connect_args={"connect_timeout":30,"ssl":{"ca":certifi.where()}})

import cloudinary, cloudinary.uploader, cloudinary.api
from app.services.badge import generate_badge_pdf

with engine.connect() as conn:
    rows = conn.execute(text("""
        SELECT a.id, a.name, a.profession, a.qr_code_id,
               e.title, e.date
        FROM attendees a
        JOIN events e ON e.id = a.event_id
        WHERE a.status = 'checked_in'
    """)).fetchall()

    print(f"Processing {len(rows)} badge(s)...\n")
    for r in rows:
        attendee_id, name, profession, qr_code_id = r[0], r[1], r[2], r[3]
        event_title, event_date = r[4], r[5]
        pid = f"solstice/badges/{attendee_id}"
        print(f"  {name:35s}")

        # Step 1: Delete from BOTH delivery types so Cloudinary forgets the old asset
        for del_type in ("authenticated", "upload"):
            try:
                cloudinary.uploader.destroy(pid, resource_type="raw", type=del_type, invalidate=True)
            except Exception:
                pass  # OK if it didn't exist under that type

        # Step 2: Generate fresh PDF and upload as public
        try:
            _, new_url = generate_badge_pdf(
                attendee_id=attendee_id,
                name=name,
                profession=profession or "Attendee",
                event_title=event_title,
                event_date=event_date,
                qr_code_id=qr_code_id,
            )
            conn.execute(text("UPDATE attendees SET badge_pdf_url=:url WHERE id=:id"),
                         {"url": new_url, "id": attendee_id})
            print(f"    OK: {new_url}")
        except Exception as e:
            print(f"    FAILED: {e}")

    conn.commit()
    print("\nDone — all badges are now public.")
