import sys, asyncio, warnings, json
if sys.platform == "win32":
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import httpx
from app.main import app
from app.services.worker import _sign_payload

ATT_ID = "34bcb064-5b76-469b-8c59-530e2c814a74"
QR_ID  = "5028d4e6-e34f-4131-9c31-c112453b739c"

async def run():
    results = []
    def check(label, resp, expected):
        ok = resp.status_code == expected
        results.append(ok)
        print(("[PASS]" if ok else "[FAIL]") + "  " + label + "  -> HTTP " + str(resp.status_code))
        if not ok: print("       " + resp.text[:300])
        return resp

    # Generate the actual badge PDF for this attendee
    from datetime import datetime, timezone
    from app.services.badge import generate_badge_pdf
    fp, url = generate_badge_pdf(
        attendee_id=ATT_ID,
        name="Phase3 Tester",
        profession="Engineer",
        event_title="Solstice Tech Summit 2025",
        event_date=datetime(2025, 8, 15, 18, 0, tzinfo=timezone.utc),
        qr_code_id=QR_ID,
    )
    print("[SETUP] Badge PDF generated: " + fp)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        r = await c.post("/auth/login", json={"email":"phase3test@solstice.dev","password":"test123"})
        uh = {"Authorization": "Bearer " + r.json().get("access_token","")}

        print("\n--- Badge download (checked_in + file exists) ---")
        r = check("GET /attendees/:id/badge -> 200 PDF",
            await c.get("/attendees/" + ATT_ID + "/badge", headers=uh), 200)
        ok_pdf = r.headers.get("content-type","").startswith("application/pdf")
        results.append(ok_pdf)
        print(("[PASS]" if ok_pdf else "[FAIL]") + "  content-type=" + r.headers.get("content-type",""))
        print("  PDF size: " + str(len(r.content)) + " bytes")

    p, t = sum(results), len(results)
    print("\n" + "="*50)
    print("Phase 4 badge download: " + str(p) + "/" + str(t) + " passed")
    if p < t: sys.exit(1)
    else: print("ALL PASSED")

asyncio.run(run())