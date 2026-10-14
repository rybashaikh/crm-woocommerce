"""Saves WooCommerce data into our database.
Every save is an 'upsert' keyed on woo_id, so running it twice never creates duplicates."""
import workflows
from woo_client import fetch_all


def upsert_customer(conn, c, run_workflows=False):
    billing = c.get("billing") or {}
    existing = conn.execute("SELECT id FROM customers WHERE woo_id = ?", (c["id"],)).fetchone()
    conn.execute(
        """
        INSERT INTO customers (woo_id, first_name, last_name, email, phone, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(woo_id) DO UPDATE SET
            first_name = excluded.first_name,
            last_name = excluded.last_name,
            email = excluded.email,
            phone = excluded.phone
        """,
        (c["id"], c.get("first_name"), c.get("last_name"), c.get("email"),
         billing.get("phone"), c.get("date_created")),
    )
    row = conn.execute("SELECT * FROM customers WHERE woo_id = ?", (c["id"],)).fetchone()
    if run_workflows:
        workflows.run_customer_workflows(conn, row, is_new=existing is None)
    return row


def _find_or_create_customer_for_order(conn, o):
    """Orders reference a customer by WooCommerce id; guest orders have customer_id 0, so match by email."""
    if o.get("customer_id"):
        row = conn.execute("SELECT * FROM customers WHERE woo_id = ?", (o["customer_id"],)).fetchone()
        if row:
            return row
    billing = o.get("billing") or {}
    email = billing.get("email")
    if email:
        row = conn.execute("SELECT * FROM customers WHERE email = ?", (email,)).fetchone()
        if row:
            return row
    cur = conn.execute(
        "INSERT INTO customers (woo_id, first_name, last_name, email, phone, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (o.get("customer_id") or None, billing.get("first_name"), billing.get("last_name"),
         email, billing.get("phone"), o.get("date_created")),
    )
    return conn.execute("SELECT * FROM customers WHERE id = ?", (cur.lastrowid,)).fetchone()


def upsert_order(conn, o, run_workflows=False):
    customer = _find_or_create_customer_for_order(conn, o)
    existing = conn.execute("SELECT id, status FROM orders WHERE woo_id = ?", (o["id"],)).fetchone()
    old_status = existing["status"] if existing else None

    conn.execute(
        """
        INSERT INTO orders (woo_id, customer_id, status, total, currency, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(woo_id) DO UPDATE SET
            customer_id = excluded.customer_id,
            status = excluded.status,
            total = excluded.total,
            currency = excluded.currency,
            updated_at = excluded.updated_at
        """,
        (o["id"], customer["id"], o.get("status"), o.get("total"), o.get("currency"),
         o.get("date_created"), o.get("date_modified")),
    )
    order = conn.execute("SELECT * FROM orders WHERE woo_id = ?", (o["id"],)).fetchone()

    # Replace line items so they always match WooCommerce
    conn.execute("DELETE FROM order_items WHERE order_id = ?", (order["id"],))
    for item in o.get("line_items", []):
        conn.execute(
            "INSERT INTO order_items (order_id, product_name, quantity, price) VALUES (?, ?, ?, ?)",
            (order["id"], item.get("name"), item.get("quantity"), str(item.get("price"))),
        )

    if run_workflows:
        workflows.run_order_workflows(conn, customer, order, is_new=existing is None, old_status=old_status)
    return order


def run_full_sync(conn):
    """Initial sync: pull all customers and orders from WooCommerce. No messages are sent during sync."""
    customers = fetch_all("customers")
    for c in customers:
        upsert_customer(conn, c, run_workflows=False)
    orders = fetch_all("orders")
    for o in orders:
        upsert_order(conn, o, run_workflows=False)
    conn.commit()
    return {"customers": len(customers), "orders": len(orders)}