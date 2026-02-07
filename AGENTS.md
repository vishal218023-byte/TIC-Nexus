# TIC Nexus - AI Agent Development Guide

**For AI Coding Assistants:** Guidelines, architecture overview, and token optimization strategies for efficient code generation and modifications.

---

## 📋 Table of Contents

1. [Project Overview](#-project-overview)
2. [Architecture & Design Patterns](#-architecture--design-patterns)
3. [File Organization](#-file-organization)
4. [Coding Standards](#-coding-standards)
5. [Token Optimization Strategies](#-token-optimization-strategies)
6. [Common Tasks](#-common-tasks)
7. [Testing Guidelines](#-testing-guidelines)
8. [Security Considerations](#-security-considerations)

---

## 🎯 Project Overview

### Technology Stack
```
Backend:  FastAPI 0.109.0 + SQLAlchemy 2.0.25 + SQLite
Auth:     JWT (python-jose) + bcrypt password hashing
Frontend: Alpine.js 3.x + Bulma CSS + Tailwind CSS
Server:   Uvicorn (dev) / Waitress (prod)
```

### Core Features
- **Physical Inventory**: Book catalog with circulation (issue/return/extend)
- **Digital Library**: PDF upload, viewing, download tracking
- **User Management**: 3-tier RBAC (Admin, Librarian, Viewer)
- **Dashboard**: Statistics, charts, real-time status

### Design Philosophy
- **RESTful API**: Clear separation between API and web routes
- **Client-side Auth**: JWT token stored in localStorage, validated on API calls
- **Role-based Access**: Backend enforcement + frontend UI hiding
- **Modular Structure**: Separate files for routes, models, auth, schemas

---

## 🏗️ Architecture & Design Patterns

### Backend Structure

```
app/
├── main.py                    # FastAPI app, web routes, exception handlers
├── models.py                  # SQLAlchemy models (8 tables)
├── schemas.py                 # Pydantic schemas for validation
├── database.py                # DB connection, session management
├── auth.py                    # JWT auth, password hashing, dependencies
├── routes.py                  # Book & circulation API endpoints
├── digital_library_routes.py  # Digital library API endpoints
├── password_reset.py          # Password reset token management
├── circulation.py             # Business logic for issue/return/extend
└── password_utils.py          # Password validation utilities
```

### Key Design Patterns

#### 1. **Dependency Injection** (FastAPI)
```python
# Auth dependencies
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    # Validates JWT, returns user

async def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    # Validates admin role

async def get_current_librarian_or_admin(current_user: User = Depends(get_current_user)) -> User:
    # Validates librarian or admin role
```

**Usage in routes:**
```python
@router.post("/books")
async def create_book(
    book: BookCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_librarian_or_admin)
):
    # Only librarians and admins can create books
```

#### 2. **Repository Pattern** (Implicit)
```python
# Business logic separated in circulation.py
def issue_book(db: Session, book_id: int, user_id: int, due_date: datetime) -> Transaction:
    # Validates book availability
    # Creates transaction
    # Updates book status
    # Returns transaction
```

#### 3. **Schema Validation** (Pydantic)
```python
class BookCreate(BaseModel):
    acc_no: str
    title: str
    author: str
    storage_loc: str  # Format: TIC-R-{rack}-S-{shelf}
    # ... other fields with validators
```

### Frontend Structure

```
templates/
├── base.html              # Base template with header/footer
├── sidebar.html           # Navigation (uses active_page parameter)
├── home_bulma.html        # Public homepage
├── login.html             # Login page
├── dashboard.html         # Dashboard with charts
├── inventory.html         # Book CRUD operations
├── circulation.html       # Issue/Return/Extend tabs
├── digital_library*.html  # Digital library pages
└── users.html             # User management (admin only)

Each page uses:
- Alpine.js for reactivity (x-data, x-show, x-if, x-for)
- Fetch API for async operations
- localStorage for token/role storage
- Toast notifications for feedback
```

### Database Models (8 Tables)

```python
1. User              # Authentication, RBAC
2. Book              # Physical inventory
3. Transaction       # Circulation records
4. DigitalBook       # Digital library resources
5. BookDigitalLink   # Many-to-many: physical ↔ digital
6. PasswordResetToken    # Password reset tokens
7. PasswordHistory       # Prevent password reuse
```

**Key Relationships:**
- User → Transactions (1:N)
- Book → Transactions (1:N)
- Book ↔ DigitalBook (N:M via BookDigitalLink)

---

## 📁 File Organization

### Critical Files (Never Delete/Rename)

```
app/main.py           # Application entry point
app/models.py         # Database schema
app/database.py       # DB connection
requirements.txt      # Dependencies
```

### Utility Scripts (in scripts/)

```
scripts/
├── download_assets.py       # Download frontend libraries
├── reset_admin_password.py  # Emergency admin password reset
└── test_application.py      # Basic application tests
```

### Configuration Files

```
.gitignore           # Excludes venv/, data/, library_vault/
run_nexus.bat        # Windows production launcher
```

---

## 📝 Coding Standards

### Python Style

- **PEP 8** compliance
- **Type hints** for function parameters and returns
- **Docstrings** for all functions/classes
- **4-space indentation**

**Example:**
```python
async def create_book(
    book: BookCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_librarian_or_admin)
) -> BookResponse:
    """
    Create a new physical book entry.
    
    Args:
        book: Book creation data
        db: Database session
        current_user: Authenticated user (librarian or admin)
    
    Returns:
        BookResponse: Created book details
    
    Raises:
        HTTPException: If accession number already exists
    """
    # Implementation
```

### Frontend Standards

**Alpine.js Patterns:**
```javascript
// Always initialize data in init()
{
    books: [],
    loading: false,
    isAdmin: false,
    userName: '',
    
    async init() {
        // Load user info from localStorage
        this.isAdmin = localStorage.getItem('user_role') === 'admin' || 
                       localStorage.getItem('user_role') === 'librarian';
        this.userName = localStorage.getItem('full_name') || 
                        localStorage.getItem('username') || 'User';
        
        // Load initial data
        await this.loadBooks();
    },
    
    async loadBooks() {
        this.loading = true;
        try {
            const response = await fetch('/api/books', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });
            this.books = await response.json();
        } finally {
            this.loading = false;
        }
    }
}
```

**HTML Structure:**
```html
<!-- Use x-cloak to prevent flash -->
<div x-data="appData()" x-cloak>
    <!-- Use x-show for conditional rendering -->
    <button x-show="isAdmin" @click="addBook()">Add Book</button>
    
    <!-- Use x-for for lists -->
    <template x-for="book in books" :key="book.id">
        <div x-text="book.title"></div>
    </template>
</div>
```

### Naming Conventions

```python
# Variables & Functions: snake_case
user_id = 42
def get_active_books() -> List[Book]:

# Classes: PascalCase
class BookCreate(BaseModel):

# Constants: UPPER_SNAKE_CASE
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB

# Private functions: _leading_underscore
def _validate_storage_location(loc: str) -> bool:
```

---

## ⚡ Token Optimization Strategies

### For AI Agents: Efficient Code Reading & Generation

#### Strategy 1: Use Targeted File Opening

**❌ Inefficient:**
```python
# Opens entire codebase (wastes tokens)
open_files(["app/main.py", "app/routes.py", "app/models.py", "templates/*.html"])
```

**✅ Efficient:**
```python
# Open only what's needed
open_files(["app/routes.py"])  # Just the file you're modifying

# Then expand specific sections if needed
expand_code_chunks("app/routes.py", patterns=["def create_book"])
```

#### Strategy 2: Use grep for Discovery

**Before opening files, search first:**
```python
# Find where a function is defined
grep(content_pattern="def issue_book", path_glob="app/*.py")

# Find all API endpoints
grep(content_pattern="@router\.(get|post|put|delete)", path_glob="app/*.py")

# Find where a role is checked
grep(content_pattern="get_current_admin_user|get_current_librarian_or_admin", path_glob="app/*.py")
```

#### Strategy 3: Incremental File Reading

**For large files:**
```python
# Step 1: Open collapsed view (shows function signatures only)
open_files(["app/main.py"])  # Large files auto-collapse

# Step 2: Expand only needed sections
expand_code_chunks("app/main.py", line_ranges=[[100, 150]])  # Specific lines
expand_code_chunks("app/main.py", patterns=["def login"])     # Specific function
```

#### Strategy 4: Pattern-Based Modifications

**When updating multiple similar endpoints:**
```python
# Use find_and_replace_code for repetitive changes
find_and_replace_code(
    file_path="templates/dashboard.html",
    find="localStorage.getItem('user_role') === 'admin'",
    replace="localStorage.getItem('user_role') === 'admin' || localStorage.getItem('user_role') === 'librarian'"
)
```

#### Strategy 5: Context-Aware Exploration

**Build mental model efficiently:**
```python
# 1. Start with models (understand data structure)
open_files(["app/models.py"])

# 2. Check schemas (understand validation)
expand_code_chunks("app/schemas.py", patterns=["BookCreate", "UserCreate"])

# 3. Review specific route
expand_code_chunks("app/routes.py", patterns=["@router.post(\"/books\")"])

# 4. Check auth dependencies
expand_code_chunks("app/auth.py", patterns=["get_current_librarian_or_admin"])
```

---

## 🔧 Common Tasks

### Task 1: Add a New API Endpoint

**Example: Add "Search Books by Author"**

1. **Define schema** (if needed):
```python
# app/schemas.py
class BookSearchResponse(BaseModel):
    id: int
    title: str
    author: str
    acc_no: str
    is_issued: bool
```

2. **Add route**:
```python
# app/routes.py
@router.get("/books/search/author", response_model=List[BookSearchResponse])
async def search_books_by_author(
    author: str = Query(..., min_length=2),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search books by author name."""
    books = db.query(Book).filter(
        Book.author.ilike(f"%{author}%")
    ).limit(50).all()
    return books
```

3. **Add frontend call**:
```javascript
// templates/inventory.html
async searchByAuthor(author) {
    const response = await fetch(`/api/books/search/author?author=${author}`, {
        headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
    });
    return await response.json();
}
```

### Task 2: Add a New User Role

**Example: Add "Guest" role with limited access**

1. **Update model comment**:
```python
# app/models.py
role = Column(String(20), nullable=False, default="viewer")  # admin, librarian, viewer, guest
```

2. **Add auth function**:
```python
# app/auth.py
async def get_current_authenticated_user(current_user: User = Depends(get_current_user)) -> User:
    """Allow any authenticated user (all roles)."""
    return current_user
```

3. **Update validation**:
```python
# app/routes.py - in create_user and update_user
if role not in ["admin", "viewer", "librarian", "guest"]:
    raise HTTPException(status_code=400, detail="Invalid role")
```

4. **Update frontend**:
```html
<!-- templates/users.html -->
<select x-model="currentUser.role" required>
    <option value="viewer">Viewer</option>
    <option value="librarian">Librarian</option>
    <option value="guest">Guest</option>
    <option value="admin">Admin</option>
</select>
```

### Task 3: Add New Field to Book Model

**Example: Add "edition" field**

1. **Add column to model**:
```python
# app/models.py - in Book class
edition = Column(String(50), nullable=True)
```

2. **Update schemas**:
```python
# app/schemas.py
class BookCreate(BaseModel):
    # ... existing fields
    edition: Optional[str] = None

class BookResponse(BaseModel):
    # ... existing fields
    edition: Optional[str] = None
```

3. **Update frontend form**:
```html
<!-- templates/inventory.html -->
<div class="field">
    <label class="label">Edition</label>
    <div class="control">
        <input class="input" type="text" x-model="currentBook.edition">
    </div>
</div>
```

4. **Recreate database** (or use migrations):
```bash
# Simple approach: delete and recreate
rm data/tic_nexus.db
# Restart app - it will create fresh DB with new schema
```

### Task 4: Add Toast Notification

**Standard pattern for user feedback:**

```javascript
// Use the global toast object (defined in static/js/toast.js)

// Success message
window.toast.success('Book added successfully!', 3000);

// Error message
window.toast.error('Failed to add book: ' + error.message, 5000);

// Info message
window.toast.info('Processing your request...', 2000);

// Warning message
window.toast.warning('Book is already issued', 4000);
```

**In template context:**
```javascript
async addBook() {
    try {
        const response = await fetch('/api/books', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(this.currentBook)
        });
        
        if (response.ok) {
            window.toast.success('Book added successfully!');
            await this.loadBooks();
            this.closeModal();
        } else {
            const error = await response.json();
            window.toast.error('Error: ' + error.detail);
        }
    } catch (error) {
        window.toast.error('Network error: ' + error.message);
    }
}
```

---

## 🧪 Testing Guidelines

### Manual Testing Checklist

**After making changes, test:**

1. **Authentication Flow**
   - Login with each role (admin, librarian, viewer)
   - Check role-based UI visibility
   - Verify API endpoint permissions

2. **CRUD Operations**
   - Create: Add new book/user/digital book
   - Read: List and search functionality
   - Update: Edit existing records
   - Delete: Remove records (admin only)

3. **Circulation Flow**
   - Issue book → Check transaction created
   - Return book → Check status updated
   - Extend book → Check due date increased

4. **Edge Cases**
   - Empty search results
   - Duplicate accession numbers
   - Invalid file uploads
   - Expired tokens

### Automated Testing

**Use test_application.py:**
```python
# scripts/test_application.py includes:
# - Database connection test
# - Model creation test
# - API endpoint availability test
# - Authentication test

python scripts/test_application.py
```

**Adding new tests:**
```python
def test_create_book():
    """Test book creation endpoint."""
    # Get admin token
    login_response = client.post("/api/auth/login", data={
        "username": "admin",
        "password": "admin123"
    })
    token = login_response.json()["access_token"]
    
    # Create book
    response = client.post("/api/books", 
        headers={"Authorization": f"Bearer {token}"},
        json={
            "acc_no": "TEST001",
            "title": "Test Book",
            "author": "Test Author",
            "storage_loc": "TIC-R-1-S-1"
        }
    )
    assert response.status_code == 200
```

---

## 🔐 Security Considerations

### Critical Security Rules

1. **Never expose SECRET_KEY**
   ```python
   # app/auth.py - MUST be changed in production
   SECRET_KEY = "your-32-char-minimum-secret-key"
   ```

2. **Always validate role on backend**
   ```python
   # ✅ CORRECT: Backend validation
   @router.delete("/books/{book_id}")
   async def delete_book(
       book_id: int,
       current_user: User = Depends(get_current_admin_user)  # Enforced!
   ):
   
   # ❌ WRONG: Frontend-only hiding
   <button x-show="isAdmin" @click="deleteBook()">Delete</button>
   # Frontend can be bypassed! Always check backend.
   ```

3. **Hash passwords properly**
   ```python
   # ✅ CORRECT: Use bcrypt
   from app.auth import get_password_hash
   hashed = get_password_hash(plain_password)
   
   # ❌ WRONG: Plain text or weak hashing
   user.password = plain_password  # NEVER!
   ```

4. **Validate file uploads**
   ```python
   # Check file type, size, content
   if file.content_type != "application/pdf":
       raise HTTPException(400, "Only PDF files allowed")
   
   if file.size > 50 * 1024 * 1024:  # 50MB
       raise HTTPException(413, "File too large")
   ```

5. **Sanitize user input**
   ```python
   # Use Pydantic for validation
   class BookCreate(BaseModel):
       title: str = Field(..., min_length=1, max_length=500)
       acc_no: str = Field(..., regex=r'^[A-Z0-9-]+$')
   ```

### SQL Injection Prevention

**✅ SAFE (SQLAlchemy ORM):**
```python
# Parameterized queries (automatic)
books = db.query(Book).filter(Book.author == author_input).all()
```

**❌ UNSAFE (Never do this):**
```python
# Raw SQL with string interpolation
db.execute(f"SELECT * FROM books WHERE author = '{author_input}'")
```

### XSS Prevention

**Frontend uses Alpine.js which auto-escapes:**
```html
<!-- ✅ SAFE: x-text auto-escapes -->
<div x-text="book.title"></div>

<!-- ❌ UNSAFE: x-html allows HTML -->
<div x-html="book.title"></div>  <!-- Don't use unless sanitized -->
```

---

## 📚 Key Concepts for AI Agents

### Role-Based Access Control (RBAC)

```
Admin:
  - Full access to everything
  - Can delete books/users
  - User management
  
Librarian:
  - Circulation operations (issue/return/extend)
  - Add/edit books (physical and digital)
  - Cannot delete or manage users
  
Viewer:
  - Read-only access
  - Can view books and transactions
  - Cannot modify anything
```

**Implementation Pattern:**
```python
# Define permission level in dependency
Depends(get_current_user)                  # Any authenticated user
Depends(get_current_librarian_or_admin)    # Librarian or Admin
Depends(get_current_admin_user)            # Admin only
```

### Storage Location Format

**Physical books use rack-shelf system:**
```
Format: TIC-R-{rack}-S-{shelf}
Examples:
  - TIC-R-1-S-5   (Rack 1, Shelf 5)
  - TIC-R-10-S-3  (Rack 10, Shelf 3)

Validation regex: ^TIC-R-\d+-S-\d+$
```

### Circulation Rules

```
Issue:
  - Book must not be already issued
  - User must exist and be active
  - Default loan period: 14 days

Return:
  - Transaction must be active (Issued/Overdue)
  - Updates book.is_issued to False
  - Sets return_date

Extend:
  - Maximum 2 extensions allowed
  - Each extension adds 7 days
  - Transaction must be active
```

### Digital Library

```
File Storage: library_vault/digital_books/{filename}
Metadata: Stored in DigitalBook table
Supported: PDF files only
Max Size: 50MB (configurable)

Features:
  - In-browser PDF viewing
  - Download tracking
  - Public browsing (unauthenticated)
  - Optional linking to physical books
```

---

## 🎯 Quick Reference for Common Patterns

### Adding an Endpoint
```python
# 1. Define in routes
@router.post("/path")
async def function_name(
    data: Schema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_X_user)
):
    # Logic here
    return result

# 2. Add frontend call
async fetchData() {
    const response = await fetch('/api/path', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    });
    return await response.json();
}
```

### Error Handling Pattern
```python
# Backend
if not found:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Resource not found"
    )

# Frontend
try {
    const response = await fetch(...);
    if (!response.ok) {
        const error = await response.json();
        window.toast.error(error.detail);
        return;
    }
    const data = await response.json();
    // Process data
} catch (error) {
    window.toast.error('Network error: ' + error.message);
}
```

### Database Query Pattern
```python
# Single record
book = db.query(Book).filter(Book.id == book_id).first()
if not book:
    raise HTTPException(404, "Book not found")

# Multiple records with pagination
books = db.query(Book).offset(skip).limit(limit).all()

# With search
books = db.query(Book).filter(
    or_(
        Book.title.ilike(f"%{search}%"),
        Book.author.ilike(f"%{search}%")
    )
).all()

# With join
transactions = db.query(Transaction).join(Book).join(User).all()
```

---

## 🚀 Development Workflow

### For AI Agents: Optimal Approach

1. **Understand the Request**
   - Identify what needs to be changed/added
   - Determine affected files (backend, frontend, or both)

2. **Gather Context (Token-Efficient)**
   ```python
   # Use grep to find relevant code
   grep(content_pattern="search_term", path_glob="app/*.py")
   
   # Open only necessary files
   open_files(["app/routes.py"])
   
   # Expand specific sections
   expand_code_chunks("app/routes.py", patterns=["def target_function"])
   ```

3. **Make Changes**
   - Use `find_and_replace_code` for precise modifications
   - Create new files with `create_file` if needed
   - Test after each change

4. **Verify**
   - Check syntax
   - Test manually or with scripts
   - Verify both UI and API

5. **Document**
   - Add docstrings for new functions
   - Update comments if logic changes
   - Update README/guides if major feature added

---

## ✅ Pre-Deployment Checklist

Before pushing changes:

- [ ] All modified files saved
- [ ] No syntax errors
- [ ] Database migrations handled (if schema changed)
- [ ] Frontend assets intact
- [ ] Auth dependencies correct
- [ ] Role permissions enforced on backend
- [ ] Error handling added
- [ ] Toast notifications for user feedback
- [ ] Manual testing completed
- [ ] No sensitive data exposed (passwords, keys)
- [ ] Comments/docstrings updated

---

## 📖 Additional Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **SQLAlchemy Docs**: https://docs.sqlalchemy.org/
- **Alpine.js Docs**: https://alpinejs.dev/
- **Bulma CSS**: https://bulma.io/documentation/

---

**This guide is specifically designed for AI coding agents to understand the TIC Nexus codebase efficiently and make modifications with minimal token usage while maintaining code quality and security standards.**

---

**Version:** 1.0.0  
**Last Updated:** February 2024  
**For:** AI Agents (Claude, GPT-4, Copilot, etc.)
