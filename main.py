import base64
import hashlib
import hmac
import json
import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()  # must run before the modules below read environment variables

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import sync
from database import get_conn, init_db

app = FastAPI(title="CRM x WooCommerce Integration")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
def startup():
    init_db()


@app.get("/", include_in_schema=False)
def dashboard():
    return FileResponse("static/index.html")


# ---------- Sync ----------
@app.post("/sync")
def run_sync():
    conn = get_conn()
    try:
        return sync.run_full_sync(conn)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Sync failed: {e}")
    finally:
        conn.close()


# ---------- Customers ----------
@app.get("/customers")
def list_customers(search: Optional[str] = None):
    conn = get_conn()
    if search:
        like = f"%{search}%"
        rows = conn.execute(
            "SELECT * FROM customers WHERE first_name LIKE ? OR last_name LIKE ? OR email LIKE ? ORDER BY id DESC",
            (like, like, like),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM customers ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/customers/{customer_id}")
def get_customer(customer_id: int):
    conn = get_conn()
    customer = conn.execute("SELECT * FROM customers WHERE id = ?", (customer_id,)).fetchone()
    if not customer:
        conn.close()
        raise HTTPException(status_code=404, detail="Customer not found")
    orders = conn.execute(
        "SELECT * FROM orders WHERE customer_id = ? ORDER BY created_at DESC", (customer_id,)
    ).fetchall()
    orders_out = []
    for o in orders:
        items = conn.execute("SELECT * FROM order_items WHERE order_id = ?", (o["id"],)).fetchall()
        orders_out.append({**dict(o), "items": [dict(i) for i in items]})
    comms = conn.execute(
        "SELECT * FROM communications WHERE customer_id = ? ORDER BY id DESC", (customer_id,)
    ).fetchall()
    conn.close()
    return {**dict(customer), "orders": orders_out, "communications": [dict(c) for c in comms]}


class CustomerUpdate(BaseModel):
    notes: Optional[str] = None
    tags: Optional[str] = None


@app.patch("/customers/{customer_id}")
def update_customer(customer_id: int, update: CustomerUpdate):
    conn = get_conn()
    if not conn.execute("SELECT id FROM customers WHERE id = ?", (customer_id,)).fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Customer not found")
    if update.notes is not None:
        conn.execute("UPDATE customers SET notes = ? WHERE id = ?", (update.notes, customer_id))
    if update.tags is not None:
        conn.execute("UPDATE customers SET tags = ? WHERE id = ?", (update.tags, customer_id))
    conn.commit()
    conn.close()
    return {"status": "updated"}


# ---------- Orders and communications ----------
@app.get("/orders")
def list_orders(status: Optional[str] = None):
    conn = get_conn()
    query = (
        "SELECT o.*, c.first_name, c.last_name FROM orders o "
        "LEFT JOIN customers c ON o.customer_id = c.id"
    )
    if status:
        rows = conn.execute(query + " WHERE o.status = ? ORDER BY o.created_at DESC", (status,)).fetchall()
    else:
        rows = conn.execute(query + " ORDER BY o.created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/communications")
def list_communications():
    conn = get_conn()
    rows = conn.execute(
        "SELECT m.*, c.first_name, c.last_name, c.email FROM communications m "
        "LEFT JOIN customers c ON m.customer_id = c.id ORDER BY m.id DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------- Webhooks ----------
def verify_signature(raw_body: bytes, signature: str) -> bool:
    """WooCommerce signs the raw body with HMAC-SHA256 using the webhook secret, then base64-encodes it."""
    secret = os.getenv("WOO_WEBHOOK_SECRET", "").encode()
    expected = base64.b64encode(hmac.new(secret, raw_body, hashlib.sha256).digest()).decode()
    return hmac.compare_digest(expected, signature or "")


@app.post("/webhooks/woocommerce")
async def woocommerce_webhook(request: Request):
    raw_body = await request.body()
    signature = request.headers.get("X-WC-Webhook-Signature", "")
    if not verify_signature(raw_body, signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    topic = request.headers.get("X-WC-Webhook-Topic", "")
    try:
        payload = json.loads(raw_body)
    except ValueError:
        return {"status": "ping acknowledged"}  # WooCommerce sends a non-JSON ping when a webhook is created

    conn = get_conn()
    try:
        if topic == "customer.created":
            sync.upsert_customer(conn, payload, run_workflows=True)
        elif topic in ("order.created", "order.updated"):
            sync.upsert_order(conn, payload, run_workflows=True)
        else:
            return {"status": f"ignored topic {topic}"}
        conn.commit()
    finally:
        conn.close()
    return {"status": "processed", "topic": topic}