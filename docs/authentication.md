# Authentication & Authorization

This document explains how authentication and authorization work in TIC Nexus.

## Table of Contents
1. [JWT Authentication](#jwt-authentication)
2. [Role-Based Access Control](#role-based-access-control)
3. [Password Security](#password-security)
4. [Password Reset Process](#password-reset-process)
5. [API Security](#api-security)

---

## JWT Authentication

### Overview

TIC Nexus uses JSON Web Tokens (JWT) for stateless authentication.

**Configuration:**
- Algorithm: HS256
- Secret Key: `BEL-TIC-NEXUS-SECRET-KEY-CHANGE-IN-PRODUCTION`
- Expiration: 8 hours (480 minutes)

### Token Structure

**Payload:**
```json
{
  "sub": "username",
  "exp": 1234567890,
  "iat": 1234567890
}
```

- `sub`: Subject (username)
- `exp`: Expiration timestamp
- `iat`: Issued at timestamp

### Login Process

```
1. User enters credentials on /login page
2. Frontend sends POST to /api/auth/login with form data:
   - username
   - password
3. Backend calls authenticate_user() from auth.py
4. If valid, create_access_token() generates JWT
5. Backend returns: {access_token, token_type, role, user_id, username, full_name}
6. Frontend stores token in localStorage
7. All subsequent API calls include: Authorization: Bearer <token>
```

### Token Validation

All protected endpoints use the `get_current_user` dependency:

```python
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    # 1. Decode JWT using secret key
    # 2. Extract username from payload
    # 3. Query User from database
    # 4. Return User or raise 401
```

---

## Role-Based Access Control

### User Roles

| Role | Description | Use Case |
|------|-------------|----------|
| admin | Full system access | System administration |
| librarian | Circulation & catalog | Daily library operations |
| viewer | Read-only access | Browse catalog only |

### Permission Matrix

| Feature | Admin | Librarian | Viewer |
|---------|-------|------------|--------|
| **Authentication** ||||
| Login | Yes | Yes | Yes |
| Change Password | Yes | Yes | Yes |
| **Dashboard** ||||
| View Dashboard | Yes | Yes | Yes |
| View Statistics | Yes | Yes | Yes |
| **Books** ||||
| List Books | Yes | Yes | Yes |
| View Book Details | Yes | Yes | Yes |
| Create Book | Yes | Yes | No |
| Edit Book | Yes | Yes | No |
| Delete Book | Yes | No | No |
| **Circulation** ||||
| List Transactions | Yes | Yes | Yes |
| Issue Books | Yes | Yes | No |
| Return Books | Yes | Yes | No |
| Extend Books | Yes | Yes | No |
| **Digital Library** ||||
| Browse | Yes | Yes | Yes |
| View/Download | Yes | Yes | Yes |
| Upload | Yes | Yes | No |
| Edit Metadata | Yes | Yes | No |
| Delete | Yes | No | No |
| **Magazines** ||||
| Browse (Public) | Yes | Yes | Yes |
| Manage | Yes | Yes | No |
| **Users** ||||
| List Users | Yes | No | No |
| Create User | Yes | No | No |
| Edit User | Yes | No | No |
| Delete User | Yes | No | No |
| Generate Reset Token | Yes | No | No |

### Implementation

Roles are enforced through dependency injection:

```python
# Any authenticated user
async def get_current_user(...)

# Admin only
async def get_current_admin_user(current_user: User = Depends(get_current_user))

# Librarian or Admin
async def get_current_librarian_or_admin(current_user: User = Depends(get_current_user))
```

**Example usage in routes:**

```python
@router.post("/books")
async def create_book(
    book: BookCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_librarian_or_admin)  # Librarian/Admin only
):
    # Only librarians and admins can create books
```

---

## Password Security

### Hashing

Passwords are hashed using bcrypt:

```python
def get_password_hash(password: str) -> str:
    import bcrypt
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')
```

### Verification

```python
def verify_password(plain_password: str, hashed_password: str) -> bool:
    import bcrypt
    try:
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except:
        # Fallback for old hashes
        return pwd_context.verify(plain_password, hashed_password)
```

### Password Strength Validation

The system validates password strength based on:
- Length (minimum 8 characters)
- Complexity (uppercase, lowercase, digits, special characters)
- Common password detection

**Strength levels:**
- Weak (0-40): Too short or simple
- Medium (41-70): Decent but can be improved
- Strong (71-100): Good password practices

---

## Password Reset Process

### Admin-Generated Token Flow

```
1. User contacts admin (forgot password)
2. Admin logs into system
3. Admin goes to Users page
4. Admin generates reset token for user
5. Admin receives token (displayed in UI)
6. Admin shares token with user (phone/in-person)
7. User visits /reset-password?token=XXX
8. User enters new password
9. System validates token and updates password
10. User can now login with new password
```

### Token Properties

| Property | Value |
|----------|-------|
| Validity | 1 hour |
| Type | admin_generated |
| Case | Case-insensitive (stored uppercase) |
| Single use | Yes |

### Endpoints

| Endpoint | Description | Auth Required |
|----------|-------------|---------------|
| `POST /api/auth/admin/generate-reset-token` | Generate token | Admin |
| `POST /api/auth/reset-password-with-token` | Reset with token | No |
| `POST /api/auth/change-password` | Change own password | Yes |
| `GET /api/auth/check-password-strength` | Check strength | No |

---

## API Security

### Protected vs Public Endpoints

**Protected (require JWT):**
- All `/api/books` endpoints except public search
- All `/api/circulation/*` endpoints
- All `/api/users/*` endpoints
- Dashboard stats
- Digital library upload/edit/delete

**Public (no auth required):**
- `POST /api/auth/login`
- `POST /api/auth/reset-password-with-token`
- `GET /api/auth/check-password-strength`
- `GET /api/public/search`
- `GET /api/public/stats`
- `GET /api/digital-library` (list)
- `GET /api/digital-library/{id}` (details)
- `GET /api/digital-library/{id}/view` (view file)
- `GET /api/digital-library/{id}/download` (download file)
- `GET /api/digital-library/filters/*` (filter options)
- `GET /api/public/magazines`

### Security Best Practices

1. **Never expose secret key in code**
   ```python
   # In production, use environment variable
   SECRET_KEY = os.environ.get("SECRET_KEY", "default-dev-key")
   ```

2. **Always validate on backend**
   ```python
   # Frontend hiding is NOT security
   # Always validate in backend
   @router.delete("/books/{book_id}")
   async def delete_book(
       current_user: User = Depends(get_current_admin_user)  # Enforced!
   ):
   ```

3. **Use parameterized queries**
   ```python
   # Safe (SQLAlchemy ORM)
   books = db.query(Book).filter(Book.author == author_input).all()
   
   # Unsafe (never do this)
   db.execute(f"SELECT * FROM books WHERE author = '{author_input}'")
   ```

4. **Validate file uploads**
   ```python
   # Check file type, size
   if file.content_type != "application/pdf":
       raise HTTPException(400, "Only PDF allowed")
   if file.size > 50 * 1024 * 1024:  # 50MB
       raise HTTPException(413, "File too large")
   ```

5. **Sanitize user input**
   ```python
   # Use Pydantic validators
   class BookCreate(BaseModel):
       title: str = Field(..., min_length=1, max_length=500)
       acc_no: str = Field(..., regex=r'^[A-Z0-9-]+$')
   ```

---

## Frontend Authentication

### Token Storage

Tokens are stored in browser's localStorage:

```javascript
localStorage.setItem('access_token', response.access_token);
localStorage.setItem('user_role', response.role);
localStorage.setItem('user_id', response.user_id);
localStorage.setItem('username', response.username);
localStorage.setItem('full_name', response.full_name);
```

### Including Token in Requests

```javascript
const headers = {
    'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
    'Content-Type': 'application/json'
};

fetch('/api/books', {
    method: 'GET',
    headers: headers
});
```

### Role-Based UI

Frontend shows/hides elements based on role:

```html
<!-- Show to librarian and admin -->
<button x-show="isAdmin" @click="addBook()">Add Book</button>

<!-- Admin only -->
<button x-show="userRole === 'admin'" @click="deleteUser()">Delete</button>
```

**Note:** This is for UX only. Backend always enforces permissions.

---

## Logout Process

```
1. User clicks logout button
2. Frontend clears localStorage:
   - localStorage.removeItem('access_token')
   - localStorage.removeItem('user_role')
   - etc.
3. Frontend redirects to /login
4. Session is now invalidated (JWT still valid until expiration)
```

**Note:** JWT tokens are stateless - they cannot be invalidated server-side before expiration. For immediate logout in high-security scenarios, consider implementing a token blacklist.
