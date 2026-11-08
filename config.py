# -*- coding: utf-8 -*-
"""
Конфигурация Flask-приложения.
Используем SQLite — не требует установки MySQL.
"""

import os

class Config:
    """Базовый класс конфигурации."""
    # Секретный ключ для сессий и CSRF-защиты
    SECRET_KEY = os.environ.get('SECRET_KEY', 'technopark-secret-key-change-me-in-production')

    # Путь к файлу SQLite-базы (создастся автоматически)
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATABASE_PATH = os.path.join(BASE_DIR, 'technopark.db')

    # Количество записей на странице (для пагинации)
    ITEMS_PER_PAGE = 20