# -*- coding: utf-8 -*-
"""
Модуль для работы с базой данных SQLite.
SQLite — встроенная в Python СУБД, не требует установки сервера.
База хранится в файле technopark.db в корне проекта.
"""

import sqlite3
from flask import g, current_app


def get_db():
    """
    Получает соединение с БД для текущего запроса.
    Если соединения ещё нет — создаёт его и сохраняет в g (контекст Flask).
    """
    if 'db' not in g:
        g.db = sqlite3.connect(current_app.config['DATABASE_PATH'])
        # Возвращаем строки как словари (как DictCursor в PyMySQL)
        g.db.row_factory = sqlite3.Row
        # Включаем поддержку внешних ключей (в SQLite по умолчанию выключена)
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(e=None):
    """
    Закрывает соединение с БД в конце запроса.
    Вызывается автоматически через teardown_appcontext.
    """
    db = g.pop('db', None)
    if db is not None:
        db.close()


def execute_query(query, params=None, fetch=True):
    """
    Универсальная функция для выполнения SQL-запросов.
    
    :param query: SQL-запрос (с плейсхолдерами ?)
    :param params: кортеж или список параметров
    :param fetch: если True — возвращает результат SELECT, иначе None
    :return: список словарей (для SELECT) или None
    """
    db = get_db()
    cursor = db.execute(query, params or ())
    if fetch:
        # Преобразуем sqlite3.Row в обычные словари для удобства
        return [dict(row) for row in cursor.fetchall()]
    return None


def execute_insert(query, params=None):
    """
    Выполняет INSERT-запрос и возвращает ID вставленной записи.
    """
    db = get_db()
    cursor = db.execute(query, params or ())
    db.commit()
    return cursor.lastrowid


def execute_update(query, params=None):
    """
    Выполняет UPDATE/DELETE-запрос и возвращает количество затронутых строк.
    """
    db = get_db()
    cursor = db.execute(query, params or ())
    db.commit()
    return cursor.rowcount


def init_app(app):
    """
    Регистрирует функции открытия/закрытия соединения в Flask-приложении.
    Вызывается из app.py.
    """
    app.teardown_appcontext(close_db)