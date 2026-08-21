# Solstice Events — Full-Stack Build Plan

<!-- Last updated after Phase 3 commit: c9b4dac -->

## Top-Level Overview

Build a full-stack event registration and check-in system called **Solstice Events** from scratch in an
empty workspace. The system has two distinct user experiences:

- **Customer side**: browse events, register, receive email confirmation with QR code, view dashboard,
  download badge PDF after check-in.
- **Admin side**: publish/manage events, scan attendee QR codes at the door, watch check-in statuses
  update in real time without a page refresh.

The defining architectural requirement is the **async badge generation pipeline**: check-in does NOT
synchronously produce a PDF. Instead it enqueues a job, a background worker generates the PDF and calls
back via an internal webhook (signed), and the frontend polls to reflect the status change automatically.

### Tech Stack (fixed)
| Layer | Choice |
|---|---|
| Backend | Python 3.11 + FastAPI |
| Database | TiDB Cloud (SSL) via SQLAlchemy async — `mysql+aiomysql` with `ssl_ca` |
| Frontend | React 18 (Vite) — functional components + hooks |
| Auth | JWT (python-jose) — roles: `customer` / `admin` |
| Email | Resend Python SDK — graceful fallback: if `RESEND_API_KEY` not set, logs email to console |
| QR codes | `qrcode[pil]` Python lib — server-side |
| PDF | `reportlab` — server-side badge generation |
| Env | Python venv (`backend/venv`) |

### Repository Layout (target)
```
solstice-events-plan.md   ← this file
logo.png                  ← platform logo (navy/orange brand)
backend/
  venv/                   ← Python virtual environment (gitignored)
  app/
    main.py
    config.py
    database.py
    models.py
    schemas.py
    auth/
      router.py
      utils.py
    routes/
      events.py
      attendees.py
      checkin.py
      webhooks.py
    services/
      email.py
      qr.py
      badge.py
      worker.py
    static/
      qrcodes/
      badges/
  seed.py
  requirements.txt
  .env.example
frontend/
  package.json
  vite.config.js
  src/
    main.jsx
    App.jsx
    api/           ← axios instance + per-resource helpers
    components/    ← shared UI: Navbar, Toast, Spinner, StatusPill, Modal
    pages/
      Landing.jsx
      Events.jsx
      Register.jsx
      Login.jsx
      Dashboard.jsx
      admin/
        AdminDashboard.jsx
        EventForm.jsx
        AttendeeList.jsx
        ScanPage.jsx
    hooks/
      useAuth.js
      usePolling.js
    context/
      AuthContext.jsx
```

---

## Phase 1 — Project Scaffolding & Configuration

### Intent
Create the folder structure, install all dependencies, and wire up configuration/environment files so
every subsequent phase has a stable foundation to build on.

### Expected Outcomes
- `backend/` directory with Python venv, `requirements.txt`, working FastAPI app returning `{"status":"ok"}`
- `frontend/` Vite+React project with Tailwind CSS and project-wide routing scaffolded
- `.env.example` with all required keys documented
- Both dev servers can start without errors

### Todo List
1. Create `backend/` folder; set up Python venv; create `requirements.txt` with:
   `fastapi uvicorn[standard] sqlalchemy aiomysql python-dotenv python-jose[cryptography]
   passlib[bcrypt] qrcode[pil] reportlab resend python-multipart httpx`
2. Create `backend/app/main.py` — FastAPI app with CORS, mounts `/static`, includes all routers
   (stubs for now), and starts the background worker thread on startup.
3. Create `backend/app/config.py` — reads all env vars via `python-dotenv`; exposes a `settings` object.
4. Create `backend/.env.example`:
   ```
   TIDB_URL=mysql+aiomysql://user:password@host:4000/solstice_events?ssl_ca=/etc/ssl/certs/ca-certificates.crt
   JWT_SECRET=change_me
   JWT_ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=60
   RESEND_API_KEY=re_...
   RESEND_FROM=onboarding@resend.dev
   WEBHOOK_SECRET=some_random_secret
   BADGE_BASE_URL=http://localhost:8000
   ```
5. Scaffold `frontend/` with `npm create vite@latest frontend -- --template react`, install
   `tailwindcss`, `@headlessui/react`, `axios`, `react-router-dom`, `react-hot-toast`,
   `react-qr-code`, `@zxing/library` (QR scanner).
6. Configure Tailwind with the brand color palette:
   - `primary`: `#F97316` (orange), `dark`: `#1E2A4A` (navy), neutral grays.
