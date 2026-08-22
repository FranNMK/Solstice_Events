# Solstice Events

> **Where Moments Become Memories**

A production-grade, full-stack event registration and check-in platform. Customers browse events, register, receive QR-code confirmation emails, and download personalised PDF badges after check-in. Admins publish and manage events, view live attendee lists, and scan QR codes at the door — with badge generation running asynchronously through a background worker pipeline.

---

## 🌐 Live Deployment

| Service | URL |
|---|---|
| **Frontend** | https://solstice-events.onrender.com |
| **Backend API** | https://solstice-events-api.onrender.com |
| **API Docs (Swagger)** | https://solstice-events-api.onrender.com/docs |

> **Note — Render free tier spin-down:** The backend sleeps after 15 minutes of inactivity. The first request after sleep takes ~30 seconds to wake up. Subsequent requests are instant.

---

## 🔑 Demo Credentials

| Role | Email | Password | Access |
|---|---|---|---|
| **Admin** | `admin@solstice.dev` | `admin123` | Full event management, QR scanner, attendee lists |
| **Customer** | `demo@solstice.dev` | `demo123` | Browse events, register, view QR, download badge |

---

## ✨ Features

### Customer
- Browse published events with countdown pills and location details
- Create an account or sign in — JWT-based auth, role-aware redirects
- Register for any event — name + profession saved to your badge
- Receive a confirmation email with event details (sent from `noreply@test.kigumotvc.ac.ke`)
- View your QR code on the dashboard — present it at the door
- Live status polling — dashboard auto-updates from `Registered → Pending → Checked In ✓` without page refresh
- Download or print your personalised PDF badge once checked in
- Unregister from an event (only while status is `registered`)

### Admin
- Create, edit, publish/unpublish, and delete events
- Delete is blocked if any attendees have registered (data safety guard)
- View per-event attendee table with live status pills and badge download links
- QR scanner page — camera-based scanning (with permission prompt) or manual paste fallback
- Real-time check-in: scan → `Pending…` spinner → `Checked In ✓` + badge link — all without refresh
- Duplicate scan protection: re-scanning shows an amber "Already checked in" banner

---

## 🏗️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.11 · FastAPI · Uvicorn |
| **Database** | TiDB Cloud (MySQL-compatible, SSL) · SQLAlchemy async (`aiomysql`) |
| **Frontend** | React 18 · Vite · Tailwind CSS v4 |
| **Auth** | JWT (`python-jose`) — roles: `customer` / `admin` |
| **Email** | Resend SDK · verified domain `test.kigumotvc.ac.ke` |
| **QR Codes** | `qrcode[pil]` — server-side PNG, in-memory generation |
| **PDF Badges** | `reportlab` — A6 card-style PDF, async pipeline |
| **File Storage** | Cloudinary CDN — QR PNGs + badge PDFs (persistent across deploys) |
| **Hosting** | Render — FastAPI web service + React static site |

---

## 🗂️ Project Structure

