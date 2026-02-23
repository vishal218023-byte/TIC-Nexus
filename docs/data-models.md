# Database Models

This document describes the database schema and table relationships in TIC Nexus.

## Table of Contents
1. [Entity Relationship Diagram](#entity-relationship-diagram)
2. [User Table](#user-table)
3. [Book Table](#book-table)
4. [Transaction Table](#transaction-table)
5. [DigitalBook Table](#digitalbook-table)
6. [BookDigitalLink Table](#bookdigitallink-table)
7. [PasswordResetToken Table](#passwordresettoken-table)
8. [PasswordHistory Table](#passwordhistory-table)
9. [Vendor Table](#vendor-table)
10. [Magazine Table](#magazine-table)
11. [MagazineIssue Table](#magazineissue-table)

---

## Entity Relationship Diagram

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│    User     │       │    Book     │       │DigitalBook  │
├─────────────┤       ├─────────────┤       ├─────────────┤
│ id (PK)     │◄──┐   │ id (PK)     │       │ id (PK)     │
│ username    │   │   │ acc_no      │       │ title       │
│ email       │   │   │ author      │       │ author      │
│ password    │   │   │ title       │       │ file_path   │
│ full_name   │   │   │ is_issued   │       │ view_count  │
│ role        │   │   └──────┬──────┘       │ download_cnt│
│ is_active   │   │          │              └──────┬──────┘
└──────┬──────┘   │          │                     │
       │          │          │                     │
       │    ┌─────▼─────┐    │              ┌──────▼──────┐
       │    │Transaction│    │              │BookDigital  │
       │    ├──────────┤    │              │   Link      │
       │    │ id (PK)  │    │              ├─────────────┤
       └───►│ book_id  │◄───┘              │ id (PK)     │
            │ user_id  │◄─────────────────│ book_id (FK)│
            │ status   │                   │ digital_id  │
            │ due_date │                   └─────────────┘
            └──────────┘
                  │
            ┌─────▼─────┐
            │ Password  │
            │  History  │
            └──────────┘
```

---

## User Table

Stores user accounts for authentication and authorization.

| Column | Type | Constraints | Description |
|--------|------|--------------|-------------|
| id | Integer | PK, Auto-increment | Unique user ID |
| username | String(50) | Unique, Not Null, Index | Login username |
| email | String(100) | Unique, Not Null | User email |
| hashed_password | String(255) | Not Null | Bcrypt hashed password |
| full_name | String(100) | Not Null | User's full name |
| role | String(20) | Not Null, Default='viewer' | User role: admin, librarian, viewer |
| is_active | Boolean | Default=True | Account active status |
| created_at | DateTime | Default=utcnow | Account creation timestamp |

**Relationships:**
- One-to-Many with Transaction (a user can have many transactions)
- One-to-Many with PasswordHistory
- One-to-Many with PasswordResetToken

---

## Book Table

Stores physical book inventory.

| Column | Type | Constraints | Description |
|--------|------|--------------|-------------|
| id | Integer | PK, Auto-increment | Unique book ID |
| acc_no | String(50) | Unique, Not Null, Index | Accession number (e.g., TIC-R-1-S-1) |
| author | Text | Not Null | Book author |
| title | Text | Not Null | Book title |
| publisher_info | Text | Nullable | Publisher details |
| subject | Text | Nullable | Subject/category |
| class_no | String(50) | Nullable | Classification number |
| year | Integer | Nullable | Publication year |
| isbn | String(20) | Nullable | ISBN number |
| language | String(50) | Nullable, Default='English' | Book language |
| storage_loc | String(50) | Not Null | Storage location (format: TIC-[RC]-#-S-#) |
| is_issued | Boolean | Default=False | Current availability |
| created_at | DateTime | Default=utcnow | Creation timestamp |
| updated_at | DateTime | Default=utcnow, Auto-update | Last modification |

**Relationships:**
- One-to-Many with Transaction
- One-to-Many with BookDigitalLink

**Storage Location Format:**
- Format: `TIC-[RC]-{rack_number}-S-{shelf_number}`
- Examples: `TIC-R-1-S-5`, `TIC-C-2-S-3`
- R = Rack, C = Cabinet

---

## Transaction Table

Tracks book circulation (issue/return/extend).

| Column | Type | Constraints | Description |
|--------|------|--------------|-------------|
| id | Integer | PK, Auto-increment | Unique transaction ID |
| book_id | Integer | FK → Book.id, Not Null | Book being borrowed |
| user_id | Integer | FK → User.id, Not Null | User borrowing |
| issue_date | DateTime | Default=utcnow | Date issued |
| due_date | DateTime | Not Null | Due date for return |
| return_date | DateTime | Nullable | Actual return date |
| extension_count | Integer | Default=0 | Number of extensions (max 2) |
| status | String(20) | Not Null, Default='Issued' | Status: Issued, Returned, Overdue |
| notes | Text | Nullable | Any notes |
| created_at | DateTime | Default=utcnow | Creation timestamp |

**Relationships:**
- Many-to-One with Book
- Many-to-One with User

**Status Values:**
- `Issued` - Currently borrowed
- `Returned` - Successfully returned
- `Overdue` - Past due date

**Business Rules:**
- Default loan period: 14 days
- Maximum extensions: 2
- Extension adds: 7 days per extension

---

## DigitalBook Table

Stores digital library resources (independent of physical books).

| Column | Type | Constraints | Description |
|--------|------|--------------|-------------|
| id | Integer | PK, Auto-increment | Unique digital book ID |
| title | Text | Not Null, Index | Book title |
| author | Text | Not Null, Index | Book author |
| file_path | Text | Not Null | Filename in library_vault |
| file_size | Integer | Nullable | File size in bytes |
| file_format | String(10) | Not Null, Default='pdf' | pdf, epub, mobi |
| publisher | Text | Nullable | Publisher |
| publication_year | Integer | Nullable | Year published |
| isbn | String(20) | Nullable, Index | ISBN |
| subject | Text | Nullable, Index | Subject/category |
| description | Text | Nullable | Book description |
| language | String(20) | Default='English' | Language |
| category | String(100) | Nullable | Category |
| tags | Text | Nullable | Comma-separated tags |
| view_count | Integer | Default=0 | Number of views |
| download_count | Integer | Default=0 | Number of downloads |
| uploaded_by | Integer | FK → User.id, Not Null | Uploader user ID |
| created_at | DateTime | Default=utcnow | Upload timestamp |
| updated_at | DateTime | Default=utcnow, Auto-update | Last modification |

**Relationships:**
- Many-to-One with User (uploader)
- One-to-Many with BookDigitalLink

**File Storage:**
- Location: `library_vault/digital_books/{filename}`
- Supported formats: PDF, EPUB, MOBI
- Max size: Configured (default 50MB)

---

## BookDigitalLink Table

Optional many-to-many relationship between physical and digital books.

| Column | Type | Constraints | Description |
|--------|------|--------------|-------------|
| id | Integer | PK, Auto-increment | Unique link ID |
| book_id | Integer | FK → Book.id, Not Null | Physical book ID |
| digital_book_id | Integer | FK → DigitalBook.id, Not Null | Digital book ID |
| link_type | String(20) | Default='same_edition' | same_edition, different_edition, related |
| notes | Text | Nullable | Link notes |
| created_at | DateTime | Default=utcnow | Creation timestamp |

**Relationships:**
- Many-to-One with Book
- Many-to-One with DigitalBook

---

## PasswordResetToken Table

Manages password reset tokens.

| Column | Type | Constraints | Description |
|--------|------|--------------|-------------|
| id | Integer | PK, Auto-increment | Unique token ID |
| user_id | Integer | FK → User.id, Not Null | User requesting reset |
| token | String(255) | Unique, Not Null, Index | Reset token |
| token_type | String(20) | Default='admin_generated' | admin_generated, emergency |
| created_at | DateTime | Default=utcnow | Token creation |
| expires_at | DateTime | Not Null | Token expiration |
| used_at | DateTime | Nullable | When token was used |
| is_used | Boolean | Default=False | Token used status |
| generated_by | Integer | FK → User.id, Nullable | Admin who generated |
| ip_address | String(45) | Nullable | Client IP |

**Token Validity:**
- Default expiry: 1 hour
- Tokens are case-insensitive (stored uppercase)

---

## PasswordHistory Table

Stores password history to prevent reuse.

| Column | Type | Constraints | Description |
|--------|------|--------------|-------------|
| id | Integer | PK, Auto-increment | Unique record ID |
| user_id | Integer | FK → User.id, Not Null | User ID |
| hashed_password | String(255) | Not Null | Previous password hash |
| changed_at | DateTime | Default=utcnow | Change timestamp |
| changed_by | Integer | FK → User.id, Nullable | Who changed (self or admin) |
| change_reason | String(50) | Nullable | user_change, admin_reset, forgot_password |
| ip_address | String(45) | Nullable | Client IP |

**Purpose:**
- Prevents password reuse (configurable history length)
- Auditing password changes

---

## Vendor Table

Stores magazine vendors/suppliers.

| Column | Type | Constraints | Description |
|--------|------|--------------|-------------|
| id | Integer | PK, Auto-increment | Unique vendor ID |
| name | String(100) | Unique, Not Null, Index | Vendor name |
| contact_details | Text | Nullable | Contact information |
| created_at | DateTime | Default=utcnow | Creation timestamp |

**Relationships:**
- One-to-Many with MagazineIssue

---

## Magazine Table

Stores magazine master records.

| Column | Type | Constraints | Description |
|--------|------|--------------|-------------|
| id | Integer | PK, Auto-increment | Unique magazine ID |
| title | String(200) | Not Null, Index | Magazine title |
| language | String(50) | Default='English' | Language |
| frequency | String(50) | Nullable | Monthly, Weekly, etc. |
| category | String(100) | Nullable | Technical, General, etc. |
| cover_image | String(255) | Nullable | Cover image path |
| is_active | Boolean | Default=True | Active status |
| created_at | DateTime | Default=utcnow | Creation timestamp |
| updated_at | DateTime | Default=utcnow, Auto-update | Last modification |

**Relationships:**
- One-to-Many with MagazineIssue (cascade delete)

---

## MagazineIssue Table

Tracks received magazine copies/issues.

| Column | Type | Constraints | Description |
|--------|------|--------------|-------------|
| id | Integer | PK, Auto-increment | Unique issue ID |
| magazine_id | Integer | FK → Magazine.id, Not Null | Magazine |
| issue_description | String(100) | Not Null | e.g., "January 2024" or "Vol 45, Issue 2" |
| received_date | DateTime | Default=utcnow | Date received |
| vendor_id | Integer | FK → Vendor.id, Not Null | Vendor supplied |
| remarks | Text | Nullable | Any remarks |
| created_at | DateTime | Default=utcnow | Creation timestamp |

**Relationships:**
- Many-to-One with Magazine
- Many-to-One with Vendor

---

## Database Indexes

| Table | Column(s) | Type | Purpose |
|-------|-----------|------|---------|
| User | username | Unique | Login lookup |
| User | email | Unique | Login lookup |
| Book | acc_no | Unique | Book lookup |
| Book | subject | Regular | Filtering |
| Book | language | Regular | Filtering |
| DigitalBook | title | Regular | Search |
| DigitalBook | author | Regular | Search |
| DigitalBook | isbn | Regular | Search |
| DigitalBook | subject | Regular | Filtering |
| Magazine | title | Regular | Search |
| Vendor | name | Unique | Vendor lookup |

---

## Database Location

- SQLite database: `data/tic_nexus.db`
- The database is automatically created on first run
- Tables are created via SQLAlchemy's `Base.metadata.create_all()`
