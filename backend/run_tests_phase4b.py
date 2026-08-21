import sys, asyncio, warnings, json, hashlib, hmac as hmac_mod
if sys.platform == "win32":
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import httpx
from app.main import app
from app.config import settings
from app.services.worker import _sign_payload

ATT_ID = "34bcb064-5b76-469b-8c59-530e2c814a74"
QR_ID  = "5028d4e6-e34f-4131-9c31-c112453b739c"
JOB_ID = "b43441c1-80d6-4c30-9174-dcbb125d691a"

async def run():
    results = []
    def check(label, resp, expected):
        ok = resp.status_code == expected
        results.append(ok)
        print(("[PASS]" if ok else "[FAIL]") + "  " + label + "  -> HTTP " + str(resp.status_code))
        if not ok: print("       " + resp.text[:300])
        return resp

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:

        print("\n--- Direct webhook test with valid signature ---")
        payload = json.dumps(
            {"job_id": JOB_ID, "attendee_id": ATT_ID,
             "badge_pdf_url": "/static/badges/" + ATT_ID + ".pdf",
             "timestamp": "2025-01-01T00:00:00"},
            separators=(",", ":"))
        sig = _sign_payload(payload)
        print("  Payload: " + payload)
        print("  Signature: " + sig[:24] + "...")

        r = check("POST /webhooks/badge-complete valid sig -> 200",
            await c.post("/webhooks/badge-complete",
                content=payload.encode(),
                headers={"Content-Type": "application/json", "X-Signature": sig}), 200)
        print("  Response: " + r.text)

        print("\n--- Verify attendee status flipped to checked_in ---")
        r = await c.post("/auth/login", json={"email":"phase3test@solstice.dev","password":"test123"})
        uh = {"Authorization": "Bearer " + r.json().get("access_token","")}
        sr = (await c.get("/attendees/" + ATT_ID + "/status", headers=uh)).json()
        ok = sr.get("status") == "checked_in"
        results.append(ok)
        print(("[PASS]" if ok else "[FAIL]") + "  Status: " + sr.get("status","") + "  badge_url: " + str(sr.get("badge_pdf_url","")))

        print("\n--- Verify duplicate scan returns already_checked_in ---")
        r = await c.post("/auth/login", json={"email":"admin@solstice.dev","password":"admin123"})
        ah = {"Authorization": "Bearer " + r.json().get("access_token","")}
        r = check("POST /checkin (already checked_in) -> 200",
            await c.post("/checkin", headers=ah, json={"qr_code_id": QR_ID}), 200)
        ok_dup = r.json().get("already_checked_in") == True
        results.append(ok_dup)
        print(("[PASS]" if ok_dup else "[FAIL]") + "  already_checked_in=" + str(r.json().get("already_checked_in")))

        print("\n--- Badge PDF accessible after checked_in ---")
        r = check("GET /attendees/:id/badge -> 200",
            await c.get("/attendees/" + ATT_ID + "/badge", headers=uh), 200)
        ok_pdf = r.headers.get("content-type","").startswith("application/pdf")
        results.append(ok_pdf)
        print(("[PASS]" if ok_pdf else "[FAIL]") + "  Content-Type: " + r.headers.get("content-type",""))

    p, t = sum(results), len(results)
    print("\n" + "="*50)
    print("Phase 4 webhook + downstream: " + str(p) + "/" + str(t) + " passed")
    print("="*50)
    if p < t: sys.exit(1)
    else: print("ALL TESTS PASSED")

asyncio.run(run())