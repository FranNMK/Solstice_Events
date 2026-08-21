import sys, asyncio, warnings
if sys.platform == "win32":
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import httpx
from app.main import app

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
        if not ok: print("       " + resp.text[:200])
        return resp

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:

        print("\n--- Health & Public ---")
        check("GET /", await c.get("/"), 200)
        r = check("GET /events", await c.get("/events"), 200)
        events = r.json()
        print("  " + str(len(events)) + " published events")
        event_id = events[0]["id"] if events else None
        if event_id:
            check("GET /events/:id", await c.get("/events/" + event_id), 200)

        print("\n--- Auth ---")
        r = await c.post("/auth/register", json={"email": TEST_EMAIL, "password": TEST_PASS, "role": "customer"})
        if r.status_code == 409:
            r = await c.post("/auth/login", json={"email": TEST_EMAIL, "password": TEST_PASS})
        results.append(r.status_code in (200, 201))
        print(("[PASS]" if results[-1] else "[FAIL]") + "  POST /auth/register|login -> HTTP " + str(r.status_code))
        token = r.json().get("access_token", "")
        print("  role=" + r.json().get("role","") + "  token=" + token[:24] + "...")
        hdrs = {"Authorization": "Bearer " + token}

        check("POST /auth/login", await c.post("/auth/login", json={"email": TEST_EMAIL, "password": TEST_PASS}), 200)
        check("POST /auth/login bad pass", await c.post("/auth/login", json={"email": TEST_EMAIL, "password": "wrong"}), 401)

        print("\n--- Attendee registration ---")
        r = check("GET /attendees/my", await c.get("/attendees/my", headers=hdrs), 200)
        att_id = None
        if event_id:
            r = await c.post("/attendees/register", headers=hdrs,
                             json={"event_id": event_id, "name": "Phase3 Tester", "profession": "Engineer"})
            if r.status_code == 409:
                print("  [INFO] Already registered, using existing")
                existing = (await c.get("/attendees/my", headers=hdrs)).json()
                att_id = existing[0]["id"] if existing else None
            else:
                check("POST /attendees/register", r, 201)
                att_id = r.json().get("id")
                print("  attendee_id=" + str(att_id))
                print("  qr_code_id=" + str(r.json().get("qr_code_id")))

            r = check("GET /attendees/my (with reg)", await c.get("/attendees/my", headers=hdrs), 200)
            print("  " + str(len(r.json())) + " registrations, event embedded=" + str("event" in r.json()[0]))
            if att_id:
                r = check("GET /attendees/:id/status", await c.get("/attendees/" + att_id + "/status", headers=hdrs), 200)
                print("  status=" + r.json().get("status",""))
                check("GET /attendees/:id/badge (no badge yet) -> 404",
                      await c.get("/attendees/" + att_id + "/badge", headers=hdrs), 404)

        print("\n--- Role enforcement ---")
        check("GET /admin/events customer -> 403", await c.get("/admin/events", headers=hdrs), 403)
        check("POST /admin/events customer -> 403", await c.post("/admin/events", headers=hdrs,
              json={"title": "x", "date": "2025-12-31T18:00:00Z"}), 403)
        check("GET /attendees/my no auth -> 401", await c.get("/attendees/my"), 401)

        print("\n--- Admin operations ---")
        r = check("POST /auth/login admin", await c.post("/auth/login",
                  json={"email": ADMIN_EMAIL, "password": ADMIN_PASS}), 200)
        ah = {"Authorization": "Bearer " + r.json().get("access_token", "")}
        r = check("GET /admin/events", await c.get("/admin/events", headers=ah), 200)
        print("  " + str(len(r.json())) + " total events")
        r = check("POST /admin/events", await c.post("/admin/events", headers=ah, json={
            "title":"Phase3 Smoke Event","description":"auto","date":"2026-01-15T09:00:00Z",
            "location":"Test City","is_published":True}), 201)
        new_id = r.json().get("id")
        check("PUT /admin/events/:id", await c.put("/admin/events/" + new_id, headers=ah,
              json={"is_published": False}), 200)
        if event_id:
            r = check("GET /admin/events/:id/attendees", await c.get(
                "/admin/events/" + event_id + "/attendees", headers=ah), 200)
            print("  " + str(len(r.json())) + " attendee(s) for seeded event")

    p, t = sum(results), len(results)
    print("\n" + "="*50)
    print("Phase 3: " + str(p) + "/" + str(t) + " passed")
    print("="*50)
    if p < t:
        print("SOME TESTS FAILED"); sys.exit(1)
    else:
        print("ALL TESTS PASSED")

asyncio.run(run())