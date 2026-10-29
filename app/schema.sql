PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS items (
 id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE,
 total INTEGER NOT NULL DEFAULT 0 CHECK(total >= 0),
 available INTEGER NOT NULL DEFAULT 0 CHECK(available >= 0 AND available <= total),
 maintenance INTEGER NOT NULL DEFAULT 0 CHECK(maintenance>=0),
 price_cents INTEGER NOT NULL DEFAULT 0 CHECK(price_cents >= 0),
 replacement_cents INTEGER CHECK(replacement_cents>=0),
 pricing_mode TEXT NOT NULL DEFAULT 'daily' CHECK(pricing_mode IN ('daily','scaffold')),
 week_cents INTEGER NOT NULL DEFAULT 0 CHECK(week_cents >= 0),
 month_cents INTEGER NOT NULL DEFAULT 0 CHECK(month_cents >= 0)
);
CREATE TABLE IF NOT EXISTS clients (
 id INTEGER PRIMARY KEY, name TEXT NOT NULL, phone TEXT NOT NULL,
 payment_rating INTEGER NOT NULL DEFAULT 3 CHECK(payment_rating BETWEEN 1 AND 5),
 return_rating INTEGER NOT NULL DEFAULT 3 CHECK(return_rating BETWEEN 1 AND 5),
 care_rating INTEGER NOT NULL DEFAULT 3 CHECK(care_rating BETWEEN 1 AND 5),
 notes TEXT NOT NULL DEFAULT ''
 ,ratings_confirmed INTEGER NOT NULL DEFAULT 0 CHECK(ratings_confirmed IN (0,1))
);
CREATE TABLE IF NOT EXISTS addresses (
 id INTEGER PRIMARY KEY, client_id INTEGER NOT NULL REFERENCES clients(id),
 address TEXT NOT NULL, UNIQUE(client_id, address)
);
CREATE TABLE IF NOT EXISTS client_billing (
 client_id INTEGER PRIMARY KEY REFERENCES clients(id),
 legal_name TEXT NOT NULL DEFAULT '', rfc TEXT NOT NULL DEFAULT '',
 postal_code TEXT NOT NULL DEFAULT '', tax_regime TEXT NOT NULL DEFAULT '',
 cfdi_use TEXT NOT NULL DEFAULT '', email TEXT NOT NULL DEFAULT '',
 fiscal_address TEXT NOT NULL DEFAULT '', notes TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS client_documents (
 id INTEGER PRIMARY KEY,
 client_id INTEGER NOT NULL REFERENCES clients(id),
 category TEXT NOT NULL, filename TEXT NOT NULL,
 content BLOB NOT NULL, size_bytes INTEGER NOT NULL CHECK(size_bytes>0),
 sha256 TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 CHECK(length(content)=size_bytes),
 UNIQUE(client_id,category,sha256)
);
CREATE TABLE IF NOT EXISTS rentals (
 id INTEGER PRIMARY KEY, client_id INTEGER NOT NULL REFERENCES clients(id),
 address_id INTEGER NOT NULL REFERENCES addresses(id),
 client_name TEXT NOT NULL, client_phone TEXT NOT NULL, work_address TEXT NOT NULL,
 departure TEXT NOT NULL, due TEXT NOT NULL, days INTEGER NOT NULL CHECK(days > 0),
 total_cents INTEGER NOT NULL CHECK(total_cents >= 0),
 subtotal_cents INTEGER NOT NULL DEFAULT 0, vat_bp INTEGER NOT NULL DEFAULT 0,
 isr_bp INTEGER NOT NULL DEFAULT 0, vat_cents INTEGER NOT NULL DEFAULT 0, isr_cents INTEGER NOT NULL DEFAULT 0,
 returned_at TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS rental_lines (
 id INTEGER PRIMARY KEY, rental_id INTEGER NOT NULL REFERENCES rentals(id),
 item_id INTEGER NOT NULL REFERENCES items(id), item_name TEXT NOT NULL,
 quantity INTEGER NOT NULL CHECK(quantity > 0), price_cents INTEGER NOT NULL CHECK(price_cents >= 0),
 replacement_cents INTEGER CHECK(replacement_cents>=0),
 returned_qty INTEGER NOT NULL DEFAULT 0 CHECK(returned_qty>=0),
 delivery_condition TEXT NOT NULL DEFAULT 'Bueno', delivery_notes TEXT NOT NULL DEFAULT '',
 pricing_mode TEXT NOT NULL DEFAULT 'daily' CHECK(pricing_mode IN ('daily','scaffold')),
 week_cents INTEGER NOT NULL DEFAULT 0 CHECK(week_cents >= 0),
 month_cents INTEGER NOT NULL DEFAULT 0 CHECK(month_cents >= 0),
 UNIQUE(rental_id, item_id)
);
CREATE TABLE IF NOT EXISTS rental_extensions (
 id INTEGER PRIMARY KEY,
 rental_id INTEGER NOT NULL REFERENCES rentals(id),
 previous_due TEXT NOT NULL, new_due TEXT NOT NULL,
 added_days INTEGER NOT NULL CHECK(added_days > 0),
 added_cents INTEGER NOT NULL CHECK(added_cents >= 0),
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 adjustment_cents INTEGER
);
CREATE TABLE IF NOT EXISTS payments (
 id INTEGER PRIMARY KEY,
 rental_id INTEGER NOT NULL REFERENCES rentals(id),
 amount_cents INTEGER NOT NULL CHECK(amount_cents > 0),
 kind TEXT NOT NULL CHECK(kind IN ('Anticipo','Abono','Liquidación')),
 method TEXT NOT NULL CHECK(method IN ('Efectivo','Transferencia','Tarjeta')),
 paid_on TEXT NOT NULL,
 reference TEXT NOT NULL DEFAULT '',
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 cancelled_at TEXT,
 cancellation_reason TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS payments_rental_idx ON payments(rental_id);
CREATE TABLE IF NOT EXISTS rental_returns (
 id INTEGER PRIMARY KEY,
 rental_id INTEGER NOT NULL REFERENCES rentals(id),
 line_id INTEGER NOT NULL REFERENCES rental_lines(id),
 quantity INTEGER NOT NULL CHECK(quantity>0),
 condition TEXT NOT NULL CHECK(condition IN ('Bueno','Malo')),
 notes TEXT NOT NULL DEFAULT '',
 returned_on TEXT NOT NULL,
 unit_cents INTEGER NOT NULL CHECK(unit_cents>=0),
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS rental_returns_line_idx ON rental_returns(line_id);
CREATE TABLE IF NOT EXISTS reservations (
 id INTEGER PRIMARY KEY,
 client_id INTEGER NOT NULL REFERENCES clients(id),
 client_name TEXT NOT NULL, client_phone TEXT NOT NULL, work_address TEXT NOT NULL,
 departure TEXT NOT NULL, due TEXT NOT NULL,
 days INTEGER NOT NULL CHECK(days>0), total_cents INTEGER NOT NULL CHECK(total_cents>=0),
 subtotal_cents INTEGER NOT NULL DEFAULT 0, vat_bp INTEGER NOT NULL DEFAULT 0,
 isr_bp INTEGER NOT NULL DEFAULT 0, vat_cents INTEGER NOT NULL DEFAULT 0, isr_cents INTEGER NOT NULL DEFAULT 0,
 status TEXT NOT NULL DEFAULT 'Confirmada' CHECK(status IN ('Confirmada','Cancelada','Entregada')),
 rental_id INTEGER REFERENCES rentals(id), created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS reservation_lines (
 id INTEGER PRIMARY KEY,
 reservation_id INTEGER NOT NULL REFERENCES reservations(id),
 item_id INTEGER NOT NULL REFERENCES items(id), item_name TEXT NOT NULL,
 quantity INTEGER NOT NULL CHECK(quantity>0),
 price_cents INTEGER NOT NULL CHECK(price_cents>=0),
 replacement_cents INTEGER CHECK(replacement_cents>=0),
 pricing_mode TEXT NOT NULL, week_cents INTEGER NOT NULL, month_cents INTEGER NOT NULL,
 UNIQUE(reservation_id,item_id)
);
