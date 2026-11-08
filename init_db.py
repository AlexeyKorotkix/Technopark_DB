# -*- coding: utf-8 -*-
"""
Скрипт инициализации базы данных SQLite.
Создаёт таблицы, пользователей и заполняет тестовыми данными.
"""

import os
import sqlite3
from werkzeug.security import generate_password_hash
from config import Config


def init_database():
    """Создаёт базу данных SQLite и все таблицы."""
    print("=" * 60)
    print("Инициализация базы данных TechnoPark DB (SQLite)")
    print("=" * 60)

    db_path = Config.DATABASE_PATH
    print(f"[INFO] Путь к БД: {db_path}")

    try:
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        print("[OK] Подключение к SQLite установлено")

        cursor = conn.cursor()

        # Читаем и выполняем schema.sql
        schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
        if os.path.exists(schema_path):
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
            cursor.executescript(schema_sql)
            print("[OK] Таблицы созданы согласно schema.sql")
        else:
            print(f"[ОШИБКА] Файл schema.sql не найден: {schema_path}")
            return False

        # Создаём пользователей по умолчанию
        users = [
            ('admin', 'admin', 'admin'),
            ('test_user', '123456', 'operator')
        ]
        
        for username, password, role in users:
            cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", (username,))
            if cursor.fetchone()[0] == 0:
                password_hash = generate_password_hash(password)
                cursor.execute(
                    "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                    (username, password_hash, role)
                )
                print(f"[OK] Создан пользователь {username} (пароль: {password})")
            else:
                print(f"[INFO] Пользователь {username} уже существует")

        conn.commit()

        # Заполняем тестовыми данными
        seed_path = os.path.join(os.path.dirname(__file__), 'seed.sql')
        if os.path.exists(seed_path):
            cursor.execute("SELECT COUNT(*) FROM laboratories")
            if cursor.fetchone()[0] == 0:
                with open(seed_path, 'r', encoding='utf-8') as f:
                    seed_sql = f.read()
                cursor.executescript(seed_sql)
                conn.commit()
                print("[OK] Тестовые данные загружены из seed.sql")
            else:
                print("[INFO] Тестовые данные уже существуют — пропуск")

        conn.close()
        print("=" * 60)
        print("[УСПЕХ] База данных успешно инициализирована!")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"[ОШИБКА] При инициализации БД: {e}")
        return False


if __name__ == '__main__':
    init_database()