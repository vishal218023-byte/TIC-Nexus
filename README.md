# TIC Nexus - Technical Information Center Management System

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)]()

> **Modern Library Management System for Bharat Electronics Limited**  
> A comprehensive web-based solution for managing physical and digital library resources with role-based access control.

---

## 🎯 Overview

**TIC Nexus** is a feature-rich library management system designed specifically for the Technical Information Center at Bharat Electronics Limited. It provides a modern, intuitive interface for managing physical book inventory, digital resources, circulation operations, and user management with three-tier role-based access control.

### 🌟 Key Features

#### 📚 **Physical Inventory Management**
- Complete book catalog with detailed metadata (Author, Title, Publisher, ISBN, Subject, Year)
- Unique accession number tracking
- Storage location mapping (Rack & Shelf system: `TLC-R-{rack}-S-{shelf}`)
- Real-time availability status
- Advanced search and filtering capabilities

#### 🔄 **Circulation Management**
- Issue books to registered users with due date tracking
- Return processing with condition notes
- Book extension system (up to 2 extensions, 7 days each)
- Automatic overdue detection and status updates
- Comprehensive transaction history

#### 💾 **Digital Library**
- Upload and manage PDF documents
- Rich metadata support (Title, Author, Subject, ISBN, Category, Tags)
- In-browser PDF viewer with fullscreen mode
- View and download statistics tracking
- Public browsing for unauthenticated users
- Link digital resources to physical books

#### 👥 **User Management**
- Three-tier role-based access control (Admin, Librarian, Viewer)
- Secure authentication with JWT tokens
- Password reset functionality with token-based recovery
- User activity tracking

#### 📊 **Dashboard & Analytics**
- Real-time statistics (Total Books, Issued, Overdue, Digital Resources)
- Subject distribution charts
- Quick access to recent activities
- System health monitoring

#### 🔐 **Security Features**
- Role-based access control (RBAC)
- Password hashing with bcrypt
- JWT token-based authentication
- Password history tracking (prevents reuse)
- Secure password reset with time-limited tokens

---

## 🎭 User Roles & Permissions

| Feature | Viewer | Librarian | Admin |
|---------|--------|-----------|-------|
| View Books & Transactions | ✅ | ✅ | ✅ |
| Issue/Return/Extend Books | ❌ | ✅ | ✅ |
| Add Physical Books | ❌ | ✅ | ✅ |
| Edit Book Metadata | ❌ | ✅ | ✅ |
| Upload Digital Books | ❌ | ✅ | ✅ |
| Delete Books | ❌ | ❌ | ✅ |
| User Management | ❌ | ❌ | ✅ |
| Generate Reset Tokens | ❌ | ❌ | ✅ |

---

## 🏗️ Technology Stack

### **Backend**
- **Framework**: FastAPI 0.109.0 (Python 3.11+)
- **Database**: SQLAlchemy 2.0.25 with SQLite
- **Authentication**: python-jose (JWT) + passlib + bcrypt
- **Server**: Uvicorn (development) / Waitress (production)

### **Frontend**
- **Framework**: Alpine.js 3.x
- **UI Library**: Bulma CSS 0.9.4
- **Styling**: Tailwind CSS + Custom CSS
- **Icons**: Font Awesome 6.x
- **Charts**: Chart.js
- **Animations**: Animate.css

### **File Storage**
- Physical files stored in `library_vault/digital_books/`
- Database metadata in SQLite (`data/tic_nexus.db`)

---

## 📁 Project Structure

```
tic-nexus/
├── app/                          # Main application package
│   ├── __init__.py              # Package initialization
│   ├── main.py                  # FastAPI application & routes
│   ├── models.py                # SQLAlchemy database models
│   ├── schemas.py               # Pydantic schemas for validation
│   ├── database.py              # Database configuration
│   ├── auth.py                  # Authentication & authorization
│   ├── routes.py                # Book & circulation API routes
│   ├── digital_library_routes.py # Digital library API routes
│   ├── password_reset.py        # Password reset functionality
│   ├── circulation.py           # Circulation logic
│   └── password_utils.py        # Password utility functions
│
├── templates/                    # Jinja2 HTML templates
│   ├── base.html                # Base template
│   ├── sidebar.html             # Navigation sidebar
│   ├── home_bulma.html          # Public homepage
│   ├── login.html               # Login page
│   ├── dashboard.html           # Dashboard
│   ├── inventory.html           # Book inventory management
│   ├── circulation.html         # Issue/Return/Extend operations
│   ├── digital_library.html     # Digital library management
│   ├── digital_library_browse.html  # Browse digital books
│   ├── digital_library_detail.html  # View/download digital books
│   ├── users.html               # User management (Admin only)
│   └── ...                      # Additional templates
│
├── static/                       # Static assets
│   ├── css/                     # Stylesheets
│   │   ├── bulma.min.css        # Bulma framework
│   │   ├── tailwind.css         # Tailwind utilities
│   │   ├── custom.css           # Custom styles
│   │   └── animate.min.css      # Animations
│   └── js/                      # JavaScript files
│       ├── alpine.min.js        # Alpine.js framework
│       ├── chart.min.js         # Chart.js library
│       ├── toast.js             # Toast notifications
│       └── auth-check.js        # Authentication utilities
│
├── data/                         # Application data
│   └── tic_nexus.db             # SQLite database (auto-created)
│
├── library_vault/               # File storage
│   └── digital_books/           # Uploaded PDF files
│
├── scripts/                      # Utility scripts
│   ├── download_assets.py       # Download frontend assets
│   ├── reset_admin_password.py  # Admin password reset utility
│   └── test_application.py      # Application testing
│
├── venv/                         # Virtual environment (excluded)
├── requirements.txt              # Python dependencies
├── run_nexus.bat                # Windows startup script
├── README.md                     # This file
├── QUICK_START.md               # Quick start guide
├── SETUP_GUIDE.md               # Detailed setup instructions
└── AGENTS.md                    # AI agent development guide
```

