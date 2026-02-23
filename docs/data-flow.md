# Data Flow

This document explains how data flows through the TIC Nexus application.

## Table of Contents
1. [Request-Response Flow](#request-response-flow)
2. [Authentication Flow](#authentication-flow)
3. [Book Circulation Flow](#book-circulation-flow)
4. [Digital Library Flow](#digital-library-flow)
5. [Password Reset Flow](#password-reset-flow)
6. [Frontend-Backend Communication](#frontend-backend-communication)

---

## Request-Response Flow

### Typical API Request Flow

```
┌─────────┐     ┌─────────────┐     ┌──────────────┐     ┌──────────┐
│ Client  │────►│   FastAPI   │────►│  Dependency  │────►│ Database │
│ (Browser)│    │   (app)    │     │  (auth.py)   │     │ (SQLite) │
└─────────┘     └─────────────┘     └──────────────┘     └──────────┘
      │                │                     │                   │
      │                │                     │                   │
      │         ┌──────▼──────┐             │                   │
      │         │   Route     │◄─────────────┘                   │
      │         │ (routes.py) │                                 │
      │         └──────┬──────┘                                 │
      │                │                                          │
      │         ┌──────▼──────┐                                  │
      │         │  Business   │◄──────────────────────────────────┘
      │         │  Logic      │
      │         │(circulation)│
      │         └──────┬──────┘
      │                │
      │         ┌──────▼──────┐
      │         │  Response   │
      └─────────│  (JSON)    │
                └─────────────┘
```

### Request Processing Steps

1. **Request Received**: FastAPI receives HTTP request
2. **Route Matching**: FastAPI matches URL to route handler
3. **Dependency Injection**: Auth dependencies validate token
4. **Schema Validation**: Pydantic validates request body
5. **Business Logic**: Application logic processes data
6. **Database Operation**: SQLAlchemy performs CRUD
7. **Response**: JSON response sent to client

---

## Authentication Flow

### Login Flow

```
┌─────────┐     ┌─────────────┐     ┌──────────────┐     ┌──────────┐
│  User   │     │  Login UI   │     │  /api/auth/  │     │ Database │
│ enters  │────►│  (form)     │────►│   login      │────►│          │
│credentials   │             │     │             │     │          │
└─────────┘     └─────────────┘     └──────────────┘     └──────────┘
                                             │                   │
                                             │                   │
                                      ┌──────▼──────┐            │
                                      │  authenticate│            │
                                      │  _user()    │◄───────────┘
                                      │ (auth.py)   │
                                      └──────┬──────┘
                                             │
                                      ┌──────▼──────┐
                                      │  JWT Token  │
                                      │  Created    │
                                      └─────────────┘
                                             │
                                             ▼
                                      ┌─────────────┐
                                      │  Response:  │
                                      │  token,     │
                                      │  role,      │
                                      │  user info  │
                                      └─────────────┘
                                             │
                                             ▼
                                      ┌─────────────┐
                                      │  Browser    │
                                      │  stores     │
                                      │  in         │
                                      │  localStorage│
                                      └─────────────┘
```

### JWT Token Structure

```json
{
  "sub": "username",
  "exp": 1234567890,
  "iat": 1234567890
}
```

**Token Details:**
- Algorithm: HS256
- Expiration: 8 hours (480 minutes)
- Storage: localStorage (client-side)

### Protected API Call Flow

```
┌─────────┐     ┌─────────────┐     ┌──────────────┐     ┌──────────┐
│ Request │     │  Include    │     │   OAuth2    │     │ Database │
│ to API  │────►│  Bearer     │────►│   Scheme    │────►│  Validate│
│ endpoint│    │  Token      │     │  (auth.py)  │     │  Token   │
└─────────┘     └─────────────┘     └──────────────┘     └──────────┘
                                                      │          
                                                      │  ┌──────▼──────┐
                                                      │  │ get_current │
                                                      │  │ _user()     │
                                                      │  └──────┬──────┘
                                                      │         │
                                                      │  ┌──────▼──────┐
                                                      │  │ Return User │
                                                      │  │  or 401     │
                                                      │  └─────────────┘
```

---

## Book Circulation Flow

### Issue Book Flow

```
┌─────────────┐     ┌─────────────────┐     ┌──────────────┐
│ Librarian   │     │  POST /api/    │     │  circulation │
│ selects     │────►│  circulation/   │────►│  .issue_book│
│ book & user │     │  issue          │     │  (function)  │
└─────────────┘     └─────────────────┘     └──────┬───────┘
                                                    │
                                           ┌────────▼────────┐
                                           │  Validate:      │
                                           │  1. Book exists │
                                           │  2. Not issued  │
                                           │  3. Not ref only│
                                           │  4. User exists │
                                           └────────┬────────┘
                                                    │
                                           ┌────────▼────────┐
                                           │  Create         │
                                           │  Transaction    │
                                           │  + Update Book  │
                                           └────────┬────────┘
                                                    │
                                           ┌────────▼────────┐
                                           │  Return         │
                                           │  transaction    │
                                           │  ID             │
                                           └─────────────────┘
```

### Return Book Flow

```
┌─────────────┐     ┌─────────────────┐     ┌──────────────┐
│ Librarian   │     │  POST /api/    │     │  circulation │
│ enters     │────►│  circulation/   │────►│  .retrieve_  │
│ trans ID   │     │  return         │     │  book()      │
└─────────────┘     └─────────────────┘     └──────┬───────┘
                                                    │
                                           ┌────────▼────────┐
                                           │  Validate:     │
                                           │  1. Transaction│
                                           │     exists     │
                                           │  2. Not already│
                                           │     returned   │
                                           └────────┬────────┘
                                                    │
                                           ┌────────▼────────┐
                                           │  Update:        │
                                           │  1. Return date │
                                           │  2. Status =    │
                                           │     Returned    │
                                           │  3. Book.       │
                                           │     is_issued   │
                                           │     = False    │
                                           └─────────────────┘
```

### Extend Book Flow

```
┌─────────────┐     ┌─────────────────┐     ┌──────────────┐
│ Librarian   │     │  POST /api/    │     │  circulation │
│ selects   │────►│  circulation/   │────►│  .extend_    │
│ transaction│     │  extend         │     │  book()      │
└─────────────┘     └─────────────────┘     └──────┬───────┘
                                                    │
                                           ┌────────▼────────┐
                                           │  Validate:      │
                                           │  1. Transaction│
                                           │     exists     │
                                           │  2. Not        │
                                           │     returned   │
                                           │  3. Extensions│
                                           │     < 2        │
                                           └────────┬────────┘
                                                    │
                                           ┌────────▼────────┐
                                           │  Update:        │
                                           │  1. due_date   │
                                           │     += 7 days  │
                                           │  2. extension  │  
                                           │     _count++   │
                                           └─────────────────┘
```

---

## Digital Library Flow

### Upload Digital Book

```
┌─────────────┐     ┌─────────────────────┐     ┌──────────────┐
│ Librarian  │     │  POST /api/        │     │  Validate   │
│ selects   │────►│  digital-library   │────►│  file format│
│ PDF file  │     │  (multipart/form)  │     │  (PDF/EPUB/ │
│           │     │                     │     │   MOBI)      │
└─────────────┘     └─────────────────────┘     └──────┬───────┘
                                                        │
                                               ┌────────▼────────┐
                                               │  Save file to   │
                                               │  library_vault/ │
                                               │  digital_books/ │
                                               └────────┬────────┘
                                                        │
                                               ┌────────▼────────┐
                                               │  Create        │
                                               │  DigitalBook   │
                                               │  record        │
                                               └────────┬────────┘
                                                        │
                                               ┌────────▼────────┐
                                               │  Return        │
                                               │  DigitalBook   │
                                               │  object        │
                                               └────────────────┘
```

### View/Download Digital Book

```
┌─────────┐     ┌─────────────────────┐     ┌──────────────┐
│ User    │     │  GET /api/         │     │  Find file  │
│ clicks │────►│  digital-library   │────►│  in vault   │
│ view/  │     │  /{id}/view        │     │              │
│ download│    │  or /download      │     └──────┬───────┘
└─────────┘     └─────────────────────┘            │
                                                     │  ┌────────▼────────┐
                                                     │  │  Increment     │
                                                     │  │  view_count or │
                                                     │  │  download_     │
                                                     │  │  count         │
                                                     │  └────────┬───────┘
                                                     │           │
                                                     └───────────▼───────────┐
                                                                             │
                                                              ┌──────────────┐
                                                              │  Stream file │
                                                              │  to browser  │
                                                              │  (FileResponse)│
                                                              └──────────────┘
```

---

## Password Reset Flow

```
┌─────────┐     ┌─────────────────────┐     ┌──────────────┐
│ Admin   │     │  POST /api/auth/    │     │  Validate:  │
│ selects │────►│  admin/generate-    │────►│  1. User    │
│ user    │     │  reset-token        │     │     exists   │
│         │     │                     │     │  2. Active   │
└─────────┘     └─────────────────────┘     └──────┬───────┘
                                                    │
                                           ┌────────▼────────┐
                                           │  Create token  │
                                           │  + Store in DB │
                                           └────────┬────────┘
                                                    │
                                           ┌────────▼────────┐
                                           │  Return token   │
                                           │  to admin      │
                                           └─────────────────┘
                                                    │
                         ┌───────────────────────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │  Admin shares      │
              │  token with user  │
              │  (phone/in-person) │
              └─────────────────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │  User visits       │
              │  /reset-password   │
              │  ?token=XXX       │
              └─────────────────────┘
                         │
                         ▼
              ┌─────────────────────┐     ┌──────────────┐
              │  POST /api/auth/   │     │  Validate:  │
              │  reset-password   │────►│  1. Token    │
              │  -with-token      │     │     valid    │
              └─────────────────────┘     └──────┬───────┘
                                                  │
                                         ┌────────▼────────┐
                                         │  Update         │
                                         │  password +     │
                                         │  Mark token     │
                                         │  as used       │
                                         └─────────────────┘
```

---

## Frontend-Backend Communication

### API Communication Pattern

```javascript
// 1. Prepare headers with JWT
const headers = {
    'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
    'Content-Type': 'application/json'
};

// 2. Make API call
const response = await fetch('/api/books', {
    method: 'GET',
    headers: headers
});

// 3. Handle response
if (response.ok) {
    const data = await response.json();
    // Process data
} else {
    const error = await response.json();
    // Show error toast
    window.toast.error(error.detail);
}
```

### Data Flow: Display Books

```
┌─────────┐     ┌─────────────┐     ┌──────────────┐     ┌──────────┐
│ Page    │     │  Fetch API  │     │   Return     │     │ Display  │
│ loads   │────►│  /api/books │────►│  JSON array  │────►│ in table │
│         │     │             │     │  of books    │     │          │
└─────────┘     └─────────────┘     └──────────────┘     └──────────┘
     │                │                     │                   │
     │          ┌─────▼──────────┐    ┌─────▼──────────┐     │
     │          │ Send request   │    │ Transform to  │     │
     │          │ with JWT token │    │ Book objects  │     │
     │          └────────────────┘    └────────────────┘     │
     │                                                         │
     │    ┌─────────────────────────────────────────────────────┘
     │    │
     ▼    ▼
┌─────────────────────────────────────────┐
│          Alpine.js Data                │
│  {                                      │
│    books: [],                           │
│    loading: false,                      │
│    async loadBooks() {...}             │
│  }                                      │
└─────────────────────────────────────────┘
```

### Data Flow: Create Book

```
┌─────────┐     ┌─────────────┐     ┌──────────────┐     ┌──────────┐
│ User    │     │  POST /api  │     │  Validate & │     │ Database │
│ submits │────►│  /books     │────►│  Create     │────►│ Create   │
│ form    │     │  (JSON)     │     │  Book       │     │ Record   │
└─────────┘     └─────────────┘     └──────────────┘     └──────────┘
      │                │                     │                   │
      │          ┌─────▼──────────┐    ┌─────▼──────────┐     │
      │          │ Include JWT    │    │ Validate with │     │
      │          │ in Authorization│    │ BookCreate    │     │
      │          │ header         │    │ Schema        │     │
      │          └────────────────┘    └────────────────┘     │
      │                                                       │
      │    ┌──────────────────────────────────────────────────┘
      │    │
      ▼    ▼
┌─────────────────────────────────────────┐
│       Alpine.js Updates                 │
│  {                                      │
│    await this.loadBooks();             │
│    window.toast.success('Created!');   │
│    this.closeModal();                  │
│  }                                      │
└─────────────────────────────────────────┘
```

---

## Error Handling Flow

```
┌─────────┐     ┌─────────────┐     ┌──────────────┐
│ Request │     │  Business   │     │   HTTP       │
│ received│────►│  Logic      │────►│  Exception   │
│         │     │  raises     │     │  raised      │
└─────────┘     └─────────────┘     └──────┬───────┘
                                           │
                                          ┌▼────────┐
                                          │ FastAPI │
                                          │ catches │
                                          └────┬────┘
                                               │
                              ┌────────────────┴────────────────┐
                              │                                 │
                              ▼                                 ▼
                    ┌─────────────────┐             ┌─────────────────┐
                    │ API Route       │             │ Web Route       │
                    │ (/api/*)        │             │ (*)             │
                    └────────┬────────┘             └────────┬────────┘
                             │                                 │
                             ▼                                 ▼
                   ┌─────────────────┐             ┌─────────────────┐
                   │ Return JSON:    │             │ Render          │
                   │ {detail: "...} │             │ error.html      │
                   └─────────────────┘             └─────────────────┘
```
