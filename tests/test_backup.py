import sqlite3

from scripts.backup import backup_database


def test_backup_creates_restorable_copy(tmp_path):
    source = tmp_path / "auth.db"
    with sqlite3.connect(source) as db:
        db.execute("create table users (id integer primary key, email text)")
        db.execute("insert into users(email) values ('backup@example.com')")
        db.commit()

    target = backup_database(source, tmp_path / "backups")
    assert target.is_file()
    with sqlite3.connect(target) as db:
        assert db.execute("select email from users").fetchone()[0] == "backup@example.com"