7. Create `frontend/src/context/AuthContext.jsx` — stores JWT token + decoded role in state,
   exposes `login()`, `logout()`, `user` to the whole app.
8. Create `frontend/src/App.jsx` — top-level router with protected route wrappers:
   `<ProtectedRoute role="customer">` and `<ProtectedRoute role="admin">`.

### Relevant Context
- Logo at `logo.png` — navy/orange palette. Copy it into `frontend/public/logo.png`.
- TiDB uses MySQL wire protocol; SQLAlchemy async dialect is `mysql+aiomysql`.
- Resend free tier: sender must be `onboarding@resend.dev` (no custom domain required).

### Status
[x] done — commit 9006f97

---

## Phase 2 — Database Models & Migrations

### Intent
Define all SQLAlchemy ORM models matching the specified data model and create the tables in TiDB.
No migration framework needed — use `Base.metadata.create_all` for initial setup.

### Expected Outcomes
- All four tables exist in TiDB: `users`, `events`, `attendees`, `badge_jobs`
- `seed.py` successfully inserts a demo admin, a demo customer, and 3 demo events
- Models are importable without errors

### Todo List
1. Create `backend/app/database.py`:
   - Async SQLAlchemy engine using `TIDB_URL` from settings
   - `AsyncSession` factory
   - `Base` declarative class
   - `get_db()` dependency for FastAPI
2. Create `backend/app/models.py` with ORM classes:
   - `User`: id (UUID), email (unique), hashed_password, role (`customer`/`admin`), created_at
   - `Event`: id (UUID), title, description, date (DateTime), location, image_url, is_published (bool),
     created_by (FK → users.id)
   - `Attendee`: id (UUID), user_id (FK), event_id (FK), name, profession, qr_code_id (unique UUID),
     status (enum: `registered`/`pending`/`checked_in`), badge_pdf_url (nullable), created_at
   - `BadgeJob`: id (UUID), attendee_id (FK), status (enum: `queued`/`processing`/`completed`),
     created_at, completed_at (nullable)
3. In `backend/app/main.py` startup event: call `Base.metadata.create_all(engine)` (sync engine for DDL).
4. Create `backend/seed.py`:
   - Creates admin user (email: `admin@solstice.dev`, password: `admin123`, role: `admin`)
   - Creates customer user (email: `demo@solstice.dev`, password: `demo123`, role: `customer`)
   - Inserts 3 demo events (published) with realistic titles/dates/locations/image URLs from Unsplash

### Relevant Context
- UUIDs should be stored as `CHAR(36)` or use `String(36)` with `default=lambda: str(uuid.uuid4())`.
- TiDB does not support all MySQL features — avoid foreign key constraints if they cause issues;
  use application-level integrity instead.
- `is_published` flag controls which events appear on the public listing.

### Status
[x] done — commit e2ee5c6

---

## Phase 3 — Backend Auth & Core APIs

### Intent
Implement JWT authentication (register, login, token refresh) and the core CRUD APIs for events and
attendees, with role-based route protection.

### Expected Outcomes
- `POST /auth/register` and `POST /auth/login` return valid JWTs
- Admin JWT-protected routes return 403 when called with a customer token
- `GET /events` (public) returns published events
- `POST /events` (admin only) creates an event
- `POST /attendees/register` registers a customer for an event, generates QR, sends email

### Todo List
1. Create `backend/app/auth/utils.py`:
   - `hash_password()`, `verify_password()` using `passlib bcrypt`
   - `create_access_token()`, `decode_token()` using `python-jose`
   - `get_current_user()` FastAPI dependency (reads Bearer token from Authorization header)
   - `require_role(role)` dependency factory returning 403 if role mismatch
2. Create `backend/app/auth/router.py`:
   - `POST /auth/register` — creates user, returns token
   - `POST /auth/login` — validates credentials, returns token
3. Create `backend/app/routes/events.py`:
   - `GET /events` — public, returns published events only
   - `GET /events/{id}` — public, single event detail
   - `POST /events` — admin only, creates event
   - `PUT /events/{id}` — admin only, updates/publishes event
   - `GET /admin/events/{id}/attendees` — admin only, lists all attendees for an event
4. Create `backend/app/services/qr.py`:
   - `generate_qr(qr_code_id: str) -> str` — generates a PNG QR code encoding the attendee's
     `qr_code_id`, saves to `backend/app/static/qrcodes/{qr_code_id}.png`, returns relative URL.
5. Create `backend/app/services/email.py`:
   - `send_confirmation_email(to, name, event_title, event_date, event_location, qr_url)` — uses
     Resend SDK, sends from `RESEND_FROM`, includes event details and QR code URL in HTML body.
