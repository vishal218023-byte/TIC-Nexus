# TIC Nexus - Comprehensive Setup Guide

Complete installation and configuration guide for TIC Nexus Library Management System.

---

## 📑 Table of Contents

1. [System Requirements](#-system-requirements)
2. [Pre-Installation Steps](#-pre-installation-steps)
3. [Installation](#-installation)
4. [Configuration](#-configuration)
5. [First-Time Setup](#-first-time-setup)
6. [Production Deployment](#-production-deployment)
7. [Database Management](#-database-management)
8. [Security Hardening](#-security-hardening)
9. [Backup & Recovery](#-backup--recovery)
10. [Troubleshooting](#-troubleshooting)

---

## 💻 System Requirements

### Minimum Requirements
- **OS**: Windows 10/11, Ubuntu 20.04+, macOS 10.15+
- **CPU**: 2 cores, 2 GHz
- **RAM**: 2 GB
- **Storage**: 5 GB free space
- **Python**: 3.11 or higher
- **Network**: Internet connection (for initial setup)

### Recommended Requirements
- **OS**: Windows 11, Ubuntu 22.04+, macOS 12+
- **CPU**: 4 cores, 2.5 GHz+
- **RAM**: 4 GB+
- **Storage**: 20 GB+ (for digital library growth)
- **Python**: 3.11 or 3.12
- **Network**: Stable LAN/WAN connection

### Browser Compatibility
- Google Chrome 90+ (Recommended)
- Microsoft Edge 90+
- Firefox 88+
- Safari 14+

---

## 🔧 Pre-Installation Steps

### Step 1: Install Python

#### Windows
1. Download Python from [python.org](https://www.python.org/downloads/)
2. Run installer
3. **✅ IMPORTANT**: Check "Add Python to PATH"
4. Click "Install Now"
5. Verify installation:
   ```cmd
   python --version
   pip --version
   ```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip
python3.11 --version
```

#### macOS
```bash
# Using Homebrew
brew install python@3.11
python3.11 --version
```

### Step 2: Install Git (Optional)

**Windows**: Download from [git-scm.com](https://git-scm.com/)  
**Linux**: `sudo apt install git`  
**macOS**: `brew install git`

### Step 3: Prepare Installation Directory

```bash
# Create a dedicated directory
mkdir C:\BEL\TIC-Nexus          # Windows
mkdir ~/BEL/TIC-Nexus            # Linux/Mac

cd C:\BEL\TIC-Nexus              # Windows
cd ~/BEL/TIC-Nexus               # Linux/Mac
```

---

## 📦 Installation

### Method 1: From ZIP Archive

1. **Extract the archive**
   ```bash
   # Windows: Right-click → Extract All
   # Linux/Mac:
   unzip tic-nexus-v1.0.0.zip
   cd tic-nexus
   ```

2. **Create virtual environment**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # Linux/Mac
   python3.11 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Download frontend assets**
   ```bash
   python scripts/download_assets.py
   ```

### Method 2: From Git Repository

1. **Clone repository**
   ```bash
   git clone <repository-url>
   cd tic-nexus
   ```

2. **Create virtual environment**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # Linux/Mac
   python3.11 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Download frontend assets**
   ```bash
   python scripts/download_assets.py
   ```

### Verification

Verify all components are installed:

```bash
# Check Python packages
pip list

# Expected packages:
# fastapi, uvicorn, sqlalchemy, python-jose, passlib, bcrypt, etc.

# Check directory structure
dir static\css     # Windows
ls static/css      # Linux/Mac

# Should show: bulma.min.css, tailwind.css, custom.css, animate.min.css
```

---

## ⚙️ Configuration

### 1. Database Configuration

The application uses SQLite by default. Location: `data/tic_nexus.db`

**For Production with PostgreSQL/MySQL:**

Edit `app/database.py`:

```python
# SQLite (default)
SQLALCHEMY_DATABASE_URL = "sqlite:///./data/tic_nexus.db"

# PostgreSQL (production)
# SQLALCHEMY_DATABASE_URL = "postgresql://user:password@localhost/tic_nexus"

# MySQL (production)
# SQLALCHEMY_DATABASE_URL = "mysql+pymysql://user:password@localhost/tic_nexus"
```

Install additional drivers if needed:
```bash
pip install psycopg2-binary  # PostgreSQL
pip install pymysql          # MySQL
```

### 2. Security Configuration

**CRITICAL: Change JWT Secret Key**

Edit `app/auth.py`:

```python
# CHANGE THIS BEFORE PRODUCTION!
SECRET_KEY = "your-super-secret-key-change-this-in-production-min-32-chars"

# Generate a secure key:
# python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Set Token Expiration**

```python
# Default: 7 days
ACCESS_TOKEN_EXPIRE_DAYS = 7

# For high-security: 1 day
ACCESS_TOKEN_EXPIRE_DAYS = 1
```

### 3. File Storage Configuration

Default location: `library_vault/digital_books/`

**To change storage location:**

Edit `app/main.py`:

```python
# Change these paths
LIBRARY_VAULT = "/path/to/your/storage"  # Custom path
DIGITAL_BOOKS_DIR = os.path.join(LIBRARY_VAULT, "digital_books")
```

**Set appropriate permissions:**

```bash
# Linux/Mac
chmod 755 library_vault/
chmod 755 library_vault/digital_books/

# Windows: Right-click → Properties → Security
```

### 4. Server Configuration

**Development Server (Uvicorn):**

Create `uvicorn_config.py`:

```python
# Development
bind = "0.0.0.0:8000"
workers = 1
reload = True
log_level = "info"
```

**Production Server (Waitress - Windows):**

Edit `run_nexus.bat`:

```batch
@echo off
echo Starting TIC Nexus Production Server...
call venv\Scripts\activate.bat
waitress-serve --host=0.0.0.0 --port=8000 --threads=4 app.main:app
```

**Production Server (Gunicorn - Linux):**

Create `gunicorn_config.py`:

```python
# Production
bind = "0.0.0.0:8000"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
accesslog = "logs/access.log"
errorlog = "logs/error.log"
loglevel = "info"
```

Run with:
```bash
gunicorn -c gunicorn_config.py app.main:app
```

---

## 🎬 First-Time Setup

### 1. Initial Startup

```bash
# Activate virtual environment
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Start application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
✓ Default admin user created (username: admin, password: admin123)
```

### 2. Access Web Interface

Open browser: `http://localhost:8000`

### 3. Change Default Admin Password

1. Login with `admin` / `admin123`
2. Click "Change Password" in user dropdown
3. Set strong password (min 8 characters)
4. Save and logout
5. Login with new password

### 4. Create Initial Users

**Create a Librarian:**
1. Go to "User Management"
2. Click "Add User"
3. Fill details:
   - Username: `librarian1`
   - Full Name: `John Smith`
   - Email: `john.smith@bel.in`
   - Password: (secure password)
   - Role: **Librarian**
4. Click "Create User"

**Create a Viewer:**
1. Click "Add User" again
2. Fill details:
   - Username: `viewer1`
   - Full Name: `Jane Doe`
   - Email: `jane.doe@bel.in`
   - Password: (secure password)
   - Role: **Viewer**
3. Click "Create User"

### 5. Add Sample Data

**Add First Book:**
1. Go to "Inventory"
2. Click "Add Book"
3. Fill details:
   - Accession No: `BK001`
   - Title: `Introduction to Python`
   - Author: `Mark Lutz`
   - Publisher: `O'Reilly Media`
   - Subject: `Computer Science`
   - Year: `2023`
   - ISBN: `978-1-449-35573-9`
   - Storage: `TIC-R-1-S-1`
4. Click "Add Book"

**Upload First Digital Book:**
1. Go to "Digital Library"
2. Click "Upload Digital Book"
3. Fill metadata and select PDF
4. Click "Upload"

---

## 🚀 Production Deployment

### Option 1: Windows Server

1. **Install Python 3.11+**

2. **Install Application**
   ```cmd
   cd C:\BEL\TIC-Nexus
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   python scripts/download_assets.py
   ```

3. **Create Windows Service (using NSSM)**
   
   Download NSSM: [nssm.cc](https://nssm.cc/download)
   
   ```cmd
   nssm install TICNexus "C:\BEL\TIC-Nexus\venv\Scripts\python.exe" "-m" "waitress" "--host=0.0.0.0" "--port=8000" "app.main:app"
   nssm set TICNexus AppDirectory "C:\BEL\TIC-Nexus"
   nssm start TICNexus
   ```

4. **Configure Windows Firewall**
   ```cmd
   netsh advfirewall firewall add rule name="TIC Nexus" dir=in action=allow protocol=TCP localport=8000
   ```

### Option 2: Linux Server (Ubuntu)

1. **Install Dependencies**
   ```bash
   sudo apt update
   sudo apt install python3.11 python3.11-venv python3-pip nginx
   ```

2. **Install Application**
   ```bash
   cd /opt/tic-nexus
   python3.11 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   pip install gunicorn
   python scripts/download_assets.py
   ```

3. **Create Systemd Service**
   
   Create `/etc/systemd/system/tic-nexus.service`:
   
   ```ini
   [Unit]
   Description=TIC Nexus Library Management System
   After=network.target
   
   [Service]
   Type=notify
   User=www-data
   Group=www-data
   WorkingDirectory=/opt/tic-nexus
   Environment="PATH=/opt/tic-nexus/venv/bin"
   ExecStart=/opt/tic-nexus/venv/bin/gunicorn -c gunicorn_config.py app.main:app
   Restart=always
   
   [Install]
   WantedBy=multi-user.target
   ```

4. **Start Service**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable tic-nexus
   sudo systemctl start tic-nexus
   sudo systemctl status tic-nexus
   ```

5. **Configure Nginx Reverse Proxy**
   
   Create `/etc/nginx/sites-available/tic-nexus`:
   
   ```nginx
   server {
       listen 80;
       server_name tic-nexus.bel.in;
       
       client_max_body_size 100M;
       
       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```
   
   Enable and restart:
   ```bash
   sudo ln -s /etc/nginx/sites-available/tic-nexus /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

### Option 3: Docker Deployment

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python scripts/download_assets.py

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  tic-nexus:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./library_vault:/app/library_vault
    environment:
      - PYTHONUNBUFFERED=1
    restart: unless-stopped
```

Deploy:
```bash
docker-compose up -d
```

---

## 🗄️ Database Management

### Backup Database

**SQLite (default):**
```bash
# Manual backup
copy data\tic_nexus.db data\backups\tic_nexus_backup_YYYYMMDD.db  # Windows
cp data/tic_nexus.db data/backups/tic_nexus_backup_$(date +%Y%m%d).db  # Linux

# Automated backup script (Windows)
# Create backup_db.bat:
@echo off
set backup_dir=data\backups
if not exist %backup_dir% mkdir %backup_dir%
set timestamp=%date:~-4%%date:~3,2%%date:~0,2%
copy data\tic_nexus.db %backup_dir%\tic_nexus_%timestamp%.db
echo Backup completed: %backup_dir%\tic_nexus_%timestamp%.db
```

**Schedule with Windows Task Scheduler:**
1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Daily at 2:00 AM
4. Action: Start a program → `backup_db.bat`

### Restore Database

```bash
# Stop application first
# Then restore:
copy data\backups\tic_nexus_backup_20240201.db data\tic_nexus.db  # Windows
cp data/backups/tic_nexus_backup_20240201.db data/tic_nexus.db  # Linux

# Restart application
```

### Database Maintenance

**Check database integrity:**
```bash
sqlite3 data/tic_nexus.db "PRAGMA integrity_check;"
```

**Vacuum database (optimize size):**
```bash
sqlite3 data/tic_nexus.db "VACUUM;"
```

---

## 🔒 Security Hardening

### 1. Change Default Secrets

**JWT Secret Key:**
```python
# Generate secure key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Update in app/auth.py
SECRET_KEY = "generated-key-here"
```

### 2. Enforce Strong Passwords

Edit `app/password_utils.py`:

```python
MIN_PASSWORD_LENGTH = 12  # Increase from 8
REQUIRE_UPPERCASE = True
REQUIRE_LOWERCASE = True
REQUIRE_DIGITS = True
REQUIRE_SPECIAL = True
```

### 3. Enable HTTPS (Production)

**Using Nginx with Let's Encrypt:**
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d tic-nexus.bel.in
```

### 4. Configure CORS (if needed)

Edit `app/main.py`:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://tic-nexus.bel.in"],  # Specific domain
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

### 5. Rate Limiting (Advanced)

Install slowapi:
```bash
pip install slowapi
```

Configure in `app/main.py`:
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/api/auth/login")
@limiter.limit("5/minute")  # 5 login attempts per minute
async def login(...):
    ...
```

---

## 💾 Backup & Recovery

### Complete Backup Strategy

**What to backup:**
1. ✅ Database: `data/tic_nexus.db`
2. ✅ Digital files: `library_vault/digital_books/`
3. ✅ Configuration: `app/*.py` (if customized)

**Backup Script (Windows):**

Create `scripts/backup_complete.bat`:
```batch
@echo off
set backup_root=D:\Backups\TIC-Nexus
set timestamp=%date:~-4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%
set backup_dir=%backup_root%\backup_%timestamp%

echo Creating backup directory...
mkdir "%backup_dir%"

echo Backing up database...
copy data\tic_nexus.db "%backup_dir%\"

echo Backing up digital library...
xcopy library_vault "%backup_dir%\library_vault\" /E /I /Y

echo Backup completed: %backup_dir%
```

**Backup Script (Linux):**

Create `scripts/backup_complete.sh`:
```bash
#!/bin/bash
backup_root="/backup/tic-nexus"
timestamp=$(date +%Y%m%d_%H%M%S)
backup_dir="$backup_root/backup_$timestamp"

echo "Creating backup directory..."
mkdir -p "$backup_dir"

echo "Backing up database..."
cp data/tic_nexus.db "$backup_dir/"

echo "Backing up digital library..."
cp -r library_vault "$backup_dir/"

echo "Creating archive..."
tar -czf "$backup_dir.tar.gz" -C "$backup_root" "backup_$timestamp"
rm -rf "$backup_dir"

echo "Backup completed: $backup_dir.tar.gz"
```

### Recovery Procedure

**Full System Recovery:**

1. **Stop application**
2. **Restore database:**
   ```bash
   copy backup\tic_nexus.db data\tic_nexus.db
   ```
3. **Restore digital files:**
   ```bash
   xcopy backup\library_vault library_vault\ /E /I /Y
   ```
4. **Restart application**
5. **Verify data integrity**

---

## 🐛 Troubleshooting

### Common Installation Issues

**Issue: "Python not found"**
```bash
# Solution: Add Python to PATH
# Windows: Reinstall Python with "Add to PATH" checked
# Linux: Use full path
/usr/bin/python3.11 -m venv venv
```

**Issue: "pip: command not found"**
```bash
# Solution: Install pip
python -m ensurepip --upgrade
```

**Issue: "Permission denied" on Linux**
```bash
# Solution: Fix permissions
sudo chown -R $USER:$USER /opt/tic-nexus
chmod -R 755 /opt/tic-nexus
```

### Runtime Issues

**Issue: "Database is locked"**
```bash
# Solution: Stop all instances
# Check for running processes:
tasklist | findstr python  # Windows
ps aux | grep python       # Linux

# Kill processes if needed
taskkill /F /IM python.exe  # Windows
pkill -f "uvicorn"          # Linux
```

**Issue: "Cannot upload files"**
```bash
# Solution: Check directory permissions
# Windows: Right-click library_vault → Properties → Security
# Linux:
chmod 755 library_vault/digital_books/
```

**Issue: "Slow performance"**
```bash
# Solution: Vacuum database
sqlite3 data/tlc_nexus.db "VACUUM;"

# Increase worker threads
waitress-serve --threads=8 app.main:app
```

### Network Issues

**Issue: "Connection refused"**
```bash
# Check if application is running
netstat -ano | findstr :8000  # Windows
netstat -tulpn | grep :8000   # Linux

# Check firewall
# Windows: Allow port 8000 in Windows Firewall
# Linux: sudo ufw allow 8000
```

**Issue: "Cannot access from other computers"**
```bash
# Solution: Bind to 0.0.0.0 instead of 127.0.0.1
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Getting Help

1. Check application logs
2. Review [README.md](README.md)
3. Check [QUICK_START.md](QUICK_START.md)
4. Contact: tlc-support@bel.in

---

## 📊 Performance Tuning

### For Small Libraries (<10,000 books)
```bash
# Single worker sufficient
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### For Medium Libraries (10,000-50,000 books)
```bash
# Multiple workers
waitress-serve --threads=4 --host=0.0.0.0 --port=8000 app.main:app
```

### For Large Libraries (>50,000 books)
```bash
# Use Gunicorn with multiple workers
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
```

---

## ✅ Post-Installation Checklist

- [ ] Python 3.11+ installed
- [ ] Virtual environment created and activated
- [ ] All dependencies installed
- [ ] Frontend assets downloaded
- [ ] Application starts without errors
- [ ] Can access web interface
- [ ] Default admin password changed
- [ ] Additional users created
- [ ] Sample data added
- [ ] Database backup configured
- [ ] JWT secret key changed
- [ ] Firewall configured
- [ ] Production server setup (if applicable)
- [ ] Documentation reviewed

---

**Congratulations! TIC Nexus is fully configured and ready for production use!** 🎉

---

**Version:** 1.0.0  
**Last Updated:** February 2024  
**Support:** tlc-support@bel.in
