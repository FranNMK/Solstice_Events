"""
Phase 3 smoke test — runs directly against a live server.
Usage: python test_phase3.py
The server must already be running on port 8005.
"""

import sys, asyncio
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import httpx, json

BASE = "http://localhost:8005"

def run():
    results = []

    def check(label, resp, expected_status):
        ok = resp.status_code == expected_status
        mark = "[PASS]" if ok else "[FAIL]"
        results.append(ok)
        print(f"{mark} {label}: HTTP {resp.status_code} (expected {expected_status})")
        if not ok:
            print(f"       Body: {resp.text[:200]}")
        return resp

    with httpx.Client(base_url=BASE, timeout=15) as client:
        # 1. Health
        r = client.get("/")
        check("GET /  health", r, 200)

        # 2. Public events list
        r = client.get("/events")
        check("GET /events  (public, 3 seeded)", r, 200)
        events = r.json()
        print(f"       Events returned: {len(events)}")

        # 3. Single event detail
        if events:
            r = client.get(f"/events/{events[0]['id']}")
            check(f"GET /events/:id  ({events[0]['title'][:30]})", r, 200)

        # 4. Register new user
        reg_payload = {"email": "smoketest3@solstice.dev", "password": "smoke123", "role": "customer"}
        r = client.post("/auth/register", json=reg_payload)
        if r.status_code == 409:
            print("[INFO] smoketest3 already exists, logging in instead")
            r = client.post("/auth/login", json={"email": "smoketest3@solstice.dev", "password": "smoke123"})
        check("POST /auth/register or /auth/login", r, 200 if r.status_code == 200 else 201)
        token = r.json().get("access_token", "")
        role  = r.json().get("role", "")
        print(f"       Role: {role}, token: {token[:30]}...")

        headers = {"Authorization": f"Bearer {token}"}

        # 5. Login separately
        r = client.post("/auth/login", json={"email": "smoketest3@solstice.dev", "password": "smoke123"})
        check("POST /auth/login", r, 200)

        # 6. My registrations (empty)
        r = client.get("/attendees/my", headers=headers)
        check("GET /attendees/my  (empty list)", r, 200)

        # 7. Register for first event
        if events:
            r = client.post("/attendees/register", headers=headers, json={
                "event_id": events[0]["id"],
                "name": "Smoke Test User",
                "profession": "QA Engineer",
            })
            if r.status_code == 409:
                print("[INFO] Already registered for this event, skipping register")
                attendee_id = None
            else:
                check("POST /attendees/register", r, 201)
                attendee_id = r.json().get("id")
                qr_id = r.json().get("qr_code_id")
                print(f"       Attendee id: {attendee_id}")
                print(f"       QR code id:  {qr_id}")

            # 8. My registrations (now has one)
            r = client.get("/attendees/my", headers=headers)
            check("GET /attendees/my  (has registration)", r, 200)
            print(f"       Registrations: {len(r.json())}")

            # 9. Status poll
            if attendee_id:
                r = client.get(f"/attendees/{attendee_id}/status", headers=headers)
                check("GET /attendees/:id/status", r, 200)
                print(f"       Status: {r.json().get('status')}")

        # 10. Admin-only route with customer token → 403
        r = client.get("/admin/events", headers=headers)
        check("GET /admin/events  with customer token → 403", r, 403)

        # 11. Login as admin
        r = client.post("/auth/login", json={"email": "admin@solstice.dev", "password": "admin123"})
        check("POST /auth/login  admin", r, 200)
        admin_token = r.json().get("access_token", "")
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # 12. Admin can list all events
        r = client.get("/admin/events", headers=admin_headers)
        check("GET /admin/events  with admin token → 200", r, 200)
        print(f"       All events: {len(r.json())}")

        # 13. Admin can create event
        r = client.post("/admin/events", headers=admin_headers, json={
            "title": "Smoke Test Event",
            "description": "Created by smoke test",
            "date": "2025-12-31T18:00:00Z",
            "location": "Test Venue",
            "is_published": True,
        })
        check("POST /admin/events  create event", r, 201)
        new_event_id = r.json().get("id")
        print(f"       New event id: {new_event_id}")

        # 14. Admin can update event
        r = client.put(f"/admin/events/{new_event_id}", headers=admin_headers, json={"is_published": False})
        check("PUT /admin/events/:id  update event", r, 200)

        # 15. Customer token → 403 on admin events create
        r = client.post("/admin/events", headers=headers, json={
            "title": "Should Fail",
            "date": "2025-12-31T18:00:00Z",
        })
        check("POST /admin/events  with customer token → 403", r, 403)

    passed = sum(results)
    total  = len(results)
    print(f"\n{'='*50}")
    print(f"Phase 3 smoke test: {passed}/{total} passed")
    if passed < total:
        print("SOME TESTS FAILED — review output above")
        sys.exit(1)
    else:
        print("ALL TESTS PASSED")

if __name__ == "__main__":
    run()
