-- =====================================================================
-- schema.sql — нормализованная схема БД "Лаборатория технопарка"
-- Нормализация: 3НФ (убраны транзитивные зависимости)
-- Добавлены связи с таблицей users для отслеживания действий
-- =====================================================================

PRAGMA foreign_keys = ON;

-- =====================================================================
-- Таблица 1: users (пользователи системы)
-- Создаём первой, т.к. на неё ссылаются другие таблицы
-- =====================================================================
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role TEXT DEFAULT 'operator' CHECK(role IN ('admin', 'operator')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================================
-- Таблица 2: laboratories (лаборатории)
-- =====================================================================
CREATE TABLE IF NOT EXISTS laboratories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    location VARCHAR(200),
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,  -- Кто создал запись (связь с users)
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- =====================================================================
-- Таблица 3: rooms (помещения)
-- =====================================================================
CREATE TABLE IF NOT EXISTS rooms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    laboratory_id INTEGER NOT NULL,
    capacity INTEGER,
    floor INTEGER,
    created_by INTEGER,  -- Кто создал запись
    FOREIGN KEY (laboratory_id) REFERENCES laboratories(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- =====================================================================
-- Таблица 4: equipment (оборудование)
-- НОРМАЛИЗАЦИЯ: убран laboratory_id (получается через room_id -> rooms)
-- Добавлены поля created_by, updated_by для отслеживания действий
-- =====================================================================
CREATE TABLE IF NOT EXISTS equipment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(150) NOT NULL,
    category VARCHAR(50),
    serial_number VARCHAR(100) UNIQUE,
    manufacturer VARCHAR(100),
    purchase_date DATE,
    purchase_price NUMERIC(10, 2),
    status TEXT DEFAULT 'available' CHECK(status IN ('available', 'in_use', 'maintenance', 'decommissioned')),
    room_id INTEGER,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,   -- Кто добавил оборудование
    updated_by INTEGER,   -- Кто последний редактировал
    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL
);

-- =====================================================================
-- Таблица 5: residents (резиденты)
-- =====================================================================
CREATE TABLE IF NOT EXISTS residents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name VARCHAR(200) NOT NULL,
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(20),
    organization VARCHAR(150),
    role TEXT DEFAULT 'student' CHECK(role IN ('student', 'researcher', 'engineer', 'manager')),
    registration_date DATE DEFAULT (DATE('now')),
    registered_by INTEGER,  -- Кто зарегистрировал резидента
    FOREIGN KEY (registered_by) REFERENCES users(id) ON DELETE SET NULL
);

-- =====================================================================
-- Таблица 6: equipment_usage (использование оборудования)
-- Добавлены поля issued_by, returned_by для отслеживания кто выдал/принял
-- =====================================================================
CREATE TABLE IF NOT EXISTS equipment_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id INTEGER NOT NULL,
    resident_id INTEGER NOT NULL,
    start_datetime DATETIME NOT NULL,
    end_datetime DATETIME,
    purpose TEXT,
    status TEXT DEFAULT 'active' CHECK(status IN ('active', 'completed', 'cancelled')),
    issued_by INTEGER,    -- Кто выдал оборудование
    returned_by INTEGER,  -- Кто принял возврат
    FOREIGN KEY (equipment_id) REFERENCES equipment(id) ON DELETE CASCADE,
    FOREIGN KEY (resident_id) REFERENCES residents(id) ON DELETE CASCADE,
    FOREIGN KEY (issued_by) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (returned_by) REFERENCES users(id) ON DELETE SET NULL
);

-- =====================================================================
-- Индексы для ускорения запросов
-- =====================================================================
CREATE INDEX IF NOT EXISTS idx_equipment_status ON equipment(status);
CREATE INDEX IF NOT EXISTS idx_equipment_category ON equipment(category);
CREATE INDEX IF NOT EXISTS idx_equipment_room ON equipment(room_id);
CREATE INDEX IF NOT EXISTS idx_residents_full_name ON residents(full_name);
CREATE INDEX IF NOT EXISTS idx_usage_status ON equipment_usage(status);
CREATE INDEX IF NOT EXISTS idx_usage_equipment ON equipment_usage(equipment_id);
CREATE INDEX IF NOT EXISTS idx_usage_resident ON equipment_usage(resident_id);