```
Solstice_Events/
├── render.yaml                   ← Render infrastructure-as-code (both services)
├── README.md
├── solstice-events-plan.md       ← Phase-by-phase build plan (all 8 phases complete)
│
├── backend/
│   ├── requirements.txt
│   ├── .env.example              ← all env vars documented
│   ├── seed.py                   ← idempotent demo data seeder
│   └── app/
│       ├── main.py               ← FastAPI app, CORS, static mount, worker thread startup
│       ├── config.py             ← all settings read from environment variables
│       ├── database.py           ← async engine (aiomysql) + sync engine (pymysql for worker)
│       ├── models.py             ← User, Event, Attendee, BadgeJob ORM models
│       ├── schemas.py            ← Pydantic v2 request/response schemas
│       ├── auth/
│       │   ├── router.py         ← POST /auth/register · POST /auth/login
│       │   └── utils.py          ← JWT encode/decode, password hashing, require_role()
│       ├── routes/
│       │   ├── events.py         ← CRUD /events + /admin/events (delete blocked if attendees exist)
│       │   ├── attendees.py      ← register, my, status poll, badge download/redirect, unregister
│       │   ├── checkin.py        ← POST /checkin — enqueues badge job, duplicate-scan guard
│       │   └── webhooks.py       ← POST /webhooks/badge-complete — HMAC-SHA256 validated
│       └── services/
│           ├── cloudinary_storage.py  ← upload_image() + upload_pdf() → Cloudinary CDN
│           ├── qr.py             ← generate PNG in memory → upload to Cloudinary → CDN URL
│           ├── badge.py          ← generate PDF to tempfile → upload to Cloudinary → CDN URL
│           ├── email.py          ← Resend HTML confirmation email (RESEND_TEST_TO override)
│           └── worker.py         ← daemon thread: polls queued jobs → badge → signed webhook
│
└── frontend/
    ├── index.html                ← favicon = logo.png · title = "Solstice Events — Where Moments Become Memories"
    ├── vite.config.js
    ├── .env.example              ← VITE_API_URL
    └── src/
        ├── App.jsx               ← BrowserRouter, RequireAuth guards, Toaster
        ├── main.jsx
        ├── index.css             ← Tailwind v4 + animate-fade-in keyframe
        ├── context/
        │   └── AuthContext.jsx   ← token in localStorage, login/logout, decodeToken()
        ├── hooks/
        │   ├── useAuth.js        ← re-export from AuthContext
        │   └── usePolling.js     ← setInterval while condition=true, auto-clears on unmount
        ├── api/
        │   ├── index.js          ← axios + Bearer interceptor + 401 redirect
        │   ├── auth.js           ← login · register
        │   ├── events.js         ← getEvents · getAdminEvents · create · update · delete
        │   └── attendees.js      ← register · my · status · badgeUrl · checkIn · unregister
        ├── components/
        │   ├── Navbar.jsx        ← logo, role-aware nav links, logout
        │   ├── EventCard.jsx     ← image, countdown pill, date, location, Register button
        │   ├── StatusPill.jsx    ← registered=gray · pending=amber · checked_in=green
        │   └── Spinner.jsx       ← animated SVG spinner (sm / md / lg)
        └── pages/
            ├── Landing.jsx       ← hero section + event carousel + feature highlights
            ├── Events.jsx        ← published events grid
            ├── Login.jsx         ← email + password (show/hide toggle)
            ├── SignUp.jsx        ← email + password × 2 (show/hide toggles)
            ├── Register.jsx      ← event-specific registration (auth-gated)
            ├── Dashboard.jsx     ← registrations, QR toggle, badge download, live polling, unregister
            └── admin/
                ├── AdminDashboard.jsx  ← event list, stats, publish toggle, delete with confirm modal
                ├── EventForm.jsx       ← create/edit with image preview + publish checkbox
                ├── AttendeeList.jsx    ← per-event table with stats + badge download links
                └── ScanPage.jsx        ← camera scanner (@zxing) + manual fallback + live polling
```

---

## 🔄 How It Works — End-to-End Flow

### 1. Customer registers for an event
```
Customer fills form → POST /attendees/register
  → Attendee row created (status: registered)
  → QR PNG generated in memory → uploaded to Cloudinary
  → Confirmation email sent via Resend (from noreply@test.kigumotvc.ac.ke)
  → Returns attendee record with qr_code_id
```

### 2. Admin scans the QR code at the door
```
Admin scans QR (camera or manual paste) → POST /checkin
  → Duplicate check: if status=pending/checked_in → return already_checked_in:true
  → Otherwise: attendee.status = "pending"
  → BadgeJob(status="queued") inserted
  → Returns immediately (non-blocking)
```

