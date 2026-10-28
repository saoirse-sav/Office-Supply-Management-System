import os
import socket
import sys
import time

import mysql.connector
from mysql.connector import errorcode

# ---------------------------------------------------------------------------
# Database settings (same defaults as before: XAMPP, user root, no password).
# You can still override any of them with environment variables:
#   DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
# ---------------------------------------------------------------------------
DEFAULT_PORT = 3306

# XAMPP's MySQL/MariaDB is sometimes moved to another port when 3306 is already
# taken (for example by a separate MySQL installation). If DB_PORT is NOT set
# and 3306 refuses the connection, these ports are tried automatically.
FALLBACK_PORTS = (3307, 3308, 3310)

# How many times to try before giving up, and the pause between tries.
# This covers the few seconds right after you press "Start" in XAMPP.
CONNECT_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 1

# Remembers a working fallback port so later requests do not search again.
_working_port = None


def get_connection_config():
    port_from_env = os.getenv("DB_PORT")
    if port_from_env:
        port = int(port_from_env)
    elif _working_port is not None:
        port = _working_port
    else:
        port = DEFAULT_PORT
    return {
        "host": os.getenv("DB_HOST", "127.0.0.1"),
        "port": port,
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "osms_db"),
        "connect_timeout": 5,
        "autocommit": True,
    }


def _port_is_open(host, port):
    # True if something is listening on host:port (quick check, 1 second max).
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except OSError:
        return False


def _explain(exc, config):
    # Turns a MySQL error into a message that says what to do next.
    where = f"{config['host']}:{config['port']}"
    errno = getattr(exc, "errno", None)

    if errno in (errorcode.CR_CONN_HOST_ERROR, errorcode.CR_CONNECTION_ERROR):
        hint = (
            f"Nothing is accepting connections at {where}, so MySQL/MariaDB is not running there. "
            "Fix: open the XAMPP Control Panel and click Start next to MySQL "
            "(wait until its name turns green and a port number shows). "
            "If it stops again right away, click Logs > mysql_error.log to see why. "
            "If XAMPP shows a port other than 3306 (for example 3307), set DB_PORT to that number."
        )
    elif errno == errorcode.ER_ACCESS_DENIED_ERROR:
        hint = (
            f"MySQL is running, but it rejected the login for user '{config['user']}'. "
            "Check DB_USER and DB_PASSWORD (XAMPP's default is user 'root' with an empty password)."
        )
    elif errno == errorcode.ER_BAD_DB_ERROR:
        hint = (
            f"MySQL is running, but the database '{config['database']}' does not exist. "
            "Open http://localhost/phpmyadmin, create it (or import your osms_db .sql file), "
            "or set DB_NAME to the correct name."
        )
    elif errno == errorcode.ER_HOST_NOT_PRIVILEGED:
        hint = (
            f"MySQL is running, but user '{config['user']}' is not allowed to connect from this host."
        )
    else:
        hint = "Make sure the XAMPP MySQL/MariaDB service is running and the user has access for that host."

    return (
        "Could not connect to the MySQL server at "
        f"{where} as '{config['user']}' "
        f"(database '{config['database']}'). "
        f"{hint} "
        f"MySQL said: {exc}"
    )


def _try_fallback_ports(config):
    # Looks for MySQL on the usual alternative XAMPP ports. Returns a connection or None.
    global _working_port
    if os.getenv("DB_PORT"):
        return None  # The user chose a port on purpose, so never second-guess it.
    for port in FALLBACK_PORTS:
        if not _port_is_open(config["host"], port):
            continue
        try:
            conn = mysql.connector.connect(**{**config, "port": port})
        except mysql.connector.Error:
            continue
        _working_port = port
        return conn
    return None


def get_connection():
    config = get_connection_config()
    last_error = None

    for attempt in range(CONNECT_ATTEMPTS):
        try:
            return mysql.connector.connect(**config)
        except mysql.connector.Error as exc:
            last_error = exc
            # Only "server not reachable" errors are worth retrying.
            if getattr(exc, "errno", None) not in (
                errorcode.CR_CONN_HOST_ERROR,
                errorcode.CR_CONNECTION_ERROR,
            ):
                break
            if attempt < CONNECT_ATTEMPTS - 1:
                time.sleep(RETRY_DELAY_SECONDS)

    # Port 3306 refused us: see whether XAMPP is running on another port.
    if getattr(last_error, "errno", None) in (
        errorcode.CR_CONN_HOST_ERROR,
        errorcode.CR_CONNECTION_ERROR,
    ):
        conn = _try_fallback_ports(config)
        if conn is not None:
            return conn

    raise RuntimeError(_explain(last_error, config)) from last_error


if __name__ == "__main__":
    # Run "python db.py" to test the database connection without starting Flask.
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT DATABASE(), VERSION()")
        database_name, server_version = cursor.fetchone()
        cursor.close()
        connection.close()
        used = get_connection_config()
        print(f"OK: connected to '{database_name}' on {used['host']}:{used['port']} (server version {server_version}).")
    except RuntimeError as problem:
        print("FAILED:", problem)
        sys.exit(1)