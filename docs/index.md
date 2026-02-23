# TIC Nexus Documentation

Welcome to the TIC Nexus documentation. This comprehensive guide covers all aspects of the application including API routes, web routes, data models, authentication, and data flow.

## Table of Contents

1. [Project Overview](./project-overview.md) - Technology stack and core features
2. [API Routes](./api-routes.md) - Complete API endpoints documentation
3. [Web Routes & Templates](./web-routes.md) - Page routes and template mapping
4. [Database Models](./data-models.md) - Database schema and relationships
5. [Data Flow](./data-flow.md) - How data flows through the system
6. [Authentication & Authorization](./authentication.md) - JWT, roles, and permissions

## Quick Reference

### Technology Stack
- **Backend**: FastAPI 0.109.0 + SQLAlchemy 2.0.25 + SQLite
- **Auth**: JWT (python-jose) + bcrypt password hashing
- **Frontend**: Alpine.js 3.x + Bulma CSS + Tailwind CSS
- **Server**: Uvicorn (dev) / Waitress (prod)

### User Roles
| Role | Permissions |
|------|-------------|
| Admin | Full access - CRUD on all resources, user management |
| Librarian | Circulation operations, book management, no user deletion |
| Viewer | Read-only access to books and transactions |

### Core Features
- **Physical Inventory**: Book catalog with circulation (issue/return/extend)
- **Digital Library**: PDF upload, viewing, download tracking
- **Magazine Management**: Vendor and issue tracking
- **User Management**: 3-tier RBAC (Admin, Librarian, Viewer)
- **Dashboard**: Statistics, charts, real-time status

## Getting Started

For installation and setup, see the [SETUP_GUIDE](../SETUP_GUIDE.md) in the root directory.

For quick start, see the [QUICK_START](../QUICK_START.md) in the root directory.
