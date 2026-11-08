# -*- coding: utf-8 -*-
"""
Пакет маршрутов (Blueprints).
"""

from .auth import auth_bp
from .dashboard import dashboard_bp
from .laboratories import laboratories_bp
from .equipment import equipment_bp
from .residents import residents_bp
from .usage import usage_bp
from .sql_console import sql_console_bp
from .reports import reports_bp  # <-- ДОБАВЛЕНО: модуль отчётов


def register_blueprints(app):
    """Регистрирует все Blueprint'ы в Flask-приложении."""
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(laboratories_bp)
    app.register_blueprint(equipment_bp)
    app.register_blueprint(residents_bp)
    app.register_blueprint(usage_bp)
    app.register_blueprint(sql_console_bp)
    app.register_blueprint(reports_bp)  # <-- ДОБАВЛЕНО