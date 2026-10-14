"""Sends a correctly signed fake WooCommerce webhook to your running CRM.
Usage:
    python simulate_webhook.py order.created
    python simulate_webhook.py order.completed
    python simulate_webhook.py customer.created
    python simulate_webhook.py bad-signature
"""
import base64
import hashlib
import hmac
import json
import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()
URL = "http://127.0.0.1:8000/webhooks/woocommerce"
SECRET = os.getenv("WOO_WEBHOOK_SECRET", "").encode()

SCENARIOS = {
    "customer.created": ("customer.created", {
        "id": 104, "first_name": "Sneha", "last_name": "Desai", "email": "sneha.d@example.com",
        "date_created": "2026-10-14T09:00:00", "billing": {"phone": "9876500004"}}),
    "order.created": ("order.created", {
        "id": 5005, "customer_id": 104, "status": "processing", "total": "1850.00", "currency": "INR",
        "date_created": "2026-10-14T09:30:00", "date_modified": "2026-10-14T09:30:00",
        "billing": {"first_name": "Sneha", "last_name": "Desai", "email": "sneha.d@example.com", "phone": "9876500004"},
        "line_items": [{"name": "Yoga Mat", "quantity": 1, "price": 1850}]}),
    "order.completed": ("order.updated", {
        "id": 5005, "customer_id": 104, "status": "completed", "total": "1850.00", "currency": "INR",
        "date_created": "2026-10-14T09:30:00", "date_modified": "2026-10-14T11:00:00",
        "billing": {"first_name": "Sneha", "last_name": "Desai", "email": "sneha.d@example.com", "phone": "9876500004"},
        "line_items": [{"name": "Yoga Mat", "quantity": 1, "price": 1850}]}),
}

choice = sys.argv[1] if len(sys.argv) > 1 else "order.created"
bad = choice == "bad-signature"
topic, payload = SCENARIOS["order.created"] if bad else SCENARIOS[choice]

body = json.dumps(payload).encode()
sig = base64.b64encode(hmac.new(SECRET, body, hashlib.sha256).digest()).decode()
if bad:
    sig = "thisisnotavalidsignature"

resp = requests.post(URL, data=body, headers={
    "Content-Type": "application/json",
    "X-WC-Webhook-Topic": topic,
    "X-WC-Webhook-Signature": sig,
})
print(resp.status_code, resp.text)