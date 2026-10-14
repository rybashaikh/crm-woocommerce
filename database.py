import os
import sqlite3

DB_PATH = os.getenv("DATABASE_PATH", "crm.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_conn()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            woo_id INTEGER UNIQUE,
            first_name TEXT,
            last_name TEXT,
            email TEXT,
            phone TEXT,
            notes TEXT DEFAULT '',
            tags TEXT DEFAULT '',
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            woo_id INTEGER UNIQUE,
            customer_id INTEGER,
            status TEXT,
            total TEXT,
            currency TEXT,
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        );

        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            product_name TEXT,
            quantity INTEGER,
            price TEXT,
            FOREIGN KEY (order_id) REFERENCES orders(id)
        );

        CREATE TABLE IF NOT EXISTS communications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            order_id INTEGER,
            channel TEXT,
            subject TEXT,
            body TEXT,
            trigger_event TEXT,
            sent_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        );
        """
    )
    conn.commit()
    conn.close()