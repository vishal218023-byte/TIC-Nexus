# API Routes Documentation

This document provides a comprehensive list of all API endpoints in TIC Nexus.

## Table of Contents
1. [Authentication API](#authentication-api)
2. [Dashboard API](#dashboard-api)
3. [Books API](#books-api)
4. [Circulation API](#circulation-api)
5. [Users API](#users-api)
6. [Digital Library API](#digital-library-api)
7. [Magazines API](#magazines-api)
8. [Public API](#public-api)

---

## Authentication API

### Login
**Endpoint:** `POST /api/auth/login`

Authenticates user and returns access token.

**Request Body (Form Data):**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| username | string | Yes | User's username |
| password | string | Yes | User's password |

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "role": "admin",
  "user_id": 1,
  "username": "admin",
  "full_name": "System Administrator"
}
```

**Errors:**
- 401: Incorrect username or password

---

### Change Password
**Endpoint:** `POST /api/auth/change-password`

Changes password for authenticated user.

**Headers:** `Authorization: Bearer <token>`

**Request Body (JSON):**
```json
{
  "current_password": "oldpassword123",
  "new_password": "newpassword456"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Password changed successfully"
}
```

**Errors:**
- 400: Current password is incorrect / New password must be different
- 401: Not authenticated

---

### Generate Reset Token (Admin)
**Endpoint:** `POST /api/auth/admin/generate-reset-token`

Generates password reset token for a user.

**Headers:** `Authorization: Bearer <token>`

**Request Body (JSON):**
```json
{
  "user_id": 5
}
```

**Response:**
```json
{
  "id": 1,
  "user_id": 5,
  "token": "ABC123XYZ",
  "expires_at": "2024-02-23T12:00:00",
  "is_used": false,
  "created_at": "2024-02-23T11:00:00"
}
```

**Errors:**
- 401: Not authenticated
- 403: Admin privileges required
- 404: User not found

---

### Reset Password with Token
**Endpoint:** `POST /api/auth/reset-password-with-token`

Resets password using a valid token (public endpoint).

**Request Body (JSON):**
```json
{
  "token": "ABC123XYZ",
  "new_password": "newpassword456"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Password has been reset successfully..."
}
```

**Errors:**
- 400: Invalid/expired token, user not found

---

### Check Password Strength
**Endpoint:** `GET /api/auth/check-password-strength?password=<password>`

Checks password strength (public endpoint).

**Response:**
```json
{
  "strength": "strong",
  "score": 85,
  "feedback": ["Password is strong"]
}
```

---

## Dashboard API

### Get Dashboard Stats
**Endpoint:** `GET /api/dashboard/stats`

Returns dashboard statistics.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "total_books": 1500,
  "total_issued": 45,
  "total_overdue": 5,
  "total_users": 25,
  "digital_library_count": 120
}
```

---

### Get Subject Distribution
**Endpoint:** `GET /api/dashboard/subject-distribution`

Returns top 10 subject distribution for charts.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
[
  {
    "subject": "Electronics",
    "count": 250
  },
  {
    "subject": "Computer Science",
    "count": 180
  }
]
```

---

## Books API

### List Books
**Endpoint:** `GET /api/books`

Returns list of books with optional filtering.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| search | string | Search by title, author, acc_no, isbn |
| subject | string | Filter by subject |
| is_issued | boolean | Filter by availability |
| language | string | Filter by language |
| skip | int | Pagination offset (default: 0) |
| limit | int | Pagination limit (default: 100, max: 500) |

**Response:** Array of Book objects
```json
[
  {
    "id": 1,
    "acc_no": "TIC-R-1-S-1",
    "title": "Introduction to Electronics",
    "author": "John Smith",
    "publisher_info": "ABC Publishers",
    "subject": "Electronics",
    "class_no": "621.3",
    "year": 2020,
    "isbn": "978-3-16-148410-0",
    "language": "English",
    "storage_loc": "TIC-R-1-S-1",
    "is_issued": false,
    "created_at": "2024-01-15T10:00:00",
    "updated_at": "2024-01-15T10:00:00",
    "digital_book_id": null
  }
]
```

---

### Get Available Books
**Endpoint:** `GET /api/books/available`

Returns books with availability status for issuing.

**Headers:** `Authorization: Bearer <token>`

**Required Role:** Librarian or Admin

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| search | string | Search by acc_no, title, author |
| skip | int | Pagination offset |
| limit | int | Pagination limit |

**Response:** Array of books with availability
```json
[
  {
    "id": 1,
    "acc_no": "TIC-R-1-S-1",
    "title": "Introduction to Electronics",
    "author": "John Smith",
    "subject": "Electronics",
    "class_no": "621.3",
    "year": 2020,
    "isbn": "978-3-16-148410-0",
    "storage_loc": "TIC-R-1-S-1",
    "is_issued": false,
    "can_issue": true,
    "is_reference": false,
    "digital_book_id": null,
    "created_at": "2024-01-15T10:00:00",
    "updated_at": "2024-01-15T10:00:00"
  }
]
```

---

### Get Single Book
**Endpoint:** `GET /api/books/{book_id}`

Returns a specific book by ID.

**Headers:** `Authorization: Bearer <token>`

**Response:** Book object

**Errors:**
- 404: Book not found

---

### Create Book
**Endpoint:** `POST /api/books`

Creates a new book.

**Headers:** `Authorization: Bearer <token>`

**Required Role:** Librarian or Admin

**Request Body (JSON):**
```json
{
  "acc_no": "TIC-R-1-S-5",
  "title": "New Book Title",
  "author": "Author Name",
  "publisher_info": "Publisher Name",
  "subject": "Subject Name",
  "class_no": "620",
  "year": 2024,
  "isbn": "978-1-23-456789-0",
  "language": "English",
  "storage_loc": "TIC-R-1-S-5"
}
```

**Response:** Created book object

**Errors:**
- 400: Book with accession number already exists

---

### Update Book
**Endpoint:** `PUT /api/books/{book_id}`

Updates a book.

**Headers:** `Authorization: Bearer <token>`

**Required Role:** Admin only

**Request Body (JSON):** Same as Create, all fields optional

**Response:** Updated book object

**Errors:**
- 404: Book not found

---

### Delete Book
**Endpoint:** `DELETE /api/books/{book_id}`

Deletes a book.

**Headers:** `Authorization: Bearer <token>`

**Required Role:** Admin only

**Response:**
```json
{
  "message": "Book deleted successfully"
}
```

**Errors:**
- 400: Cannot delete a book that is currently issued
- 404: Book not found

---

### Get Languages
**Endpoint:** `GET /api/languages`

Returns unique languages for filtering.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
["English", "Hindi", "Telugu", "Tamil"]
```

---

### Get Subjects
**Endpoint:** `GET /api/subjects`

Returns unique subjects for filtering.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
["Electronics", "Computer Science", "Mathematics", "Physics"]
```

---

## Circulation API

### Issue Book
**Endpoint:** `POST /api/circulation/issue`

Issues a book to a user.

**Headers:** `Authorization: Bearer <token>`

**Required Role:** Librarian or Admin

**Request Body (Form Data):**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| book_id | int | Yes | Book ID |
| user_id | int | Yes | User ID |
| days | int | No | Loan period (default: 14, max: 90) |
| notes | string | No | Any notes |

**Response:**
```json
{
  "message": "Book issued successfully",
  "transaction_id": 123
}
```

**Errors:**
- 400: Book already issued / Reference only book / Maximum extension limit reached
- 404: Book or User not found

---

### Return Book
**Endpoint:** `POST /api/circulation/return`

Returns a book.

**Headers:** `Authorization: Bearer <token>`

**Required Role:** Librarian or Admin

**Request Body (Form Data):**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| transaction_id | int | Yes | Transaction ID |
| notes | string | No | Any notes |

**Response:**
```json
{
  "message": "Book returned successfully",
  "transaction_id": 123
}
```

**Errors:**
- 400: Book already returned
- 404: Transaction not found

---

### Extend Book
**Endpoint:** `POST /api/circulation/extend`

Extends book's due date by 7 days.

**Headers:** `Authorization: Bearer <token>`

**Required Role:** Librarian or Admin

**Request Body (Form Data):**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| transaction_id | int | Yes | Transaction ID |

**Response:**
```json
{
  "message": "Book extended successfully (Extension 1/2)",
  "new_due_date": "2024-03-15T10:00:00"
}
```

**Errors:**
- 400: Maximum extension limit (2) reached / Cannot extend returned book
- 404: Transaction not found

---

### List Transactions
**Endpoint:** `GET /api/transactions`

Returns all transactions.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| status_filter | string | Filter by status (Issued, Returned, Overdue) |
| user_id | int | Filter by user |
| book_id | int | Filter by book |
| skip | int | Pagination offset |
| limit | int | Pagination limit |

**Response:** Array of transactions with details
```json
[
  {
    "id": 1,
    "book_id": 5,
    "user_id": 3,
    "book_acc_no": "TIC-R-1-S-1",
    "book_title": "Book Title",
    "book_author": "Author Name",
    "user_name": "John Doe",
    "user_username": "johnd",
    "issue_date": "2024-02-01T10:00:00",
    "due_date": "2024-02-15T10:00:00",
    "return_date": null,
    "extension_count": 0,
    "status": "Issued",
    "notes": null,
    "is_overdue": false,
    "is_due_soon": false,
    "days_until_due": 10
  }
]
```

---

### List Active Transactions
**Endpoint:** `GET /api/transactions/active`

Returns active (Issued/Overdue) transactions.

**Headers:** `Authorization: Bearer <token>`

**Required Role:** Librarian or Admin

**Response:** Array similar to List Transactions

---

### List Extendable Transactions
**Endpoint:** `GET /api/transactions/extendable`

Returns transactions with extendability status.

**Headers:** `Authorization: Bearer <token>`

**Required Role:** Librarian or Admin

**Response:** Array with additional fields:
```json
{
  "remaining_extensions": 2,
  "can_extend": true,
  "new_due_date": "2024-03-15T10:00:00"
}
```

---

### Update Overdue Status
**Endpoint:** `POST /api/circulation/update-overdue`

Manually updates overdue status for all transactions.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "message": "Updated 5 transaction(s) to overdue status",
  "updated_count": 5
}
```

---

## Users API

### Get Current User
**Endpoint:** `GET /api/user/me`

Returns current logged-in user information.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@bel.in",
  "full_name": "System Administrator",
  "role": "admin",
  "is_active": true
}
```

---

### List Users
**Endpoint:** `GET /api/users`

Returns all users.

**Headers:** `Authorization: Bearer <token>`

**Required Role:** Admin only

**Response:** Array of user objects
```json
[
  {
    "id": 1,
    "username": "admin",
    "email": "admin@bel.in",
    "full_name": "System Administrator",
    "role": "admin",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00"
  }
]
```

---

### Create User
**Endpoint:** `POST /api/users`

Creates a new user.

**Headers:** `Authorization: Bearer <token>`

**Required Role:** Admin only

**Request Body (Form Data):**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| username | string | Yes | Unique username (min 3 chars) |
| email | string | Yes | Unique email |
| password | string | Yes | Password (min 6 chars) |
| full_name | string | Yes | User's full name |
| role | string | Yes | admin, librarian, or viewer |

**Response:** Created user object

**Errors:**
- 400: Username/Email already exists / Invalid role

---

### Update User
**Endpoint:** `PUT /api/users/{user_id}`

Updates a user.

**Headers:** `Authorization: Bearer <token>`

**Required Role:** Admin only

**Request Body (Form Data):** All fields optional
| Parameter | Type | Description |
|-----------|------|-------------|
| email | string | New email |
| full_name | string | New full name |
| role | string | New role |
| is_active | boolean | Account status |
| password | string | New password |

**Response:** Updated user object

**Errors:**
- 400: Cannot deactivate your own account / Email already exists
- 404: User not found

---

### Delete User
**Endpoint:** `DELETE /api/users/{user_id}`

Deletes a user.

**Headers:** `Authorization: Bearer <token>`

**Required Role:** Admin only

**Response:**
```json
{
  "message": "User deleted successfully"
}
```

**Errors:**
- 400: Cannot delete your own account / User has active transactions
- 404: User not found

---

## Digital Library API

### List Digital Books
**Endpoint:** `GET /api/digital-library`

Returns digital books with optional filtering. **Public access allowed.**

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| search | string | Search by title, author, isbn, description |
| subject | string | Filter by subject |
| category | string | Filter by category |
| language | string | Filter by language |
| file_format | string | Filter by format (pdf, epub, mobi) |
| skip | int | Pagination offset |
| limit | int | Pagination limit |

**Response:** Array of digital book objects
```json
[
  {
    "id": 1,
    "title": "Digital Book Title",
    "author": "Author Name",
    "file_path": "filename.pdf",
    "file_size": 5242880,
    "file_format": "pdf",
    "publisher": "Publisher Name",
    "publication_year": 2023,
    "isbn": "978-1-23-456789-0",
    "subject": "Computer Science",
    "description": "Book description",
    "language": "English",
    "category": "Textbook",
    "tags": "programming, python, basics",
    "view_count": 150,
    "download_count": 45,
    "uploaded_by": 1,
    "created_at": "2024-01-15T10:00:00",
    "updated_at": "2024-01-15T10:00:00"
  }
]
```

---

### Get Digital Book Details
**Endpoint:** `GET /api/digital-library/{digital_book_id}`

Returns digital book with full details. **Public access allowed.**

**Response:** Extended digital book object
```json
{
  "id": 1,
  "title": "Digital Book Title",
  "author": "Author Name",
  ...
  "uploader_name": "System Administrator",
  "linked_physical_books": [
    {
      "link_id": 1,
      "book_id": 5,
      "acc_no": "TIC-R-1-S-1",
      "title": "Physical Book Title",
      "author": "Author Name",
      "storage_loc": "TIC-R-1-S-1",
      "is_issued": false,
      "link_type": "same_edition"
    }
  ]
}
```

---

### Upload Digital Book
**Endpoint:** `POST /api/digital-library`

Uploads a new digital book.

**Headers:** `Authorization: Bearer <token>`

**Required Role:** Librarian or Admin

**Request Body (Form Data):**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| title | string | Yes | Book title |
| author | string | Yes | Author name |
| file | file | Yes | PDF/EPUB/MOBI file |
| publisher | string | No | Publisher |
| publication_year | int | No | Year |
| isbn | string | No | ISBN |
| subject | string | No | Subject |
| description | string | No | Description |
| language | string | No | Language (default: English) |
| category | string | No | Category |
| tags | string | No | Comma-separated tags |

**Response:** Created digital book object

**Errors:**
- 400: Invalid file format

---

### Update Digital Book
**Endpoint:** `PUT /api/digital-library/{digital_book_id}`

Updates digital book metadata.

**Headers:** `Authorization: Bearer <token>`

**Required Role:** Librarian or Admin

**Request Body (Form Data):** All fields optional

**Response:** Updated digital book object

---

### Delete Digital Book
**Endpoint:** `DELETE /api/digital-library/{digital_book_id}`

Deletes digital book and file.

**Headers:** `Authorization: Bearer <token>`

**Required Role:** Admin only

**Response:**
```json
{
  "message": "Digital book and file deleted successfully"
}
```

---

### View Digital Book
**Endpoint:** `GET /api/digital-library/{digital_book_id}/view`

Streams file for in-browser viewing. **Public access allowed.**

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| token | string | Optional JWT for auth (via query) |

**Response:** File stream (PDF, EPUB, MOBI)

**Side Effects:** Increments view_count

---

### Download Digital Book
**Endpoint:** `GET /api/digital-library/{digital_book_id}/download`

Downloads digital book file. **Public access allowed.**

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| token | string | Optional JWT for auth (via query) |

**Response:** File download

**Side Effects:** Increments download_count

---

### Get Digital Library Stats
**Endpoint:** `GET /api/digital-library/stats/overview`

Returns digital library statistics.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "total_books": 120,
  "total_views": 5000,
  "total_downloads": 1500,
  "by_format": [
    {"format": "pdf", "count": 100},
    {"format": "epub", "count": 20}
  ],
  "by_category": [
    {"category": "Textbook", "count": 80}
  ],
  "top_subjects": [
    {"subject": "Computer Science", "count": 50}
  ]
}
```

---

### Get Categories
**Endpoint:** `GET /api/digital-library/filters/categories`

Returns unique categories. **Public access allowed.**

**Response:** Array of category strings

---

### Get Subjects
**Endpoint:** `GET /api/digital-library/filters/subjects`

Returns unique subjects. **Public access allowed.**

**Response:** Array of subject strings

---

### Get Languages
**Endpoint:** `GET /api/digital-library/filters/languages`

Returns unique languages. **Public access allowed.**

**Response:** Array of language strings

---

### Link Physical to Digital Book
**Endpoint:** `POST /api/digital-library/links`

Links a physical book to a digital book.

**Headers:** `Authorization: Bearer <token>`

**Required Role:** Librarian or Admin

**Request Body (JSON):**
```json
{
  "book_id": 5,
  "digital_book_id": 10,
  "link_type": "same_edition",
  "notes": "Optional notes"
}
```

**Response:** Link object

---

### Get Digital Book Links
**Endpoint:** `GET /api/digital-library/links/{digital_book_id}`

Returns all physical book links for a digital book.

**Headers:** `Authorization: Bearer <token>`

**Response:** Array of link objects

---

### Delete Link
**Endpoint:** `DELETE /api/digital-library/links/{link_id}`

Deletes a book-digital link.

**Headers:** `Authorization: Bearer <token>`

**Required Role:** Admin only

---

### Find Digital by Physical
**Endpoint:** `GET /api/digital-library/search/by-physical-book/{book_id}`

Finds digital books linked to a physical book.

**Headers:** `Authorization: Bearer <token>`

**Response:** Array of digital books with link info

---

## Magazines API

### Create Vendor
**Endpoint:** `POST /api/vendors`

Creates a new vendor.

**Headers:** `Authorization: Bearer <token>`

**Required Role:** Admin only

**Request Body (JSON):**
```json
{
  "name": "Vendor Name",
  "contact_details": "Contact info"
}
```

**Response:** Vendor object

---

### List Vendors
**Endpoint:** `GET /api/vendors`

Returns all vendors.

**Headers:** `Authorization: Bearer <token>`

**Response:** Array of vendor objects

---

### Create Magazine
**Endpoint:** `POST /api/magazines`

Creates a new magazine master record.

**Headers:** `Authorization: Bearer <token>`

**Required Role:** Librarian or Admin

**Request Body (Form Data):**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| title | string | Yes | Magazine title |
| language | string | No | Language (default: English) |
| frequency | string | No | Monthly, Weekly, etc. |
| category | string | No | Category |
| cover_image | file | No | Cover image |

**Response:** Magazine object

---

### List Magazines
**Endpoint:** `GET /api/magazines`

Returns magazines with filtering.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| q | string | Search query |
| language | string | Filter by language |
| frequency | string | Filter by frequency |
| category | string | Filter by category |

**Response:** Array of magazine objects

---

### Get Magazine Filters
**Endpoint:** `GET /api/magazines/filters/languages`

Returns unique magazine languages.

**Headers:** `Authorization: Bearer <token>**

**Response:** Array of language strings

Similar endpoints exist for:
- `/api/magazines/filters/frequencies`
- `/api/magazines/filters/categories`

---

### Update Magazine
**Endpoint:** `PUT /api/magazines/{magazine_id}`

Updates magazine details.

**Headers:** `Authorization: Bearer <token>`

**Required Role:** Librarian or Admin

**Request Body (JSON):** All fields optional

**Response:** Updated magazine object

---

### Upload Magazine Cover
**Endpoint:** `POST /api/magazines/{magazine_id}/upload-cover`

Uploads/replaces magazine cover.

**Headers:** `Authorization: Bearer <token>`

**Required Role:** Librarian or Admin

**Request Body:** Form data with cover_image file

---

### Log Magazine Issue
**Endpoint:** `POST /api/magazines/issues`

Logs a received magazine issue.

**Headers:** `Authorization: Bearer <token>`

**Required Role:** Librarian or Admin

**Request Body (JSON):**
```json
{
  "magazine_id": 1,
  "issue_description": "January 2024",
  "received_date": "2024-01-15",
  "vendor_id": 1,
  "remarks": "Optional remarks"
}
```

**Response:** Issue object

---

### Get Magazine Issues
**Endpoint:** `GET /api/magazines/{magazine_id}/issues`

Returns issues for a magazine.

**Headers:** `Authorization: Bearer <token>`

**Response:** Array of issue objects with vendor_name

---

### Get Public Magazines
**Endpoint:** `GET /api/public/magazines`

Public endpoint to list active magazines.

**Response:** Array of magazines with recent issues

---

## Public API

### Public Search
**Endpoint:** `GET /api/public/search?q=<query>`

Public search for books.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| q | string | Yes | Search query |

**Response:** Array of books (limited to 20)
```json
[
  {
    "id": 1,
    "title": "Book Title",
    "author": "Author Name",
    "acc_no": "TIC-R-1-S-1",
    "isbn": "978-...",
    "subject": "Subject",
    "language": "English",
    "is_issued": false,
    "digital_book_id": 5,
    "digital_book_format": "pdf"
  }
]
```

---

### Public Stats
**Endpoint:** `GET /api/public/stats`

Public statistics endpoint.

**Response:**
```json
{
  "total_books": 1500,
  "available_books": 1455,
  "digital_library_count": 120,
  "subjects_count": 25
}
```
