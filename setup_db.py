import os
import sys

import mysql.connector

import db

# The schema file lives inside the project, next to this script:
#   C:\osms-python\database\osms_full_schema.sql
SCHEMA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database", "osms_full_schema.sql")


def connect_without_database():
    # Same settings as db.py, but without choosing a database,
    # because osms_db may not exist yet (or is about to be deleted).
    config = db.get_connection_config()
    config.pop("database", None)
    ports = [config["port"]]
    if not os.getenv("DB_PORT"):
        ports += [p for p in db.FALLBACK_PORTS if p not in ports]

    last_error = None
    for port in ports:
        try:
            return mysql.connector.connect(**{**config, "port": port})
        except mysql.connector.Error as exc:
            last_error = exc
            if getattr(exc, "errno", None) not in (2002, 2003):
                break
    config["database"] = os.getenv("DB_NAME", "osms_db")
    print("FAILED:", db._explain(last_error, config))
    sys.exit(1)


def read_statements(path):
    # Reads the .sql file and returns a list of single SQL statements.
    with open(path, encoding="utf-8") as sql_file:
        lines = [line for line in sql_file if not line.strip().startswith("--")]
    return [part.strip() for part in "".join(lines).split(";") if part.strip()]


def main():
    database_name = os.getenv("DB_NAME", "osms_db")
    reset = "--reset" in sys.argv

    if not os.path.isfile(SCHEMA_FILE):
        print(f"FAILED: schema file not found: {SCHEMA_FILE}")
        sys.exit(1)

    conn = connect_without_database()
    cursor = conn.cursor()

    if reset:
        print(f"WARNING: this will permanently DELETE the database '{database_name}' and all its data.")
        answer = input(f"Type the database name ({database_name}) to confirm: ").strip()
        if answer != database_name:
            print("Cancelled. Nothing was deleted.")
            conn.close()
            sys.exit(0)
        cursor.execute(f"DROP DATABASE IF EXISTS `{database_name}`")
        print(f"Deleted database '{database_name}'.")

    for statement in read_statements(SCHEMA_FILE):
        cursor.execute(statement)
    conn.commit()

    cursor.execute(f"USE `{database_name}`")
    cursor.execute("SHOW TABLES")
    tables = [row[0] for row in cursor.fetchall()]
    cursor.execute("SELECT COUNT(*) FROM roles")
    role_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM approval_levels")
    level_count = cursor.fetchone()[0]
    conn.close()

    print(f"OK: database '{database_name}' is ready with {len(tables)} tables "
          f"({role_count} roles, {level_count} approval levels).")
    print("Next: run  python db.py  to test, then  python app.py  to start the app.")


if __name__ == "__main__":
    main()