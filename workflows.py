"""Communication workflows: rules that turn order/customer events into messages.
Emails are simulated: they are saved in the communications table and printed to the console."""

TEMPLATES = {
    "welcome": {
        "subject": "Welcome, {first_name}!",
        "body": "Hi {first_name}, thanks for creating an account with us. We're glad to have you.",
    },
    "order_confirmation": {
        "subject": "We received your order #{order_number}",
        "body": "Hi {first_name}, your order #{order_number} (total {total} {currency}) is confirmed and being prepared.",
    },
    "order_completed": {
        "subject": "Your order #{order_number} is complete",
        "body": "Hi {first_name}, your order #{order_number} is complete. Thank you for shopping with us! "
                "We'd love to hear your feedback.",
    },
    "order_cancelled": {
        "subject": "Your order #{order_number} was cancelled",
        "body": "Hi {first_name}, your order #{order_number} has been cancelled. Contact us if this was a mistake.",
    },
}


def send_message(conn, customer, template_key, trigger_event, order=None):
    """Render a template and log it as a simulated email."""
    tpl = TEMPLATES[template_key]
    values = {
        "first_name": customer["first_name"] or "there",
        "order_number": order["woo_id"] if order else "",
        "total": order["total"] if order else "",
        "currency": order["currency"] if order else "",
    }
    subject = tpl["subject"].format(**values)
    body = tpl["body"].format(**values)
    conn.execute(
        "INSERT INTO communications (customer_id, order_id, channel, subject, body, trigger_event) "
        "VALUES (?, ?, 'email (simulated)', ?, ?, ?)",
        (customer["id"], order["id"] if order else None, subject, body, trigger_event),
    )
    print(f"[WORKFLOW] {trigger_event} -> to {customer['email']}: {subject}")


def run_customer_workflows(conn, customer, is_new):
    if is_new:
        send_message(conn, customer, "welcome", "customer.created")


def run_order_workflows(conn, customer, order, is_new, old_status):
    """Decide which message (if any) to send for this order event."""
    new_status = order["status"]
    if is_new and new_status in ("pending", "processing", "on-hold"):
        send_message(conn, customer, "order_confirmation", "order.created", order)
    elif not is_new and old_status != new_status:
        if new_status == "completed":
            send_message(conn, customer, "order_completed", "order.updated", order)
        elif new_status == "cancelled":
            send_message(conn, customer, "order_cancelled", "order.updated", order)