# Plantation Yield Automation — Upgraded

This upgraded project keeps your existing monthly Excel input style and rebuilds the app into two pages:

- `/` — public main dashboard
- `/admin` — admin data input and report generation page

## What changed

- Removed OTP + email login
- Added backend username/password admin login
- Built a modern, pastel, responsive Next.js UI
- Preserved flexible Excel input normalization
- Added public dashboard filters for plantation, region, estate, division, year, metric, operator, value, ranking, and benchmark
- Added estate summary and region summary cards
- Added chart and map actions on answer rows
- Added monthly dataset persistence after admin upload
- Added clean report generation workflow from the admin page

## Default admin credentials

These are stored in `backend/.env` and can be changed:

- Username: `datainput`
- Password: `data123`

## Backend

```bash
cd backend
python -m venv .venv
# activate the venv
pip install -r requirements.txt
cp .env.example .env
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Frontend

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

## Notes

- Upload the regional Excel files from the admin page each month.
- The public dashboard becomes active after admin upload.
- Generated Excel, PDF, ZIP, and preview images are available from the admin page and the backend `/outputs` folder.
- The backend stores the active monthly dataset in `backend/data_store`.


## External login portal support

This build was updated to work behind a **separate first login page**.

### Flow
1. User logs in from the central portal.
2. Portal opens this project with `?username=THE_USER`.
3. Frontend sends `X-Auth-User` on dashboard requests.
4. Backend reads `backend/data/user_estate_access.json` and scopes the visible plantations / estates.

### Plantation visibility rules in this build
- Estate users: only their mapped plantation / estate
- CEO (TTEL / KVPL / HPL): all estates inside only their mapped plantation
- MD: all plantations
- Admin: all plantations

### Important
For production, point both projects to the **same shared access file** so user mappings stay in sync.

Example:
- Estate Worker uses `USER_ACCESS_FILE=/srv/shared-auth/user_estate_access.json`
- Plantation uses `access_file_path=/srv/shared-auth/user_estate_access.json`

### Direct access
If a user opens this project directly without the portal, the dashboard will refuse access.
