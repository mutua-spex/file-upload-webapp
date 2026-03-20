# ChatApp (Python Backend + Kivy Mobile Client)

This workspace contains a **Python FastAPI backend** and a **Python Kivy mobile client** prototype.

## Folder structure

- `backend/` - FastAPI server (real-time chat via WebSockets, authentication, rooms, message history, file uploads)
- `mobile/` - Kivy-based client app (login, room list, chat, file attachment)

---

## ✅ Backend (FastAPI)

### Setup

1. Create a virtual environment and activate it:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

### Run

```powershell
uvicorn main:app --reload
```

The server will start at `http://127.0.0.1:8000`.

### Key endpoints

- `POST /api/auth/register` – Register a new user
- `POST /api/auth/token` – Login and get an access + refresh token pair
- `POST /api/auth/refresh` – Rotate refresh token and get a new access token
- `GET /api/rooms` – List rooms
- `POST /api/rooms` – Create room
- `GET /api/rooms/{room_id}/messages` – Get recent messages
- `GET /api/rooms/{room_id}/presence` – Show users currently in the room
- `POST /api/upload` – Upload file (requires auth)
- `ws://.../ws/{room_id}?token=...` – WebSocket chat

### Environment variables (optional)

- `CHATAPP_SECRET_KEY` – Secret used to sign JWT tokens (change in production)
- `CHATAPP_ACCESS_TOKEN_EXPIRE_MINUTES` – TTL for access tokens (default: 10080)
- `CHATAPP_REFRESH_TOKEN_EXPIRE_DAYS` – TTL for refresh tokens (default: 30)

---

## ✅ Mobile client (Kivy)

### Setup

1. Create a virtual environment and activate it:

```powershell
cd mobile
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

### Run

```powershell
python main.py
```

### Notes

- The mobile client defaults to talking to `http://127.0.0.1:8000`.
- You can change the backend URL by setting the `CHAT_BACKEND_URL` environment variable.

---

## 🚀 Deploying the backend (production)

1. **Set environment variables** (required):
   - `CHATAPP_SECRET_KEY` (strong random secret)
   - `CHATAPP_ACCESS_TOKEN_EXPIRE_MINUTES` (optional, default 10080)
   - `CHATAPP_REFRESH_TOKEN_EXPIRE_DAYS` (optional, default 30)

2. **Install dependencies** (on your server):

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

3. **Run with a production server** (example using uvicorn):

```powershell
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4
```

> For real production, run behind a reverse proxy (NGINX) and/or use a process manager (systemd, supervisor).

### Docker (optional)

If you prefer container deployment, create a `Dockerfile` and build an image to run the backend in a container.

---

## 📱 Deploying the mobile client

The mobile client currently runs as a Python/Kivy app. For production you can:

- **Run on desktop** (Windows/macOS/Linux):
  - Package with `PyInstaller` or `briefcase`.
- **Build for Android**: Use `buildozer` (Linux) or `p4a` with Kivy.

You can also run the client directly during development with:

```powershell
cd mobile
python main.py
```

---

## ✅ Next enhancements (optional)

- Add push notifications (platform-specific)
- Improve UI/UX and message rendering
- Add room membership and user presence tracking
- Add message pagination
- Harden authentication (refresh tokens, better secret management)
