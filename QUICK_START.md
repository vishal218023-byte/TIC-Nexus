# TIC Nexus - Quick Start Guide

Get up and running with TIC Nexus in **5 minutes**! ⚡

---

## 📋 Prerequisites

Before you begin, ensure you have:
- ✅ **Python 3.11+** installed ([Download](https://www.python.org/downloads/))
- ✅ **pip** (comes with Python)
- ✅ Internet connection (for downloading dependencies)

**Check your Python version:**
```bash
python --version
# Should show: Python 3.11.x or higher
```

---

## 🚀 Installation (5 Steps)

### Step 1: Extract/Clone the Project

```bash
# If you have a ZIP file
unzip tic-nexus.zip
cd tic-nexus

# OR if using Git
git clone <repository-url>
cd tic-nexus
```

---

### Step 2: Create Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**✅ You should see `(venv)` in your terminal prompt**

---

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

**Expected output:** Installing 10-15 packages (FastAPI, SQLAlchemy, etc.)  
**Time:** ~1-2 minutes depending on internet speed

---

### Step 4: Download Frontend Assets

```bash
python scripts/download_assets.py
```

**What this does:**
- Downloads Bulma CSS
- Downloads Alpine.js
- Downloads Font Awesome icons
- Downloads Chart.js

**✅ Success message:** "All assets downloaded successfully!"

---

### Step 5: Start the Application

**Option A - Development Mode (Recommended for testing):**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Option B - Production Mode (Windows):**
```bash
run_nexus.bat
```

**Option C - Production Mode (Linux/Mac):**
```bash
waitress-serve --host=0.0.0.0 --port=8000 app.main:app
```

**✅ Success message:** "Application startup complete"

---

## 🌐 Access the Application

1. **Open your web browser**
2. **Navigate to:** `http://localhost:8000`
3. **You should see the TIC Nexus homepage!** 🎉

---

## 🔐 First Login

### Default Admin Credentials
- **Username:** `admin`
- **Password:** `admin123`

### ⚠️ IMPORTANT: Change Password Immediately!

After first login:
1. Click your username in the sidebar
2. Select "Change Password"
3. Set a strong, secure password
4. Save changes

---

## 🎯 Quick Feature Tour

### 1️⃣ **Dashboard** (First Page After Login)
- View total books, issued books, overdue books
- See subject distribution chart
- Quick access to all features

### 2️⃣ **Add Your First Book**
1. Click "Inventory" in sidebar
2. Click "Add Book" button
3. Fill in the details:
   - **Accession No:** `BK001` (must be unique)
   - **Title:** `Introduction to FastAPI`
   - **Author:** `John Doe`
   - **Storage Location:** `TIC-R-1-S-1` (Rack 1, Shelf 1)
4. Click "Add Book"

**✅ Your first book is now in the system!**

### 3️⃣ **Create a User**
1. Click "User Management" in sidebar
2. Click "Add User"
3. Fill in details:
   - **Username:** `librarian1`
   - **Full Name:** `John Smith`
   - **Email:** `john@example.com`
   - **Password:** (set secure password)
   - **Role:** `Librarian`
4. Click "Create User"

**✅ New user can now login!**

### 4️⃣ **Upload a Digital Book**
1. Click "Digital Library" in sidebar
2. Click "Upload Digital Book"
3. Fill metadata:
   - **Title:** `Python Programming Guide`
   - **Author:** `Jane Doe`
   - **Subject:** `Programming`
4. Select a PDF file
5. Click "Upload"

**✅ Digital book is now available for viewing!**

### 5️⃣ **Issue a Book**
1. Click "Circulation" in sidebar
2. Go to "Issue" tab
3. Select book from dropdown
4. Select user
5. Set due date (default: 14 days)
6. Click "Issue Book"

**✅ Book is now issued to the user!**

---

## 👥 Understanding User Roles

| Role | What They Can Do |
|------|------------------|
| **Viewer** | 📖 View books and transactions only |
| **Librarian** | 📚 Issue/return books, add books, upload digital content |
| **Admin** | 🔐 Everything + user management + delete operations |

---

## 🔄 Daily Workflow Example

**Morning Routine:**
1. Login to dashboard
2. Check overdue books (if any)
3. Process book returns from previous day
4. Issue new books to users

**Throughout the Day:**
5. Add new books to inventory as they arrive
6. Upload digital resources
7. Extend book due dates if requested

**Evening:**
8. Review day's transactions
9. Plan for next day

---

## 📱 Browser Compatibility

TIC Nexus works best on:
- ✅ **Google Chrome** (Recommended)
- ✅ **Microsoft Edge**
- ✅ **Firefox**
- ✅ **Safari**

**Minimum resolution:** 1366x768

---

## 🛑 Stopping the Application

**If running in development mode:**
- Press `Ctrl+C` in the terminal

**If running as Windows service:**
- Close the command prompt window
- OR press `Ctrl+C`

---

## 🆘 Quick Troubleshooting

### Problem: "Port 8000 already in use"
**Solution:**
```bash
# Use a different port
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
# Then access at: http://localhost:8001
```

### Problem: "Module not found" errors
**Solution:**
```bash
# Make sure virtual environment is activated
# You should see (venv) in your terminal
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Then reinstall dependencies
pip install -r requirements.txt
```

### Problem: "Cannot login with admin/admin123"
**Solution:**
```bash
# Reset admin password
python scripts/reset_admin_password.py
# Follow the prompts
```

### Problem: "No styles, looks broken"
**Solution:**
```bash
# Download frontend assets again
python scripts/download_assets.py
```

### Problem: Database error on startup
**Solution:**
```bash
# Delete and recreate database
# (WARNING: This deletes all data!)
del data\tic_nexus.db  # Windows
rm data/tic_nexus.db   # Linux/Mac

# Restart application - it will create a fresh database
```

---

## 🎓 Next Steps

Now that you're up and running:

1. **📖 Read the full documentation:** [README.md](README.md)
2. **🔧 Detailed setup:** [SETUP_GUIDE.md](SETUP_GUIDE.md)
3. **🤖 For developers:** [AGENTS.md](AGENTS.md)

### Learn More About:
- **User Management:** How to create and manage users
- **Backup & Restore:** Protecting your data
- **Advanced Features:** Digital-physical book linking, bulk operations
- **Security:** Changing JWT secrets, password policies
- **Deployment:** Running in production environment

---

## 📞 Getting Help

**Need assistance?**
- 📚 Check [README.md](README.md) for detailed documentation
- 🔧 See [SETUP_GUIDE.md](SETUP_GUIDE.md) for setup issues
- 🐛 Review troubleshooting section above
- 💬 Contact: tic-support@bel.in

---

## ✅ Quick Reference Commands

```bash
# Activate virtual environment
venv\Scripts\activate                      # Windows
source venv/bin/activate                   # Linux/Mac

# Start application (development)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start application (production Windows)
run_nexus.bat

# Reset admin password
python scripts/reset_admin_password.py

# Download assets
python scripts/download_assets.py

# Run tests
python scripts/test_application.py
```

---

## 🎉 Congratulations!

You're all set! TIC Nexus is now running and ready to manage your library.

**Happy Library Management!** 📚✨

---

**Version:** 1.0.0  
**Last Updated:** February 2024