### 3. Async badge generation pipeline
```
BadgeWorker daemon thread (polls every 2 s)
  → Finds queued BadgeJob
  → Marks job status = "processing"
  → Sleeps 3–5 s (simulates badge printer)
  → Generates A6 PDF badge via reportlab (with QR embedded)
  → Uploads PDF to Cloudinary → gets CDN URL
  → Deletes local temp file
  → Builds webhook payload {job_id, attendee_id, badge_pdf_url, timestamp}
  → Signs with HMAC-SHA256(WEBHOOK_SECRET)
  → POST /webhooks/badge-complete with X-Signature header
  → Marks job status = "completed"

POST /webhooks/badge-complete
  → Validates HMAC signature (401 if invalid)
  → Sets attendee.status = "checked_in"
  → Sets attendee.badge_pdf_url = Cloudinary CDN URL
```

### 4. Frontend reflects status in real time
```
Customer dashboard / Admin scan page
  → usePolling(getAttendeeStatus, 3000ms, status==="pending")
  → Status changes to "checked_in" → polling stops
  → Toast fires: "Checked In ✓ — badge ready"
  → "Download Badge" button appears → 302 redirect to Cloudinary CDN PDF
```

---

## ☁️ Infrastructure & Storage

### Render (hosting)
| Service | Type | Plan |
|---|---|---|
| `solstice-events-api` | Web Service (Python) | Free |
| `solstice-events` | Static Site | Free |

Both services auto-deploy on every push to `main`.

### TiDB Cloud (database)
MySQL-compatible serverless database. Four tables:
- `users` — UUID pk, email, hashed_password, role
- `events` — UUID pk, title, description, date, location, image_url, is_published
- `attendees` — UUID pk, user_id FK, event_id FK, name, profession, qr_code_id, status, badge_pdf_url
- `badge_jobs` — UUID pk, attendee_id FK, status (queued/processing/completed), timestamps

### Cloudinary (file storage)
All generated files are uploaded to Cloudinary so they survive Render restarts:
- QR codes → `solstice/qrcodes/{qr_code_id}` (PNG, `image` resource type)
- Badges → `solstice/badges/{attendee_id}` (PDF, `raw` resource type)

The `GET /attendees/{id}/badge` endpoint issues a **302 redirect** to the Cloudinary CDN URL — no file serving overhead on the API server.

### Resend (email)
Sending domain: `test.kigumotvc.ac.ke` (verified)
From address: `noreply@test.kigumotvc.ac.ke`
Delivers to any recipient worldwide.

---

## 🚀 Local Development Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- TiDB Cloud cluster (free tier — get connection string from the TiDB console)
- Cloudinary account (free tier — for file storage)
- Resend account + verified domain (optional — emails log to console if key not set)

---

### 1 — Backend

```bash
# Clone and enter the project
git clone https://github.com/FranNMK/Solstice_Events.git
cd Solstice_Events/backend

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1      # Windows PowerShell
# source venv/bin/activate        # macOS / Linux

# Install dependencies
pip install -r requirements.txt

# Copy and fill in environment variables
copy .env.example .env           # Windows
# cp .env.example .env            # macOS / Linux
```

Edit `backend/.env`:

```env
TIDB_URL=mysql+aiomysql://user:password@host:4000/solstice_events
JWT_SECRET=any-long-random-string
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
RESEND_API_KEY=re_xxxxxxxxxxxx
RESEND_FROM=noreply@test.kigumotvc.ac.ke
RESEND_TEST_TO=                            # leave empty — domain is verified
WEBHOOK_SECRET=another-random-string
BADGE_BASE_URL=http://localhost:8000
ALLOWED_ORIGINS=http://localhost:5173
CLOUDINARY_URL=cloudinary://api_key:api_secret@cloud_name
```

```bash
# Create tables and seed demo data
python seed.py

# Start the API server
uvicorn app.main:app --reload --port 8000
```

API → **http://localhost:8000**  
Swagger docs → **http://localhost:8000/docs**

---

### 2 — Frontend

```bash
cd ../frontend

# Install dependencies
npm install

# Copy environment file
copy .env.example .env           # Windows
# cp .env.example .env            # macOS / Linux
# File contains: VITE_API_URL=http://localhost:8000

# Start dev server
npm run dev
```

Frontend → **http://localhost:5173**

---

## 🧪 Testing the Full Flow Locally

Once both servers are running:

