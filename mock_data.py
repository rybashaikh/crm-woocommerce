"""Sample data shaped like WooCommerce REST API v3 responses.
Used when USE_MOCK=true so you can build and demo without a real store."""

CUSTOMERS = [
    {"id": 101, "first_name": "Aarav", "last_name": "Naik", "email": "aarav.naik@example.com",
     "date_created": "2026-09-01T10:15:00", "billing": {"phone": "9876500001"}},
    {"id": 102, "first_name": "Maria", "last_name": "Fernandes", "email": "maria.f@example.com",
     "date_created": "2026-09-05T14:30:00", "billing": {"phone": "9876500002"}},
    {"id": 103, "first_name": "Rohan", "last_name": "Kamat", "email": "rohan.k@example.com",
     "date_created": "2026-09-12T09:00:00", "billing": {"phone": "9876500003"}},
]

ORDERS = [
    {"id": 5001, "customer_id": 101, "status": "completed", "total": "1499.00", "currency": "INR",
     "date_created": "2026-09-02T11:00:00", "date_modified": "2026-09-04T12:00:00",
     "billing": {"first_name": "Aarav", "last_name": "Naik", "email": "aarav.naik@example.com", "phone": "9876500001"},
     "line_items": [{"name": "Cotton T-Shirt", "quantity": 2, "price": 499},
                    {"name": "Canvas Tote Bag", "quantity": 1, "price": 501}]},
    {"id": 5002, "customer_id": 102, "status": "processing", "total": "2999.00", "currency": "INR",
     "date_created": "2026-09-06T16:00:00", "date_modified": "2026-09-06T16:00:00",
     "billing": {"first_name": "Maria", "last_name": "Fernandes", "email": "maria.f@example.com", "phone": "9876500002"},
     "line_items": [{"name": "Running Shoes", "quantity": 1, "price": 2999}]},
    {"id": 5003, "customer_id": 101, "status": "pending", "total": "799.00", "currency": "INR",
     "date_created": "2026-09-20T18:45:00", "date_modified": "2026-09-20T18:45:00",
     "billing": {"first_name": "Aarav", "last_name": "Naik", "email": "aarav.naik@example.com", "phone": "9876500001"},
     "line_items": [{"name": "Water Bottle", "quantity": 1, "price": 799}]},
    {"id": 5004, "customer_id": 0, "status": "completed", "total": "1200.00", "currency": "INR",
     "date_created": "2026-09-22T10:10:00", "date_modified": "2026-09-23T10:10:00",
     "billing": {"first_name": "Guest", "last_name": "Buyer", "email": "guest.buyer@example.com", "phone": "9876500009"},
     "line_items": [{"name": "Notebook Set", "quantity": 4, "price": 300}]},
]