6. Create `backend/app/routes/attendees.py`:
   - `POST /attendees/register` — customer auth required; registers for event, calls QR service,
     calls email service, returns attendee record
   - `GET /attendees/my` — customer auth; returns all attendees records for the current user
   - `GET /attendees/{id}/status` — auth required; returns `{status, badge_pdf_url}` — used for polling
   - `GET /attendees/{id}/qr` — customer auth; returns QR code image URL for this attendee
7. Create `backend/app/schemas.py` — Pydantic v2 models for all request/response shapes.

### Relevant Context
- `require_role("admin")` must be used as a dependency on all `/admin/*` and event-mutation routes.
- The QR code encodes only the `qr_code_id` string — the scan page will send this value to the
  check-in endpoint. Do not encode a full URL in the QR.
- Email sending should be fire-and-forget (wrap in `asyncio.create_task`) so it does not block registration.

### Status
[x] done — commit c9b4dac (18/18 smoke tests passing)

---

## Phase 4 — Async Check-in & Badge Pipeline

### Intent
Implement the core async pipeline: check-in endpoint enqueues a job, a background worker generates
the badge PDF and calls the internal signed webhook, the webhook handler updates the attendee record.
This is the most architecturally critical phase.

### Expected Outcomes
- `POST /checkin` with a valid QR code ID sets status to `pending` and inserts a `BadgeJob` row,
  then returns immediately (no PDF generated yet)
- Duplicate scan correctly returns `{"already_checked_in": true}` without inserting a new job
- Background worker picks up `queued` jobs, simulates delay, generates PDF, calls webhook
- Webhook validates HMAC-SHA256 signature and sets attendee `status = checked_in` + `badge_pdf_url`
- `GET /attendees/{id}/status` reflects the change within ~5 seconds of the scan

### Todo List
1. Create `backend/app/routes/checkin.py`:
   - `POST /checkin` — admin auth required
   - Accepts `{qr_code_id: str}`
   - Looks up attendee by `qr_code_id`
   - If `status == checked_in` OR `status == pending` → return `{"already_checked_in": true, "status": current_status}`
   - Otherwise: set `status = pending`, insert `BadgeJob(status="queued")`, return `{"job_id": ..., "attendee_id": ...}`
   - Use a DB-level transaction to prevent race conditions on concurrent scans of the same attendee
2. Create `backend/app/services/badge.py`:
   - `generate_badge_pdf(attendee, event) -> str` — uses `reportlab` to produce a card-style A6 PDF:
     - Attendee name (large, bold)
     - Profession (subtitle)
     - Event name + formatted date
     - QR code image embedded (reads from static/qrcodes/)
     - Solstice Events logo (if accessible) or brand text
   - Saves to `backend/app/static/badges/{attendee_id}.pdf`
   - Returns relative URL path
3. Create `backend/app/services/worker.py`:
   - `BadgeWorker` class with a `run()` method that loops indefinitely (sleep 2s between polls)
   - On each tick: query `BadgeJob` WHERE `status = queued` (take 1 at a time)
   - Mark job `status = processing`
   - Simulate delay: `time.sleep(random.randint(3, 5))`
   - Generate badge PDF via `badge.py`
   - Build webhook payload: `{job_id, attendee_id, badge_pdf_url, timestamp}`
   - Compute HMAC-SHA256 signature over JSON payload using `WEBHOOK_SECRET`
   - POST to `{BADGE_BASE_URL}/webhooks/badge-complete` with `X-Signature` header
   - Mark job `status = completed`, set `completed_at`
   - Run `BadgeWorker` in a daemon thread started from `main.py` lifespan startup.
4. Create `backend/app/routes/webhooks.py`:
   - `POST /webhooks/badge-complete` — no auth header, but validates `X-Signature` HMAC
   - If signature invalid → 401
   - Updates `Attendee.status = checked_in` and `Attendee.badge_pdf_url`
   - Returns `{"ok": true}`
5. Add `GET /attendees/{id}/badge` — returns the PDF file (FileResponse) if status is `checked_in`,
   else 404. This is used by the "Download Badge" button.

### Relevant Context
- The worker must use its **own synchronous SQLAlchemy session** (not the async one) since it runs
  in a thread, not in an async context. Create a separate sync engine for the worker.
- The HMAC signature: `hmac.new(WEBHOOK_SECRET.encode(), json_body.encode(), hashlib.sha256).hexdigest()`
- The webhook endpoint must re-compute the same HMAC over the raw request body to validate.
- Duplicate-scan protection: the check at the top of `POST /checkin` covers both `checked_in` AND
  `pending` — this prevents a second badge job being queued while the first is still processing.

