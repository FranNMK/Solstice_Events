# Solstice Events

A full-stack event registration and check-in platform built with **FastAPI + TiDB + React**.

Customers browse events, register, receive QR-code email confirmations, and download personalised PDF badges after check-in. Admins publish events, view attendee lists, and scan QR codes at the door — with badge generation happening asynchronously via a background worker + internal webhook.

---

## Tech Stack

| Layer | Choice |
|---|---|
| Backend | Python 3.11 · FastAPI · Uvicorn |
| Database | TiDB Cloud (MySQL-compatible) via SQLAlchemy async (`aiomysql`) |
| Frontend | React 18 · Vite · Tailwind CSS v4 |
| Auth | JWT (python-jose) — roles: `customer` / `admin` |
| Email | Resend Python SDK (logs to console if key not set) |
| QR codes | `qrcode[pil]` — server-side PNG generation |
| PDF badges | `reportlab` — async background worker pipeline |

---

## Project Structure

```
solstice-events-plan.md
backend/
  app/
    main.py             ← FastAPI app, CORS, static mount, worker startup
    config.py           ← env var settings
    database.py         ← SQLAlchemy async engine + session
    models.py           ← User, Event, Attendee, BadgeJob ORM models
    schemas.py          ← Pydantic v2 request/response schemas
    auth/
      router.py         ← POST /auth/register, POST /auth/login
      utils.py          ← JWT encode/decode, password hashing, auth deps
    routes/
      events.py         ← GET/POST/PUT /events, /admin/events
      attendees.py      ← POST /attendees/register, GET /attendees/my, status, badge
      checkin.py        ← POST /checkin (admin, enqueues badge job)
      webhooks.py       ← POST /webhooks/badge-complete (HMAC-signed)
    services/
      qr.py             ← QR PNG generation
      email.py          ← Resend confirmation email
      badge.py          ← ReportLab PDF badge generation
      worker.py         ← Background thread polls queued jobs → generates badge → calls webhook
    static/
      qrcodes/          ← generated QR PNGs
      badges/           ← generated badge PDFs
  seed.py               ← idempotent demo data seeder
  requirements.txt
  .env.example
frontend/
  src/
    App.jsx             ← router, route guards (RequireAuth)
    context/
      AuthContext.jsx   ← JWT storage, login/logout, decoded user
    hooks/
      useAuth.js        ← convenience re-export
      usePolling.js     ← interval polling while condition is true
    api/
      index.js          ← axios instance + auth interceptor
      auth.js · events.js · attendees.js
    components/
      Navbar.jsx · EventCard.jsx · StatusPill.jsx · Spinner.jsx
    pages/
      Landing.jsx       ← hero + event carousel
      Events.jsx        ← public event grid
      Login.jsx         ← JWT login form
      SignUp.jsx        ← customer registration form
      Register.jsx      ← event-specific registration form
      Dashboard.jsx     ← customer registrations, QR codes, badge download + polling
      admin/
        AdminDashboard.jsx  ← event list, publish toggle, stats
        EventForm.jsx       ← create / edit event form
        AttendeeList.jsx    ← per-event attendee table
        ScanPage.jsx        ← camera QR scanner + manual entry + live status polling
  .env.example
```

---

## Local Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- A TiDB Cloud cluster (free tier works) — get the connection string from the TiDB console

---

### 1 — Backend

```bash
# 1. Enter the backend directory and create a virtual environment
cd backend
python -m venv venv

# 2. Activate the venv
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# macOS / Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
copy .env.example .env        # Windows
# cp .env.example .env         # macOS/Linux
```

Edit `backend/.env` and fill in your values:

```env
TIDB_URL=mysql+aiomysql://user:password@host:4000/solstice_events?ssl_ca=/etc/ssl/certs/ca-certificates.crt
JWT_SECRET=change_me_to_a_long_random_string
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
RESEND_API_KEY=re_...          # optional — emails log to console if omitted
RESEND_FROM=onboarding@resend.dev
WEBHOOK_SECRET=some_random_secret
BADGE_BASE_URL=http://localhost:8000
```

```bash
# 5. Seed the database (creates tables + demo users + 3 events)
python seed.py

# 6. Start the API server
uvicorn app.main:app --reload --port 8000
```

API is now running at **http://localhost:8000**  
Interactive docs: **http://localhost:8000/docs**

---

### 2 — Frontend

```bash
# 1. Enter the frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Configure environment
copy .env.example .env        # Windows
# cp .env.example .env         # macOS/Linux
# .env should contain: VITE_API_URL=http://localhost:8000

# 4. Start the dev server
npm run dev
```

Frontend is now running at **http://localhost:5173**

---

## Demo Credentials

| Role | Email | Password |
|---|---|---|
| Admin | `admin@solstice.dev` | `admin123` |
| Customer | `demo@solstice.dev` | `demo123` |

---

## Demo Flow (end-to-end)

1. **Browse** — open http://localhost:5173, see 3 seeded events on the landing page
2. **Register** — log in as the demo customer, click any event → "Register", fill in name + profession
3. **Email** — check the console (or inbox if Resend is configured) for the confirmation email
4. **QR code** — go to `/dashboard`, click "View QR Code" on the registration card
5. **Admin scan** — log in as admin in another tab → `/admin/scan`
   - Click "Start Camera" and scan the QR, **or** paste the QR code ID into the manual input
6. **Pending** — both the admin scan page and the customer dashboard show "Pending…" with a spinner
7. **Badge ready** (~3–5 s) — status auto-updates to "Checked In ✓"; "Download Badge" appears on both sides
8. **Duplicate scan** — scan the same QR again → "Already checked in" amber banner
9. **PDF badge** — click "Download Badge" to get the PDF; "Print Badge" opens it in a new tab

---

## Key Architecture Notes

### Async Badge Pipeline
Check-in does **not** block on PDF generation:

```
POST /checkin
  → attendee.status = "pending"
  → BadgeJob(status="queued") inserted
  → returns immediately

BadgeWorker (daemon thread, polls every 2 s)
  → picks up queued job
  → generates PDF via reportlab
  → POSTs to /webhooks/badge-complete with HMAC-SHA256 signature
  → job.status = "completed"

POST /webhooks/badge-complete
  → validates HMAC signature
  → attendee.status = "checked_in"
  → attendee.badge_pdf_url = "/static/badges/{id}.pdf"

Frontend polls GET /attendees/{id}/status every 3 s
  → detects status change
  → updates UI without page refresh
```

### Route Protection
- `RequireAuth role="customer"` → redirects unauthenticated users to `/login`
- `RequireAuth role="admin"` → redirects non-admins to `/unauthorized`
- Backend `require_role("admin")` dependency → returns HTTP 403 on role mismatch

---

## Available Scripts

| Command | What it does |
|---|---|
| `uvicorn app.main:app --reload` | Start backend dev server (run from `backend/`) |
| `python seed.py` | Seed demo data into TiDB (run from `backend/`) |
| `npm run dev` | Start frontend dev server (run from `frontend/`) |
| `npm run build` | Production build (run from `frontend/`) |
