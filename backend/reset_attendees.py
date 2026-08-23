"""
reset_attendees.py — one-shot DB maintenance script.

Resets ALL attendees back to 'registered' status and clears badge_pdf_url,
then deletes all badge_jobs rows. Run this once after migrating badge PDF
storage from Cloudinary to Cloudflare R2, so that every future check-in
generates a fresh badge stored in R2.

Usage (from repo root):
    backend/venv/Scripts/python.exe backend/reset_attendees.py        # Windows
    backend/venv/bin/python          backend/reset_attendees.py        # macOS/Linux

Dry-run mode (prints what would happen, touches nothing):
    DRY_RUN=1 python backend/reset_attendees.py
"""

import os
import sys

# ---------------------------------------------------------------------------
# Bootstrap: add backend/ to path and load .env
# ---------------------------------------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

from dotenv import load_dotenv
load_dotenv(os.path.join(_HERE, ".env"))

from sqlalchemy import create_engine, text
from app.database import _sync_url_base
import certifi

DRY_RUN = os.getenv("DRY_RUN", "0").strip() in ("1", "true", "yes")

# ---------------------------------------------------------------------------
# Sync engine (pymysql) — same one the worker uses
# ---------------------------------------------------------------------------
engine = create_engine(
    _sync_url_base,
    echo=False,
    pool_pre_ping=True,
    connect_args={
        "connect_timeout": 30,
        "ssl": {"ca": certifi.where()},
    },
)

DIVIDER = "-" * 60

def _run():
    with engine.connect() as conn:
        # ── 1. Inspect current state ──────────────────────────────────────
        print(DIVIDER)
        print("CURRENT ATTENDEE STATUS BREAKDOWN")
        print(DIVIDER)
        rows = conn.execute(text(
            "SELECT status, COUNT(*) AS cnt FROM attendees GROUP BY status"
        )).fetchall()
        total = 0
        for row in rows:
            print(f"  {row[0]:<15} {row[1]:>4}")
            total += row[1]
        print(f"  {'TOTAL':<15} {total:>4}")

        print()
        print("BADGE_PDF_URL SAMPLES (first 10 checked_in)")
        print(DIVIDER)
        samples = conn.execute(text(
            "SELECT id, name, badge_pdf_url "
            "FROM attendees WHERE status='checked_in' LIMIT 10"
        )).fetchall()
        if not samples:
            print("  (none)")
        for s in samples:
            url = s[2] or "(null)"
            # Truncate long URLs for display
            display = url if len(url) < 80 else url[:77] + "..."
            print(f"  [{s[0][:8]}…] {s[1]:<25} {display}")

        print()
        badge_job_count = conn.execute(
            text("SELECT COUNT(*) FROM badge_jobs")
        ).scalar()
        print(f"BADGE JOBS ROW COUNT: {badge_job_count}")
        print()

        if DRY_RUN:
            print("DRY RUN — no changes made.")
            print(DIVIDER)
            print("Would execute:")
            print("  DELETE FROM badge_jobs")
            print("  UPDATE attendees SET status='registered', badge_pdf_url=NULL")
            return

        # ── 2. Confirm before destructive write ───────────────────────────
        print(">>> This will DELETE all badge_jobs and reset ALL attendees to")
        print("    status='registered' with badge_pdf_url=NULL.")
        print(">>> Everyone will need to be re-scanned at the door.")
        print()
        answer = input("Type YES to proceed, anything else to abort: ").strip()
        if answer != "YES":
            print("Aborted — no changes made.")
            return

        # ── 3. Delete badge_jobs first (FK constraint) ────────────────────
        result = conn.execute(text("DELETE FROM badge_jobs"))
        jobs_deleted = result.rowcount
        print(f"  Deleted {jobs_deleted} badge_job row(s).")

        # ── 4. Reset all attendees ─────────────────────────────────────────
        result = conn.execute(text(
            "UPDATE attendees SET status='registered', badge_pdf_url=NULL"
        ))
        attendees_reset = result.rowcount
        print(f"  Reset {attendees_reset} attendee row(s) to status='registered'.")

        conn.commit()

        # ── 5. Verify ──────────────────────────────────────────────────────
        print()
        print("POST-RESET VERIFICATION")
        print(DIVIDER)
        rows2 = conn.execute(text(
            "SELECT status, COUNT(*) AS cnt FROM attendees GROUP BY status"
        )).fetchall()
        for row in rows2:
            print(f"  {row[0]:<15} {row[1]:>4}")
        remaining_jobs = conn.execute(
            text("SELECT COUNT(*) FROM badge_jobs")
        ).scalar()
        print(f"  badge_jobs remaining: {remaining_jobs}")
        print()
        print("Done. All attendees reset. Re-scan to generate R2 badges.")
        print(DIVIDER)


if __name__ == "__main__":
    _run()