### Status
[x] done — commit f6d91a6

---

## Phase 5 — Frontend: Public Pages & Auth

### Intent
Build the customer-facing public pages: landing page with carousel, events listing, register/login
forms, and the auth context wiring that gates the rest of the app.

### Expected Outcomes
- Landing page renders with hero section + event carousel (calls `GET /events`)
- Events grid page lists all published events with countdown
- Register and Login pages submit to backend, store JWT in AuthContext, redirect by role
- Protected routes redirect unauthenticated users to `/login`

### Todo List
1. Create `frontend/src/api/index.js` — axios instance with `baseURL = import.meta.env.VITE_API_URL`,
   request interceptor attaches `Authorization: Bearer <token>` from localStorage.
2. Create `frontend/src/api/events.js`, `auth.js`, `attendees.js` — thin wrappers around axios calls.
3. Create `frontend/src/components/Navbar.jsx` — logo, nav links, user menu (logout), role-aware links.
4. Create `frontend/src/components/EventCard.jsx` — card with image, title, date, location, countdown
   pill, "Register" button. Countdown: `Math.ceil((eventDate - now) / 86400000)` days.
5. Create `frontend/src/components/StatusPill.jsx` — colored pill:
   `registered` → gray, `pending` → amber, `checked_in` → green.
6. Create `frontend/src/pages/Landing.jsx`:
   - Hero section: full-width background, logo, tagline, CTA buttons
   - Carousel (CSS-only or Headless UI Transition) showing 3 featured upcoming events
   - "Browse All Events" link
7. Create `frontend/src/pages/Events.jsx` — grid of EventCards, calls `GET /events`
8. Create `frontend/src/pages/Login.jsx` and `Register.jsx`:
   - Forms with loading spinner on submit
   - On success: store token, decode role from JWT payload, redirect:
     - `admin` → `/admin`
     - `customer` → `/dashboard`
9. Create `frontend/src/hooks/useAuth.js` — convenience hook that reads from `AuthContext`.
10. Implement route protection in `App.jsx`: wrap customer routes in `<RequireAuth role="customer">`,
    admin routes in `<RequireAuth role="admin">`.

### Relevant Context
- JWT payload contains `{sub: user_id, role: "customer"|"admin", exp}` — decode client-side with
  `atob()` on the middle segment (no library needed).
- Toast notifications via `react-hot-toast`: show on login success, registration success, errors.
- Brand colors already configured in Tailwind — use `bg-primary`, `text-dark`, etc.
- `VITE_API_URL=http://localhost:8000` goes in `frontend/.env`.

### Status
[x] done — phases 5 & 6 implementation

---

## Phase 6 — Frontend: Customer Dashboard

### Intent
Build the logged-in customer experience: list their registered events, show QR code per event,
show badge download after check-in (via polling).

### Expected Outcomes
- Dashboard renders the customer's registrations with status pills
- "View QR Code" expands/shows the QR image for each registration
- Polling every 3 seconds updates status from `pending` → `checked_in` without page refresh
- "View/Download Badge" button appears only when `status === checked_in`
- "Print Badge" opens PDF in new tab and triggers `window.print()`

### Todo List
1. Create `frontend/src/pages/Dashboard.jsx`:
   - Calls `GET /attendees/my` on mount to get user's registrations
   - Renders a card per registration with event name, date, location, status pill
   - "Register for an event" CTA if list is empty
2. Create `frontend/src/hooks/usePolling.js`:
   - `usePolling(fn, interval, condition)` — calls `fn()` every `interval` ms while `condition` is true
   - Used to poll `GET /attendees/{id}/status` when status is `pending`
3. Per registration card:
   - "View QR Code" toggle — renders `<QRCodeSVG value={qr_code_id} />` from `react-qr-code`
   - When status transitions to `checked_in`: show "Download Badge" (`<a href="/attendees/{id}/badge" download>`)
     and "Print Badge" button that opens PDF in new tab + calls `window.print()`
4. Registration flow: `frontend/src/pages/Register.jsx` (event-specific):
   - Accepts `eventId` from URL param
   - Form: name, email (pre-filled from auth), profession
   - Calls `POST /attendees/register`, shows toast, redirects to `/dashboard`

### Relevant Context
- `react-qr-code` renders the QR as an SVG from the raw `qr_code_id` value — this is what the
  customer presents at the door.
- Polling should stop once status reaches `checked_in` (condition becomes false).
- Badge PDF URL: use the backend route `GET /attendees/{id}/badge` which streams the file.

