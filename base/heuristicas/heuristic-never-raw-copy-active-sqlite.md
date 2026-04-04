# HEURISTIC: Never Raw-Copy Active SQLite

**DOMAIN:** database / deployment
**RULE:** Never back up an active SQLite database by raw-copying the .sqlite3 file (cp, tar, rsync, filesystem snapshots). Always use VACUUM INTO or the SQLite .backup command.
**APPLIES WHEN:** Any situation where you need a copy of a SQLite database that is currently open and being written to by an application. Includes backup scripts, migration procedures, and container image builds.
**RATIONALE:**
1. SQLite uses WAL (Write-Ahead Logging) and journaling to protect the active database from corruption during writes, but these protections apply to the active process — not to a raw file copy. [explicit]
2. If a write is in progress at the moment of copying, the resulting file is a half-written, inconsistent database that may not open or may contain corrupted data. [explicit]
3. VACUUM INTO produces an atomic, consistent copy by reading the database through SQLite's own consistency guarantees, ensuring the backup is always valid regardless of concurrent activity. [derived]
**COUNTER-INDICATION:** If the database is guaranteed to be offline (application stopped, no open connections), raw copy is safe. But using VACUUM INTO is still preferred because it also desfragments the database, producing a smaller and faster backup file.

## SOURCE
https://akitaonrails.com/2026/02/20/sqlite-kamal-deploy-de-rails-sem-drama-bastidores-do-the-m-akita-chronicles/
