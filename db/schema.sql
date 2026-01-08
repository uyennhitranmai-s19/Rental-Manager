PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS bill;
DROP TABLE IF EXISTS contract;
DROP TABLE IF EXISTS tenant;
DROP TABLE IF EXISTS room;
DROP TABLE IF EXISTS user;

CREATE TABLE IF NOT EXISTS room (
    room_id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_name TEXT NOT NULL,
    area_m2 INTEGER,
    floor INTEGER,
    base_rent INTEGER,
    electric_unit_price INTEGER,
    water_unit_price INTEGER,
    status INTEGER NOT NULL DEFAULT 0 CHECK (status IN (0,1,2)),
    note TEXT,
    is_deleted INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS tenant (
    tenant_id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    sex INTEGER CHECK (sex IN (0,1,2)),
    phone TEXT,
    id_number TEXT NOT NULL,
    address TEXT,
    birth TEXT,
    email TEXT,
    note TEXT,
    is_deleted INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS contract (
    contract_id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id INTEGER,
    tenant_id INTEGER NOT NULL,
    start_ymd TEXT NOT NULL,
    end_ymd TEXT,
    rent INTEGER NOT NULL,
    deposit_amount INTEGER,
    electric_meter_start INTEGER,
    water_meter_start INTEGER,
    contract_status TEXT DEFAULT 'active',
    deposit_ymd TEXT,
    note TEXT,
--    contract_name TEXT,
    is_deleted INTEGER DEFAULT 0,
    FOREIGN KEY (room_id) REFERENCES room(room_id),
    FOREIGN KEY (tenant_id) REFERENCES tenant(tenant_id)
);

CREATE TABLE IF NOT EXISTS bill (
    bill_id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL REFERENCES contract(contract_id),
    room_id INTEGER REFERENCES room(room_id),
    tenant_name TEXT NOT NULL,
    room_name TEXT NOT NULL,
    bill_month TEXT NOT NULL,
    elec_prev INTEGER,
    elec_current INTEGER,
    water_prev INTEGER,
    water_current INTEGER,
    water_unit_price INTEGER,
    electric_unit_price INTEGER,
    room_rent_amount INTEGER,
    other_fee INTEGER,
    total_amount INTEGER,
    paid_amount INTEGER,
    paid_status TEXT DEFAULT 'unpaid',
    paid_ymd TEXT,
    pdf_path TEXT,
    note TEXT,
    invoice_name TEXT,
    is_deleted INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS user (
    login_id TEXT PRIMARY KEY,
    login_password TEXT NOT NULL,
    user_name TEXT NOT NULL,
    email TEXT
);

INSERT OR IGNORE INTO user (login_id, login_password, user_name, email)
VALUES ('admin', '123456', 'Admin', 'admin@gmail.com');