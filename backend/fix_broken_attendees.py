"""
fix_broken_attendees.py
Directly sets checked_in + badge_pdf_url for attendees whose badge_job
completed successfully but whose attendee row was never updated (because
the HTTP loopback webhook silently failed on Render).

We reconstruct the Cloudinary URL from the attendee_id since that is the
public_id used when the PDF was uploaded.
"""
import os, re, certifi
from dotenv import load_dotenv
load_dotenv()
from sqlalchemy import create_engine, text

url = os.getenv("TIDB_URL","").replace("mysql+aiomysql://","mysql+pymysql://")
url = re.sub(r"[&?]ssl_ca=[^&]*","",url)
url = re.sub(r"\?$","",url)

# Read CLOUDINARY_URL to derive the cloud name for URL reconstruction
cloudinary_url = os.getenv("CLOUDINARY_URL","")
# cloudinary://API_KEY:API_SECRET@CLOUD_NAME
cloud_name = cloudinary_url.split("@")[-1] if "@" in cloudinary_url else ""
if not cloud_name:
    raise SystemExit("CLOUDINARY_URL not set or malformed")

def cloudinary_pdf_url(attendee_id: str) -> str:
    # Mirrors what cloudinary_storage.upload_pdf uses:
    # public_id = solstice/badges/{attendee_id}, format=pdf, resource_type=raw
    return f"https://res.cloudinary.com/{cloud_name}/raw/upload/solstice/badges/{attendee_id}.pdf"

engine = create_engine(url, connect_args={"connect_timeout":30,"ssl":{"ca":certifi.where()}})
with engine.connect() as conn:
    # Find every attendee whose most-recent completed job exists but badge_pdf_url is NULL
    rows = conn.execute(text("""
        SELECT DISTINCT a.id, a.name, a.status
        FROM attendees a
        JOIN badge_jobs j ON j.attendee_id = a.id
        WHERE j.status = 'completed'
          AND (a.badge_pdf_url IS NULL OR a.badge_pdf_url = '')
    """)).fetchall()

    if not rows:
        print("No broken attendees found.")
    else:
        print(f"Found {len(rows)} attendee(s) to fix:")
        for r in rows:
            badge_url = cloudinary_pdf_url(r[0])
            print(f"  {r[1]:30s}  {r[0]}")
            print(f"    -> badge_url: {badge_url}")
            conn.execute(text("""
                UPDATE attendees
                SET status = 'checked_in', badge_pdf_url = :url
                WHERE id = :id
            """), {"url": badge_url, "id": r[0]})

        conn.commit()
        print(f"\nFixed {len(rows)} attendee(s). All set to checked_in with badge URL.")
