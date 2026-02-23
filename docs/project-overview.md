# Project Overview

## Technology Stack

| Component | Technology |
|-----------|------------|
| Backend Framework | FastAPI 0.109.0 |
| ORM | SQLAlchemy 2.0.25 |
| Database | SQLite |
| Authentication | JWT (python-jose) + bcrypt |
| Frontend | Alpine.js 3.x + Bulma CSS + Tailwind CSS |
| Server (Dev) | Uvicorn |
| Server (Prod) | Waitress |

## Core Features

### 1. Physical Inventory Management
- Complete book catalog with detailed metadata
- Storage location tracking using rack-shelf system (format: `TIC-R-{rack}-S-{shelf}`)
- ISBN, author, title, publisher information
- Language and subject categorization

### 2. Circulation Management
- **Issue**: Borrow books to users with configurable due dates (default: 14 days)
- **Return**: Process book returns and update availability
- **Extend**: Extend book loans by 7 days (maximum 2 extensions per transaction)
- **Overdue Tracking**: Automatic status update for overdue books

### 3. Digital Library
- PDF, EPUB, MOBI file support
- In-browser PDF viewing
- Download tracking with view/download counts
- Optional linking to physical books
- Public browsing without authentication

### 4. Magazine Management
- Magazine master records with language and frequency
- Issue tracking (received copies)
- Vendor management
- Public magazine browsing

### 5. User Management
- Three-tier Role-Based Access Control (RBAC)
- Password reset with admin-generated tokens
- Password history to prevent reuse
- Password strength validation

### 6. Dashboard & Analytics
- Real-time statistics (total books, issued, overdue)
- Subject distribution charts
- Digital library statistics

## Architecture Overview

```
TIC Nexus/
├── app/                    # Backend application
│   ├── main.py            # FastAPI app, web routes, exception handlers
│   ├── models.py          # SQLAlchemy models (8 tables)
│   ├── schemas.py         # Pydantic schemas for validation
│   ├── database.py        # DB connection, session management
│   ├── auth.py            # JWT auth, password hashing, dependencies
│   ├── routes.py          # Book & circulation API endpoints
│   ├── digital_library_routes.py  # Digital library API
│   ├── magazine_routes.py        # Magazine API
│   ├── password_reset.py         # Password reset logic
│   ├── circulation.py            # Business logic for issue/return/extend
│   └── password_utils.py         # Password validation utilities
├── templates/             # Jinja2 HTML templates
│   ├── base.html         # Base template
│   ├── sidebar.html      # Navigation
│   ├── dashboard.html   # Dashboard page
│   ├── inventory.html   # Book CRUD
│   ├── circulation.html # Issue/Return/Extend
│   └── ...               # Other pages
├── static/               # CSS, JS, uploads
├── library_vault/        # Digital book storage
├── data/                 # SQLite database
├── docs/                 # Documentation
└── scripts/             # Utility scripts
```

## Design Philosophy

### RESTful API
- Clear separation between API and web routes
- API routes prefixed with `/api/`
- Web routes serve HTML templates

### Client-Side Authentication
- JWT token stored in localStorage
- Token validated on every API call
- Role-based UI hiding (not security - backend enforces permissions)

### Role-Based Access Control

| Feature | Admin | Librarian | Viewer |
|---------|-------|------------|--------|
| View Dashboard | Yes | Yes | Yes |
| View Books | Yes | Yes | Yes |
| Add Books | Yes | Yes | No |
| Edit Books | Yes | Yes | No |
| Delete Books | Yes | No | No |
| Issue Books | Yes | Yes | No |
| Return Books | Yes | Yes | No |
| Extend Books | Yes | Yes | No |
| View Transactions | Yes | Yes | Yes |
| Manage Digital Library | Yes | Yes | No |
| Manage Magazines | Yes | Yes | No |
| Manage Users | Yes | No | No |
| Change Password | Yes | Yes | Yes |

## Database Tables

1. **User** - Authentication and RBAC
2. **Book** - Physical inventory
3. **Transaction** - Circulation records
4. **DigitalBook** - Digital library resources
5. **BookDigitalLink** - Many-to-many: physical ↔ digital
6. **PasswordResetToken** - Password reset tokens
7. **PasswordHistory** - Prevent password reuse
8. **Vendor** - Magazine suppliers
9. **Magazine** - Magazine titles
10. **MagazineIssue** - Received magazine copies
