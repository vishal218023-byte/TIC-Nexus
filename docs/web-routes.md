# Web Routes & Template Mapping

This document lists all web page routes and their corresponding templates in TIC Nexus.

## Table of Contents
1. [Public Routes](#public-routes)
2. [Authentication Routes](#authentication-routes)
3. [Protected Routes](#protected-routes)
4. [Template to Route Mapping](#template-to-route-mapping)

---

## Public Routes

These routes are accessible without authentication.

| Route | Template | Description |
|-------|----------|-------------|
| `/` | `home_bulma.html` | Public homepage |
| `/login` | `login.html` | Login page |
| `/forgot-password` | `forgot_password.html` | Forgot password page |
| `/reset-password` | `reset_password.html` | Reset password page |
| `/public/digital-library` | `public_digital_library.html` | Public digital library browse |
| `/public/digital-library/view/{book_id}` | `public_digital_view.html` | Public digital book viewer |
| `/public/magazines` | `public_magazines.html` | Public magazines page |

---

## Authentication Routes

### Login Flow
1. User visits `/login`
2. Submits credentials to `POST /api/auth/login`
3. On success, JWT stored in localStorage
4. Redirects to `/dashboard`

### Password Reset Flow
1. User visits `/forgot-password`
2. Admin generates token via `POST /api/auth/admin/generate-reset-token`
3. Admin shares token with user (phone/in-person)
4. User visits `/reset-password?token={token}`
5. User submits new password via form
6. `POST /api/auth/reset-password-with-token` processes reset

---

## Protected Routes

These routes serve HTML but require client-side authentication (JWT in localStorage). The actual API endpoints enforce server-side authentication.

| Route | Template | Description | Required Role |
|-------|----------|-------------|---------------|
| `/dashboard` | `dashboard.html` | Dashboard with stats & charts | Any authenticated |
| `/inventory` | `inventory.html` | Book management (CRUD) | Librarian/Admin |
| `/circulation` | `circulation.html` | Issue/Return/Extend operations | Librarian/Admin |
| `/digital-library` | `digital_library_browse.html` | Digital library browse | Any authenticated |
| `/digital-library/{book_id}` | `digital_library_detail.html` | Digital book details | Any authenticated |
| `/magazines` | `magazines.html` | Magazine management | Librarian/Admin |
| `/users` | `users.html` | User management | Admin only |

---

## Template to Route Mapping

### Base Templates

| Template | Purpose |
|----------|---------|
| `base.html` | Base template with header/footer, includes navbar and sidebar |
| `sidebar.html` | Navigation sidebar with role-based menu items |

### Authentication Templates

| Template | Route | Purpose |
|----------|-------|---------|
| `login.html` | `/login` | User login form |
| `forgot_password.html` | `/forgot-password` | Request password reset |
| `reset_password.html` | `/reset-password` | Enter new password with token |
| `change_password_modal.html` | Included in other templates | Modal for changing password |

### Public Templates

| Template | Route | Purpose |
|----------|-------|---------|
| `home_bulma.html` | `/` | Public homepage with search |
| `navbar_public.html` | Included in public pages | Public navigation bar |
| `public_digital_library.html` | `/public/digital-library` | Browse digital books (public) |
| `public_digital_view.html` | `/public/digital-library/view/{id}` | View digital book (public) |
| `public_magazines.html` | `/public/magazines` | Browse magazines (public) |
| `error.html` | N/A (error handler) | Error page template |

### Protected Templates

| Template | Route | Purpose |
|----------|-------|---------|
| `dashboard.html` | `/dashboard` | Statistics dashboard with charts |
| `inventory.html` | `/inventory` | Physical book CRUD operations |
| `circulation.html` | `/circulation` | Issue/Return/Extend tabs |
| `digital_library_browse.html` | `/digital-library` | Digital library browsing |
| `digital_library_detail.html` | `/digital-library/{id}` | Digital book details |
| `digital_library.html` | N/A (legacy) | Legacy digital library page |
| `magazines.html` | `/magazines` | Magazine and vendor management |
| `users.html` | `/users` | User management (admin only) |

---

## Navigation Structure

### Public Navigation (Navbar)
```
TIC Nexus (Logo) → Home | Digital Library | Magazines | Login
```

### Protected Navigation (Sidebar)

**Common (All Roles):**
- Dashboard
- Digital Library

**Librarian/Admin:**
- Inventory
- Circulation
- Magazines

**Admin Only:**
- Users

---

## Frontend Architecture

### Alpine.js Patterns

The frontend uses Alpine.js for reactivity. Key patterns:

**Data Initialization:**
```javascript
async init() {
    // Load user info from localStorage
    this.isAdmin = localStorage.getItem('user_role') === 'admin' || 
                   localStorage.getItem('user_role') === 'librarian';
    this.userName = localStorage.getItem('full_name') || 
                    localStorage.getItem('username') || 'User';
    
    // Load initial data
    await this.loadBooks();
}
```

**API Calls:**
```javascript
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
```

### Role-Based UI Hiding

The frontend hides UI elements based on role, but this is NOT security. Backend always enforces permissions.

```html
<!-- Admin/Librarian only -->
<button x-show="isAdmin" @click="addBook()">Add Book</button>

<!-- Admin only -->
<button x-show="userRole === 'admin'" @click="deleteUser()">Delete User</button>
```

---

## Static Assets

### CSS
- `/static/css/` - Bulma, Tailwind, custom styles
- `/static/css/toast.css` - Toast notification styles

### JavaScript
- `/static/js/` - JavaScript utilities
- `/static/js/toast.js` - Toast notification system
- Alpine.js loaded from CDN

### Uploads
- `/static/uploads/magazines/` - Magazine cover images
- `/library_vault/digital_books/` - Digital book files

---

## Error Handling

### HTTP Error Handling
- API errors return JSON with `detail` field
- Web routes render `error.html` template
- Error codes: 400, 401, 403, 404, 500, etc.

### Client-Side Error Handling
```javascript
try {
    const response = await fetch('/api/books', {...});
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

### Toast Notifications
```javascript
window.toast.success('Book added successfully!', 3000);
window.toast.error('Failed to add book: ' + error.message, 5000);
window.toast.info('Processing your request...', 2000);
window.toast.warning('Book is already issued', 4000);
```
