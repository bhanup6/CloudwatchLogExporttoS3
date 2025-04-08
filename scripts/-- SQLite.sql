-- SQLite
sqlite3 database/exports.db "ALTER TABLE export_status ADD COLUMN transfer_time REAL"
sqlite3 database/exports.db "ALTER TABLE export_status ADD COLUMN log_size INTEGER"
sqlite3 database/exports.db "ALTER TABLE export_status ADD COLUMN log_group_name TEXT"