---

## 🚀 Quick Start

For a rapid setup, see **[QUICK_START.md](QUICK_START.md)**.

### Prerequisites
- Python 3.11 or higher
- pip (Python package manager)
- Git (optional)

### Installation (Summary)

1. **Clone or download the project**
```bash
git clone <repository-url>
cd tic-nexus
```

2. **Create virtual environment**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Download frontend assets**
```bash
python scripts/download_assets.py
```

5. **Run the application**
```bash
# Development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production (Windows)
run_nexus.bat
```

6. **Access the application**
- Open browser: `http://localhost:8000`
- Default credentials: `admin` / `admin123`

For detailed installation instructions, see **[SETUP_GUIDE.md](SETUP_GUIDE.md)**.

---

## 📖 Usage Guide

### First Time Setup

1. **Login with default admin credentials**
   - Username: `admin`
   - Password: `admin123`
   - **⚠️ Change this password immediately!**

2. **Create additional users**
   - Navigate to "User Management"
   - Add librarians and viewers as needed
   - Assign appropriate roles

3. **Add books to inventory**
   - Go to "Inventory" → "Add Book"
   - Fill in book details
   - Use storage location format: `TLC-R-1-S-5` (Rack 1, Shelf 5)

4. **Upload digital resources**
   - Navigate to "Digital Library"
   - Click "Upload Digital Book"
   - Fill metadata and select PDF file

### Daily Operations

#### Issue a Book
1. Go to "Circulation" → "Issue" tab
2. Select book from dropdown
3. Select user
4. Set due date (default: 14 days)
5. Click "Issue Book"

#### Return a Book
1. Go to "Circulation" → "Return" tab
2. Select active transaction
3. Add return notes (optional)
4. Click "Return Book"

#### Extend a Book
1. Go to "Circulation" → "Extend" tab
2. Select eligible transaction
3. Click "Extend" (adds 7 days, max 2 extensions)

---

## 🔧 Configuration

### Database
- Location: `data/tic_nexus.db`
- Automatically created on first run
- Backup recommended before updates

### File Storage
- Digital books: `library_vault/digital_books/`
- Ensure sufficient disk space
- Regular backups recommended

### Security
- **JWT Secret**: Edit `app/auth.py` → `SECRET_KEY` (change before production!)
- **Token Expiry**: Default 7 days (configurable in `auth.py`)
- **Password Policy**: Minimum 8 characters (configurable)

---

## 🛠️ Administration

### Reset Admin Password
If you lose admin access:
```bash
python scripts/reset_admin_password.py
```
Follow prompts to reset password.

### Database Backup
```bash
# Manual backup
copy data\tic_nexus.db data\tic_nexus_backup.db

# Scheduled backup (Windows Task Scheduler recommended)
```

### Viewing Logs
Application logs are printed to console. For production:
```bash
uvicorn app.main:app --log-level info > app.log 2>&1
```

---

## 🐛 Troubleshooting

### Common Issues

**Issue**: Application won't start
- Check if port 8000 is already in use
- Verify Python version: `python --version` (3.11+)
- Ensure virtual environment is activated

**Issue**: Login fails with correct credentials
- Check if `data/tic_nexus.db` exists
- Try resetting admin password with `scripts/reset_admin_password.py`

**Issue**: Digital books won't upload
- Verify `library_vault/digital_books/` directory exists
- Check file permissions
- Ensure PDF file is valid

**Issue**: Frontend assets missing (no styles)
- Run `python scripts/download_assets.py`
- Check `static/css/` and `static/js/` directories

---

## 🚦 Development

### Running in Development Mode
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Running Tests
```bash
python scripts/test_application.py
```

### For AI Agents
See **[AGENTS.md](AGENTS.md)** for development guidelines and token optimization strategies.

---

## 📝 API Documentation

FastAPI provides automatic interactive API documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## 🤝 Contributing

This is a proprietary project for Bharat Electronics Limited. For internal contributions:

1. Create a feature branch
2. Make changes with clear commit messages
3. Test thoroughly
4. Submit for review

---

## 📄 License

**Proprietary Software** - © 2024 Bharat Electronics Limited  
All rights reserved. Unauthorized copying, distribution, or modification is prohibited.

---

## 👨‍💻 Support

For technical support or questions:
- Internal: Contact IT Department
- Email: tlc-support@bel.in (update with actual contact)

---

## 🎉 Acknowledgments

- **Developed for**: Bharat Electronics Limited - Technical Information Center
- **Framework**: FastAPI community
- **UI**: Bulma CSS & Alpine.js communities
- **Icons**: Font Awesome

---

**Version**: 1.0.0  
**Last Updated**: February 2024  
**Status**: Production Ready ✅
