# GEMINI.md - TIC Nexus Context

## 🎯 Project Overview
**TIC Nexus** is a Technical Information Center Management System developed for Bharat Electronics Limited (BEL). It is a full-stack web application designed to manage physical book inventory, digital library resources, and library circulation operations (issue, return, extension).

### Core Technologies
- **Backend:** FastAPI (Python 3.11+)
- **Database:** SQLAlchemy 2.0 with SQLite
- **Authentication:** JWT (python-jose) + bcrypt hashing
- **Frontend:** Jinja2 Templates, Alpine.js (reactivity), Bulma CSS (UI), Tailwind CSS (utilities)
- **Deployment:** Uvicorn (dev) / Waitress (production)

---

## 🏗️ Architecture & Structure
The project follows a modular FastAPI structure:

- `app/`: Core application logic
    - `main.py`: Entry point, app initialization, and web routes.
    - `models.py`: SQLAlchemy models (Users, Books, Transactions, DigitalBooks, Magazines, Vendors).
    - `schemas.py`: Pydantic schemas for data validation and API response models.
    - `routes.py`: API endpoints for books and circulation.
    - `digital_library_routes.py`: API endpoints for digital resource management.
    - `magazine_routes.py`: API endpoints for magazine management.
    - `auth.py`: JWT authentication, role-based access control (RBAC), and password hashing.
    - `circulation.py`: Business logic for library operations.
    - `database.py`: Session management and engine configuration.
- `templates/`: HTML templates using Jinja2 and Alpine.js.
- `static/`: Frontend assets (CSS, JS, images).
- `scripts/`: Utility scripts for setup, testing, and administration.
- `data/`: Contains the SQLite database (`tic_nexus.db`).
- `library_vault/`: Storage for uploaded digital resources (PDFs).

---

## 🚀 Building and Running

### Development
1. **Environment Setup:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. **Download Assets:**
   ```powershell
   python scripts/download_assets.py
   ```
3. **Run Application:**
   ```powershell
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Production (Windows)
Execute the batch script:
```powershell
.\run_nexus.bat
```

### Testing
Run the application test suite:
```powershell
python scripts/test_application.py
```

---

## 🛠️ Development Conventions

### Coding Standards
- **Python:** PEP 8 compliance, mandatory type hints, and docstrings for all functions/classes.
- **Frontend:** Use Alpine.js for client-side reactivity. Initialize data in `init()` and use `window.toast` for user notifications.
- **Database:** Always use SQLAlchemy ORM for queries. Parameterized queries are mandatory to prevent SQL injection.
- **Naming:** `snake_case` for variables/functions, `PascalCase` for classes, `UPPER_SNAKE_CASE` for constants.

### Role-Based Access Control (RBAC)
- **Admin:** Full system access, user management, and deletion rights.
- **Librarian:** Circulation operations, adding/editing books (physical & digital).
- **Viewer:** Read-only access to catalogs and history.
*Security Note: Permissions MUST be enforced on the backend via FastAPI dependencies (`get_current_admin_user`, etc.).*

### Data Formats
- **Storage Location:** `TIC-R-{rack}-S-{shelf}` (e.g., `TIC-R-1-S-5`).
- **Physical Books:** Tracked via unique Accession Numbers (`acc_no`).
- **Digital Books:** PDFs only, max 50MB.

---

## 🔐 Security & Safety
- **Secrets:** `SECRET_KEY` in `app/auth.py` must be updated for production.
- **Passwords:** Never store plain text; always use `bcrypt` via `auth.py` utilities.
- **Validation:** Use Pydantic schemas in `app/schemas.py` for all incoming API data.

---

## 📖 Key Reference Files
- `AGENTS.md`: Detailed technical guide for AI agents and token optimization.
- `README.md`: High-level project overview.
- `SETUP_GUIDE.md`: Detailed environment configuration.
- `app/models.py`: Source of truth for database schema.
