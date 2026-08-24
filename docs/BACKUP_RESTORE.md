# Backup & Restore

## Backup
```bash
DATABASE_URL=postgresql+asyncpg://... ./scripts/backup.sh ./backups
```
Produces a custom-format dump (`pg_dump -Fc`). Store off-host and encrypted.

## Restore
```bash
DATABASE_URL=postgresql+asyncpg://... ./scripts/restore.sh ./backups/aisupport_YYYY.dump
```
Uses `pg_restore --clean --if-exists`. Run migrations afterward if the target
schema is newer: `alembic upgrade head`.

## Attachments
Local storage: back up `STORAGE_LOCAL_DIR`. S3: rely on bucket versioning +
lifecycle policies.