1. **Open** http://localhost:5173 — landing page with 3 seeded events
2. **Sign up** as a new customer at `/register` (or use `demo@solstice.dev` / `demo123`)
3. **Browse events** → click **Register** on any event → fill in name and profession
4. **Check your inbox** — confirmation email from `noreply@test.kigumotvc.ac.ke`
5. **Dashboard** (`/dashboard`) → click **View QR Code** on your registration card
6. **Open a new tab**, log in as `admin@solstice.dev` / `admin123`
7. **Go to** `/admin/scan` → click **Start Camera** (allow permission) OR paste the QR code ID manually
8. **Scan / submit** — both tabs immediately show **Pending…** with a spinner
9. **Wait ~3–5 seconds** — status auto-updates to **Checked In ✓** on both tabs simultaneously (no refresh)
10. **Click Download Badge** → PDF opens from Cloudinary CDN
11. **Scan the same QR again** → amber **"Already checked in"** banner appears — no duplicate job created

---

## 📡 API Reference

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/auth/register` | — | Create account, returns JWT |
| `POST` | `/auth/login` | — | Login, returns JWT |
| `GET` | `/events` | — | List published events |
| `GET` | `/events/{id}` | — | Single event detail |
| `GET` | `/admin/events` | Admin | All events incl. drafts |
| `POST` | `/admin/events` | Admin | Create event |
| `PUT` | `/admin/events/{id}` | Admin | Update / publish event |
| `DELETE` | `/admin/events/{id}` | Admin | Delete event (blocked if attendees exist) |
| `GET` | `/admin/events/{id}/attendees` | Admin | List attendees for event |
| `POST` | `/attendees/register` | Customer | Register for event |
| `GET` | `/attendees/my` | Customer | My registrations (with event details) |
| `GET` | `/attendees/{id}/status` | Auth | Status poll for badge pipeline |
| `GET` | `/attendees/{id}/badge` | Auth | 302 redirect to Cloudinary PDF |
| `DELETE` | `/attendees/{id}` | Customer | Unregister (blocked if pending/checked_in) |
| `POST` | `/checkin` | Admin | Scan QR → enqueue badge job |
| `POST` | `/webhooks/badge-complete` | HMAC | Worker callback → set checked_in |

---

## 🛠️ Available Scripts

| Command | Directory | Description |
|---|---|---|
| `uvicorn app.main:app --reload --port 8000` | `backend/` | Start backend dev server with hot-reload |
| `python seed.py` | `backend/` | Seed TiDB with demo users + 3 events (idempotent) |
| `npm run dev` | `frontend/` | Start Vite dev server |
| `npm run build` | `frontend/` | Production build → `dist/` |

---

## 🔐 Environment Variables Reference

### Backend (`backend/.env`)

| Variable | Required | Description |
|---|---|---|
| `TIDB_URL` | ✅ | SQLAlchemy async connection string for TiDB Cloud |
| `JWT_SECRET` | ✅ | Secret key for signing JWTs — use a long random string |
| `JWT_ALGORITHM` | ✅ | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | ✅ | Token lifetime in minutes (default `60`) |
| `RESEND_API_KEY` | ⚠️ | Resend API key — emails log to console if omitted |
| `RESEND_FROM` | ⚠️ | Sender address — must match a verified Resend domain |
| `RESEND_TEST_TO` | — | Override: redirect all emails to this address (free-tier workaround) |
| `WEBHOOK_SECRET` | ✅ | HMAC-SHA256 secret shared between worker and webhook endpoint |
| `BADGE_BASE_URL` | ✅ | Backend public URL — used by worker to call the webhook |
| `ALLOWED_ORIGINS` | ✅ | Comma-separated CORS origins (frontend URL) |
| `CLOUDINARY_URL` | ⚠️ | `cloudinary://key:secret@cloud_name` — files stored locally if omitted |

### Frontend (`frontend/.env`)

| Variable | Required | Description |
|---|---|---|
| `VITE_API_URL` | ✅ | Full backend URL, e.g. `http://localhost:8000` or the Render URL |
