import sys, asyncio, warnings, time, json, hashlib, hmac as hmac_mod
if sys.platform == "win32":
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import httpx
from app.main import app
from app.config import settings

ADMIN_EMAIL = "admin@solstice.dev"
ADMIN_PASS  = "admin123"
TEST_EMAIL  = "phase3test@solstice.dev"
TEST_PASS   = "test123"

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

        print("\n--- Setup: get tokens and attendee ---")
        r = await c.post("/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASS})
        ah = {"Authorization": "Bearer " + r.json().get("access_token", "")}

        r = await c.post("/auth/login", json={"email": TEST_EMAIL, "password": TEST_PASS})
        uh = {"Authorization": "Bearer " + r.json().get("access_token", "")}

        regs = (await c.get("/attendees/my", headers=uh)).json()
        if not regs:
            print("  No registration found - need to register first")
            events = (await c.get("/events")).json()
            r = await c.post("/attendees/register", headers=uh,
                json={"event_id": events[0]["id"], "name": "P4 Tester", "profession": "Dev"})
            regs = [r.json()]
        att_id = regs[0]["id"]
        qr_id  = regs[0]["qr_code_id"]
        print("  attendee_id=" + att_id + "  qr_code_id=" + qr_id)

        print("\n--- Import checks ---")
        from app.services.badge import generate_badge_pdf
        from app.services.worker import _sign_payload
        from app.routes.checkin import router as cr
        from app.routes.webhooks import router as wr
        results.append(True); print("[PASS]  All Phase 4 modules import OK")

        print("\n--- Badge PDF generation (unit test) ---")
        from datetime import datetime, timezone
        fp, url = generate_badge_pdf(
            attendee_id="test-badge-001",
            name="Jane Smith",
            profession="Software Engineer",
            event_title="Solstice Tech Summit 2025",
            event_date=datetime(2025, 8, 15, 18, 0, tzinfo=timezone.utc),
            qr_code_id=qr_id,
        )
        import os
        ok = os.path.exists(fp)
        results.append(ok)
        print(("[PASS]" if ok else "[FAIL]") + "  Badge PDF created at: " + fp)

        print("\n--- HMAC signature ---")
        payload = json.dumps({"job_id":"j1","attendee_id":"a1","badge_pdf_url":"/static/badges/a1.pdf","timestamp":"2025-01-01T00:00:00"}, separators=(",",":"))
        sig = _sign_payload(payload)
        expected = hmac_mod.new(settings.WEBHOOK_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
        ok = sig == expected
        results.append(ok)
        print(("[PASS]" if ok else "[FAIL]") + "  HMAC signature matches: " + sig[:16] + "...")

        print("\n--- Webhook signature validation ---")
        r = await c.post("/webhooks/badge-complete",
            content=payload.encode(),
            headers={"Content-Type": "application/json", "X-Signature": "bad_signature"})
        check("POST /webhooks/badge-complete bad sig -> 401", r, 401)

        r = await c.post("/webhooks/badge-complete",
            content="{}".encode(),
            headers={"Content-Type": "application/json",
                     "X-Signature": _sign_payload("{}")})
        check("POST /webhooks/badge-complete missing fields -> 400", r, 400)

        print("\n--- Full check-in pipeline ---")
        # Reset attendee to 'registered' if it was already pending/checked_in from prev run
        # (We do this by directly using the test attendee; re-register if needed)
        status_r = (await c.get("/attendees/" + att_id + "/status", headers=uh)).json()
        print("  Current status: " + status_r.get("status",""))

        if status_r.get("status") == "checked_in":
            print("  [INFO] Already checked_in from previous run. Testing duplicate scan only.")
            r = check("POST /checkin (already checked_in) -> 200 already_checked_in=true",
                      await c.post("/checkin", headers=ah, json={"qr_code_id": qr_id}), 200)
            results.append(r.json().get("already_checked_in") == True)
            print(("[PASS]" if results[-1] else "[FAIL]") + "  already_checked_in=" + str(r.json().get("already_checked_in")))
        else:
            # Fresh scan
            r = check("POST /checkin (new) -> 200 status=pending",
                      await c.post("/checkin", headers=ah, json={"qr_code_id": qr_id}), 200)
            body = r.json()
            ok_pending = body.get("status") == "pending" and body.get("already_checked_in") == False
            results.append(ok_pending)
            print(("[PASS]" if ok_pending else "[FAIL]") + "  status=pending already_checked_in=False")
            job_id = body.get("job_id")
            print("  job_id=" + str(job_id))

            # Duplicate scan while pending
            r2 = check("POST /checkin (duplicate while pending) -> 200 already_checked_in=true",
                       await c.post("/checkin", headers=ah, json={"qr_code_id": qr_id}), 200)
            ok_dup = r2.json().get("already_checked_in") == True
            results.append(ok_dup)
            print(("[PASS]" if ok_dup else "[FAIL]") + "  already_checked_in=True (blocked correctly)")

            print("\n--- Polling: waiting for worker to complete (up to 30s) ---")
            final_status = "pending"
            for i in range(15):
                await asyncio.sleep(2)
                sr = (await c.get("/attendees/" + att_id + "/status", headers=uh)).json()
                final_status = sr.get("status", "")
                print("  poll " + str(i+1) + ": status=" + final_status + " badge=" + str(sr.get("badge_pdf_url","none")))
                if final_status == "checked_in":
                    break

            ok_ci = final_status == "checked_in"
            results.append(ok_ci)
            print(("[PASS]" if ok_ci else "[FAIL]") + "  Final status: " + final_status)

            if ok_ci:
                r = check("GET /attendees/:id/badge -> 200 (PDF available)",
                          await c.get("/attendees/" + att_id + "/badge", headers=uh), 200)
                results.append(r.headers.get("content-type","").startswith("application/pdf"))
                print(("[PASS]" if results[-1] else "[FAIL]") + "  Content-Type: application/pdf")

        # Customer cannot access admin-only checkin
        check("POST /checkin customer -> 403", await c.post("/checkin", headers=uh, json={"qr_code_id": qr_id}), 403)

    p, t = sum(results), len(results)
    print("\n" + "="*50)
    print("Phase 4: " + str(p) + "/" + str(t) + " passed")
    print("="*50)
    if p < t:
        print("SOME TESTS FAILED"); sys.exit(1)
    else:
        print("ALL TESTS PASSED")

asyncio.run(run())