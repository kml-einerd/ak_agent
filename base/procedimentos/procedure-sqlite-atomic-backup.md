# PROCEDURE: SQLite Atomic Backup

**TRIGGER:** Need to back up a SQLite database that is actively serving requests, without stopping the application or risking corruption
**DOMAIN:** deployment / database
**PRE-CONDITIONS:** SQLite database is in use (WAL mode recommended). Destination directory exists. Application is running and handling requests.

---

## STEPS

1. Execute `VACUUM INTO '/path/to/backup/database.sqlite3'` via SQL → produces an atomic, consistent, desfragmented copy of the database while the application continues serving requests normally
2. Verify the backup file is a valid SQLite database → `sqlite3 /path/to/backup/database.sqlite3 "PRAGMA integrity_check;"` should return "ok"
3. Transfer the backup file to an external location (rsync, S3 upload, or shared volume) → the file is a standalone, complete SQLite database that can be opened, queried, or restored directly
4. Automate with a scheduled job (e.g., Rails job running hourly via SolidQueue cron) → `ActiveRecord::Base.connection.execute("VACUUM INTO '#{dest}'")`

**ON_FAILURE[step-1]:** If VACUUM INTO fails due to disk space, ensure the destination has at least as much free space as the database size. VACUUM INTO creates a full copy, not an incremental one.
**ON_FAILURE[step-2]:** If integrity check fails, the backup is corrupted — discard and retry. Check if the destination disk has I/O errors.

---

## DONE WHEN
- A valid .sqlite3 backup file exists at the destination path (verified by `sqlite3 backup.sqlite3 "PRAGMA integrity_check;"` returning "ok")
- The backup file can be opened and queried independently as a standalone database
- The application was never interrupted during the backup process (verified by checking application logs for zero downtime)

**WARNING:** NEVER back up an active SQLite database by raw-copying the .sqlite3 file (cp, tar, rsync). If a write is in progress during the copy, the backup will be a half-written, corrupted file. Always use VACUUM INTO or the `.backup` command.

## SOURCE
https://akitaonrails.com/2026/02/20/sqlite-kamal-deploy-de-rails-sem-drama-bastidores-do-the-m-akita-chronicles/
