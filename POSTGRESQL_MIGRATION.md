# PostgreSQL Migration Guide

This guide explains how to migrate the SmartLinks Autopilot backend from SQLite to PostgreSQL.

## Prerequisites

1. PostgreSQL server installed and running
2. Python 3.8 or higher
3. `pip` package manager

## Setup Instructions

### 1. Install Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

### 2. Configure PostgreSQL

1. Create a new PostgreSQL database and user:

```bash
# Connect to PostgreSQL as superuser
psql -U postgres

# Create database and user
CREATE DATABASE smartlinks;
CREATE USER smartlinks_user WITH PASSWORD 'smartpass';
GRANT ALL PRIVILEGES ON DATABASE smartlinks TO smartlinks_user;
```

Or use the setup script (requires PostgreSQL superuser credentials):

```bash
python scripts/setup_postgres.py
```

### 3. Configure Environment Variables

Update your `.env` file with the PostgreSQL connection string:

```
DATABASE_URL=postgresql+psycopg2://smartlinks_user:smartpass@localhost:5432/smartlinks
```

### 4. Initialize the Database

Run the database initialization script to create tables and seed initial data:

```bash
python -m src.soft.initdb
```

Or use the helper script:

```bash
python scripts/init_db.py
```

### 5. Run the Application

Start the FastAPI server:

```bash
uvicorn src.soft.main:app --reload
```

## Verifying the Migration

1. Connect to the PostgreSQL database:

```bash
psql -U smartlinks_user -d smartlinks
```

2. Check the tables:

```sql
\dt
```

3. Verify data was seeded:

```sql
SELECT * FROM offers;
SELECT * FROM segments;
```

## Troubleshooting

### Connection Issues

- Ensure PostgreSQL is running: `sudo service postgresql status`
- Check connection string in `.env`
- Verify database user permissions

### Database Errors

- Check logs for specific error messages
- Ensure all migrations have been applied
- Verify database schema matches models

## Reverting to SQLite

To switch back to SQLite:

1. Update `.env`:

```
DATABASE_URL=sqlite:///./smartlinks.db
```

2. Delete the SQLite database file if it exists:

```bash
rm smartlinks.db
```

3. Re-initialize the database:

```bash
python -m src.soft.initdb
```

## Backup and Restore

### Backup Database

```bash
pg_dump -U smartlinks_user -d smartlinks > smartlinks_backup.sql
```

### Restore Database

```bash
psql -U smartlinks_user -d smartlinks < smartlinks_backup.sql
```

## Performance Tuning (Optional)

For production use, consider these PostgreSQL optimizations:

1. Update `postgresql.conf`:

```
shared_buffers = 1GB                  # 25% of total RAM
work_mem = 64MB                      # 2-4x for complex queries
maintenance_work_mem = 256MB         # For VACUUM and CREATE INDEX
synchronous_commit = off             # For better write performance
wal_buffers = 16MB
checkpoint_completion_target = 0.9
random_page_cost = 1.1               # For SSDs
effective_cache_size = 4GB            # 50-75% of total RAM
```

2. Create indexes for frequently queried columns:

```sql
CREATE INDEX idx_clicks_ts ON clicks(ts);
CREATE INDEX idx_conversions_click_id ON conversions(click_id);
CREATE INDEX idx_offers_status ON offers(status);
```

3. Run `VACUUM ANALYZE` regularly or set up autovacuum.

## Monitoring

Use these queries to monitor database performance:

```sql
-- Active queries
SELECT pid, now() - query_start AS duration, query, state 
FROM pg_stat_activity 
WHERE state != 'idle' 
ORDER BY duration DESC;

-- Index usage
SELECT relname, indexrelname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes 
ORDER BY idx_scan DESC;

-- Table statistics
SELECT relname, n_live_tup, n_dead_tup, last_vacuum, last_autovacuum
FROM pg_stat_user_tables;
```

## Maintenance

1. Regular backups
2. Monitor and adjust autovacuum settings
3. Regular `REINDEX` and `VACUUM FULL` during maintenance windows
4. Monitor query performance and add indexes as needed
