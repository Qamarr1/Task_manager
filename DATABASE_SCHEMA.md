# Database Schema

## Entities
- **users**  
  Holds account data for authentication and ownership.  
  Columns: `id (PK)`, `username (unique)`, `email (unique)`, `password_hash`, `created_at`.
- **tasks**  
  Stores tasks linked to a user.  
  Columns:  
  - `id (PK)`  
  - `user_id (FK -> users.id)`  
  - `title` (required, 255 char max)  
  - `description` (optional text)  
  - `priority` (`High` | `Medium` | `Low`, default `Medium`; Azure SQL defaults lowercase `medium`)  
  - `category` (text label, default `General`; Azure SQL defaults lowercase `general`)  
  - `due_date` (datetime, optional)  
  - `status` (canonical workflow state: `todo` | `in_progress` | `in_review` | `done`, default `todo`)  
  - `completed` (legacy boolean in older SQLite schemas; not present in Azure schema)  
  - `created_at` (timestamp, default current)  
  - `updated_at` (Azure SQL only, defaults to current)

## Relationships & Behaviors
- **users 1 ──► many tasks** via `tasks.user_id` with `ON DELETE CASCADE` so removing a user cleans up their tasks.
- **Workflow fields:** `status` is canonical. The app writes/reads `todo`, `in_progress`, `in_review`, `done`. `completed` is only used for backward compatibility; when both columns exist, `status` drives behavior and `completed` is synchronized to keep tests and old data working.
- **Schema drift handling:** `ensure_schema_columns()` keeps optional columns (due_date, priority, category, status/completed) present across SQLite and Azure SQL.

## Azure SQL Physical Schema
Source: `init_azure_sql.py` (used during provisioning on Azure).

```sql
CREATE TABLE users (
    id INT IDENTITY(1,1) PRIMARY KEY,
    username NVARCHAR(80) NOT NULL UNIQUE,
    email NVARCHAR(120) NOT NULL UNIQUE,
    password_hash NVARCHAR(255) NOT NULL,
    created_at DATETIME2 DEFAULT GETDATE()
);

CREATE TABLE tasks (
    id INT IDENTITY(1,1) PRIMARY KEY,
    title NVARCHAR(200) NOT NULL,
    description NVARCHAR(MAX),
    status NVARCHAR(20) NOT NULL DEFAULT 'todo',
    priority NVARCHAR(10) NOT NULL DEFAULT 'medium',
    category NVARCHAR(100) DEFAULT 'general',
    due_date DATETIME2 NULL,
    user_id INT NOT NULL,
    created_at DATETIME2 DEFAULT GETDATE(),
    updated_at DATETIME2 DEFAULT GETDATE(),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_tasks_user_id ON tasks(user_id);
CREATE INDEX idx_tasks_status ON tasks(status);
```

Notes:
- The Azure schema does not include `completed`; it relies on `status` for workflow. The app tolerates `completed` when present (SQLite) for backward compatibility.
- Length limits differ slightly from SQLite (e.g., `title` 200 chars in Azure vs 255 in SQLite).
- Defaults are lowercase in Azure (`medium`, `general`) but normalized in app logic when reading/writing.

## Diagram (Azure SQL)
```text
┌───────────────┐          1 ──► ┌────────────────────────────────┐
│   users       │◀───────────────┤             tasks              │
├───────────────┤                ├────────────────────────────────┤
│ id (PK)       │                │ id (PK)                        │
│ username (U)  │                │ user_id (FK -> users.id)       │
│ email (U)     │                │ title (NVARCHAR(200))          │
│ password_hash │                │ description (NVARCHAR(MAX))    │
│ created_at    │                │ status (todo|in_progress|      │
└───────────────┘                │         in_review|done)        │
                                 │ priority (medium|high|low)     │
                                 │ category (general|custom)      │
                                 │ due_date (DATETIME2 NULL)      │
                                 │ created_at (GETDATE default)   │
                                 │ updated_at (GETDATE default)   │
                                 └────────────────────────────────┘
(Compatibility: SQLite adds legacy `completed` boolean and allows
255-char titles; app normalizes to `status` as canonical.)
```

## Implementation Notes
- **Schema files:** `schema.sql` for SQLite; `init_azure_sql.py` initializes Azure SQL equivalents.
- **Runtime guardrails:** `app.py` calls `ensure_schema_columns()` to add optional columns (due_date, priority, category, status/completed) if missing, enabling older databases to stay compatible.
- **Type differences:** Azure SQL uses `NVARCHAR`/`DATETIME`; SQLite uses `TEXT`/`DATETIME` with `BOOLEAN` emulation.
