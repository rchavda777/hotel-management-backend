-- ==============================================================
--                     Hotel Management System
-- ==============================================================

-- ======================== USERS ===============================
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    system_role VARCHAR(20) NOT NULL CHECK (system_role IN ('super_admin', 'user')),
    phone VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE,
    CONSTRAINT valid_email CHECK (
        email ~* '^[A-Za-z0-9._%-]+@[A-Za-z0-9.-]+\\.[A-Za-z]+$'
    )
);

-- ===================== STAFF POSITIONS ========================
CREATE TABLE IF NOT EXISTS staff_positions (
    id SERIAL PRIMARY KEY,
    position_name VARCHAR(50) NOT NULL UNIQUE CHECK (
        position_name IN (
            'Manager',
            'Receptionist',
            'Housekeeping',
            'Maintenance',
            'Chef',
            'Security',
            'Cleaner'
        )
    ),
    description TEXT,
    department VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ===================== STAFF PROFILES =========================
CREATE TABLE IF NOT EXISTS staff_profiles (
    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    date_of_birth DATE NOT NULL,
    address VARCHAR(255) NOT NULL,
    position_id INTEGER NOT NULL REFERENCES staff_positions(id) ON DELETE CASCADE,
    hire_date DATE NOT NULL
);

-- ===================== GUEST PROFILES =========================
CREATE TABLE IF NOT EXISTS guest_profiles (
    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    date_of_birth DATE NOT NULL,
    address VARCHAR(255) NOT NULL,
    preferences JSONB
);

-- ========================= HOTELS =============================
CREATE TABLE IF NOT EXISTS hotels (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    address TEXT NOT NULL,
    city VARCHAR(50) NOT NULL,
    state_province VARCHAR(50) NOT NULL,
    postal_code VARCHAR(20),
    country VARCHAR(50),
    phone VARCHAR(15) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_by INT REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ====================== ROOM TYPES ============================
CREATE TABLE IF NOT EXISTS room_types (
    id SERIAL PRIMARY KEY,
    type_name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    capacity SMALLINT NOT NULL CHECK (capacity > 0),
    price DECIMAL(10, 2) NOT NULL
);

-- ========================= ROOMS ==============================
CREATE TABLE IF NOT EXISTS rooms (
    id SERIAL PRIMARY KEY,
    hotel_id INTEGER NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
    room_number VARCHAR(10) NOT NULL,
    room_type INTEGER NOT NULL REFERENCES room_types(id),
    floor_number SMALLINT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'available' CHECK (
        status IN ('available', 'occupied', 'maintenance', 'cleaning')
    ),
    price DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (hotel_id, room_number)
);

-- ===================== ROOM STATUS HISTORY ====================
CREATE TABLE IF NOT EXISTS room_status_history (
    id SERIAL PRIMARY KEY,
    room_id INTEGER NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
    old_status VARCHAR(20) NOT NULL CHECK (
        old_status IN ('available', 'occupied', 'maintenance', 'cleaning')
    ),
    new_status VARCHAR(20) NOT NULL CHECK (
        new_status IN ('available', 'occupied', 'maintenance', 'cleaning')
    ),
    changed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    changed_by INTEGER REFERENCES users(id)
);

-- ===================== DISCOUNTS ==============================
CREATE TABLE IF NOT EXISTS discounts (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    description TEXT,
    percentage DECIMAL(5, 2) CHECK (percentage > 0 AND percentage <= 100),
    valid_from DATE NOT NULL,
    valid_to DATE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);


-- ======================= BOOKINGS =============================
CREATE TABLE IF NOT EXISTS bookings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    hotel_id INTEGER NOT NULL REFERENCES hotels(id) ON DELETE RESTRICT,
    room_id INTEGER NOT NULL REFERENCES rooms(id) ON DELETE RESTRICT,
    check_in_date DATE NOT NULL,
    check_out_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (
        status IN ('pending', 'confirmed', 'cancelled', 'completed')
    ),
    total_amount DECIMAL(10, 2) NOT NULL,
    payment_status VARCHAR(20) NOT NULL DEFAULT 'unpaid' CHECK (
        payment_status IN ('unpaid', 'paid', 'refunded')
    ),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_dates CHECK (
        check_in_date < check_out_date
    ),
    discount_id INTEGER REFERENCES discounts(id)
);

-- ===================== BOOKING PAYMENTS =======================
CREATE TABLE IF NOT EXISTS booking_payments (
    id SERIAL PRIMARY KEY,
    booking_id INTEGER NOT NULL REFERENCES bookings(id) ON DELETE CASCADE,
    amount DECIMAL(10, 2) NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    transaction_id VARCHAR(100) UNIQUE NOT NULL,
    payment_date TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (
        status IN ('pending', 'completed', 'failed', 'refunded')
    ),
    notes TEXT
);

-- ===================== STAFF ASSIGNMENTS ======================
CREATE TABLE IF NOT EXISTS staff_assignments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    hotel_id INTEGER NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
    position_id INTEGER NOT NULL REFERENCES staff_positions(id) ON DELETE CASCADE,
    start_date DATE NOT NULL,
    end_date DATE CHECK (end_date IS NULL OR end_date > start_date),
    is_primary BOOLEAN DEFAULT TRUE,
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (
        status IN ('active', 'inactive', 'terminated')
    )
);

-- ===================== USER-HOTEL ACCESS ======================
CREATE TABLE IF NOT EXISTS user_hotels (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    hotel_id INTEGER NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'manager', 'staff')),
    assigned_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, hotel_id)
);

-- ===================== HOTEL REVIEWS ==========================
CREATE TABLE IF NOT EXISTS hotel_reviews (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    hotel_id INTEGER NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
    rating SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ===================== CHECK-IN LOGS ==========================
CREATE TABLE IF NOT EXISTS checkin_logs (
    id SERIAL PRIMARY KEY,
    booking_id INTEGER NOT NULL REFERENCES bookings(id) ON DELETE CASCADE,
    check_in TIMESTAMPTZ,
    check_out TIMESTAMPTZ,
    checked_in_by INTEGER REFERENCES users(id),
    checked_out_by INTEGER REFERENCES users(id)
);