### Status
[x] done — phases 5 & 6 implementation

---

## Phase 7 — Frontend: Admin Dashboard & Scan Page

### Intent
Build the admin experience: event management (create/publish), attendee list per event, and the
real-time QR scan + check-in page with status polling.

### Expected Outcomes
- Admin can create an event and publish it (it then appears on the public listing)
- Admin can view all attendees per event with their current status
- Scan page uses device camera (via `@zxing/library`) to read a QR code
- On scan: calls `POST /checkin`, shows "Pending…" immediately
- Polling updates the scanned attendee's status to "Checked In ✓" without refresh
- Duplicate scan shows "Already checked in" inline
- Badge PDF link appears in the admin scan result once `checked_in`

### Todo List
1. Create `frontend/src/pages/admin/AdminDashboard.jsx`:
   - Lists all events (calls `GET /events` without published filter for admin — add admin variant)
   - "Create Event" button → navigates to `EventForm`
   - Per event: attendee count, "View Attendees" link, "Edit" link, publish toggle
2. Create `frontend/src/pages/admin/EventForm.jsx`:
   - Fields: title, description, date (datetime-local), location, image URL
   - Save → `POST /events`; update → `PUT /events/{id}`
   - Publish toggle calls the update endpoint with `is_published: true`
3. Create `frontend/src/pages/admin/AttendeeList.jsx`:
   - Calls `GET /admin/events/{id}/attendees`
   - Table with columns: name, profession, email, status pill, badge link (if checked_in)
4. Create `frontend/src/pages/admin/ScanPage.jsx`:
   - Uses `@zxing/library BrowserQRCodeReader` to stream camera into a `<video>` element
   - Fallback: text input to paste a QR code ID manually (for testing without camera)
   - On decode: calls `POST /checkin` with `{qr_code_id}`
   - Response handling:
     - `already_checked_in: true` → show amber "Already checked in" banner
     - Otherwise: add scanned attendee to a local list with status "Pending…"
   - Start polling `GET /attendees/{id}/status` every 3s for each pending item in the list
   - When status → `checked_in`: update list item to green "Checked In ✓" + show badge link
   - Multiple attendees can appear in the list simultaneously (out-of-order completions work naturally)

### Relevant Context
- `@zxing/library` scanning requires `https://` or `localhost` for camera access.
- Keep scanned results in local component state as an array: `[{attendee_id, name, status, badge_url}]`.
- The "Already checked in" check on the backend covers concurrent scans — the frontend just shows
  whatever the API returns.
- Admin routes are protected with `<RequireAuth role="admin">` — a customer token gets redirected.

### Status
[ ] pending

---

## Phase 8 — Polish, Seed Data & Final Integration

### Intent
Wire together all remaining loose ends: loading states, toast notifications, responsive design,
page transitions, the event countdown, and the seed script. Verify the full demo loop end-to-end.

### Expected Outcomes
- Every network action has a loading spinner and a toast on success/failure
- All pages are responsive (mobile → desktop)
- Seed script runs cleanly against TiDB and populates demo data
- Full demo loop works: publish event → register → receive email → view QR → admin scan →
  pending → checked_in → badge viewable on both sides → re-scan shows "Already checked in"

### Todo List
1. Audit every form/button for loading state (`isLoading` flag → spinner + disabled button).
2. Ensure `react-hot-toast` `<Toaster>` is in `App.jsx` and all API calls fire toasts on error.
3. Add subtle page-entry animation: `opacity-0 → opacity-100` via Tailwind `animate-fadeIn` on page mount.
4. Verify event countdown displays correctly on EventCard and Dashboard cards.
5. Test duplicate-scan scenario manually: scan → while pending, scan again → confirm "Already checked in"
   is returned and no second job is created.
6. Finalize `backend/seed.py` to be idempotent (upsert/skip if records already exist).
7. Add `frontend/.env.example` with `VITE_API_URL=http://localhost:8000`.
8. Write a root-level `README.md` with setup instructions:
   - Backend: create venv, `pip install -r requirements.txt`, copy `.env`, run `seed.py`, `uvicorn`
   - Frontend: `npm install`, copy `.env`, `npm run dev`
   - Demo credentials: admin / customer
9. Smoke-test: start both servers, run the full loop, confirm badge PDF is downloadable and printable.

### Relevant Context
- The demo loop is the acceptance criterion — every phase feeds into it.
- Keep the `README.md` concise and focused on running the app locally.

### Status
[ ] pending

---

## Implementation Order

```
Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6 → Phase 7 → Phase 8
```

Each phase is designed to be independently reviewable before the next begins.
