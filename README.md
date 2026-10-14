# CRM System Integration with WooCommerce

A mini CRM that syncs customers and orders from a WooCommerce store, tracks orders per customer, and runs automatic communication workflows.

## Features
- Customer data management (search, notes, tags)
- Order tracking linked to customers
- Communication workflows (order confirmation, completed, cancelled, welcome)
- Initial sync via WooCommerce REST API + real-time updates via webhooks
- Webhook signature verification (HMAC-SHA256)

## Tech stack
Python, FastAPI, SQLite, HTML/JS dashboard

## Setup
1. `python -m venv venv` and activate it
2. `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and fill in values (`USE_MOCK=true` runs with sample data)
4. `uvicorn main:app --reload`
5. Open http://127.0.0.1:8000 (dashboard) or http://127.0.0.1:8000/docs (API docs)

## Testing webhooks
`python simulate_webhook.py order.created` (also: `order.completed`, `customer.created`, `bad-signature`)

## Assumptions
Single store, simulated emails, single admin user. Payments and multi-user auth are out of scope.
