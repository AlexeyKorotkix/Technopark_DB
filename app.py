# -*- coding: utf-8 -*-
"""
Главный файл Flask-приложения "СУБД для лаборатории технопарка".
"""

from flask import Flask, render_template
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from datetime import datetime  # <-- ДОБАВЛЕНО для работы с датами
from config import Config
from database.db import init_app as init_db
from routes import register_blueprints
from routes.auth import User
from database.db import execute_query


def create_app():
    """Фабрика Flask-приложения."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Инициализируем защиту от CSRF
    csrf = CSRFProtect(app)

    # Инициализируем работу с БД
    init_db(app)

    # Настраиваем Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Пожалуйста, войдите в систему для доступа к этой странице'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        user_row = execute_query(
            "SELECT id, username, role FROM users WHERE id = ?",
            (user_id,)
        )
        if user_row:
            row = user_row[0]
            return User(row['id'], row['username'], row['role'])
        return None

    # =========================================================
    # ДОБАВЛЕНО: Умный фильтр для форматирования дат в шаблонах
    # Он работает и с объектами datetime, и со строками из SQLite
    # =========================================================
    @app.template_filter('format_dt')
    def format_dt_filter(value, fmt='%d.%m.%Y'):
        if not value:
            return '—'
        if isinstance(value, str):
            try:
                # Пытаемся распарсить как дату и время (YYYY-MM-DD HH:MM:SS)
                return datetime.strptime(value, '%Y-%m-%d %H:%M:%S').strftime(fmt)
            except ValueError:
                try:
                    # Пытаемся распарсить как просто дату (YYYY-MM-DD)
                    return datetime.strptime(value, '%Y-%m-%d').strftime(fmt)
                except ValueError:
                    return value  # Если не вышло, возвращаем строку как есть
        return value.strftime(fmt)
    # =========================================================

    # Регистрируем все маршруты (Blueprint'ы)
    register_blueprints(app)

    # Обработчики ошибок
    @app.errorhandler(404)
    def not_found(error):
        return render_template('error.html', error_code=404,
                               error_message='Страница не найдена'), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template('error.html', error_code=500,
                               error_message='Внутренняя ошибка сервера'), 500

    return app


# Создаём экземпляр приложения
app = create_app()


if __name__ == '__main__':
    print("=" * 60)
    print("Приложение 'СУБД лаборатории технопарка' запущено")
    print("Откройте в браузере: http://127.0.0.1:5000")
    print("Логин: admin / Пароль: admin")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)