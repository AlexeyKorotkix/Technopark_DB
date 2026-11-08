# -*- coding: utf-8 -*-
"""
Модуль главной страницы (Dashboard).
Отображает краткую статистику по системе.
"""

from flask import Blueprint, render_template
from flask_login import login_required
from database.db import execute_query

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required  # требуем авторизацию для доступа к главной
def index():
    """
    Главная страница — Dashboard.
    Собирает статистику из БД и передаёт в шаблон.
    """
    # Считаем количество лабораторий
    labs_count = execute_query("SELECT COUNT(*) AS cnt FROM laboratories")[0]['cnt']

    # Считаем количество оборудования (общее и по статусам)
    equipment_stats = execute_query("""
        SELECT 
            COUNT(*) AS total,
            SUM(CASE WHEN status = 'available' THEN 1 ELSE 0 END) AS available,
            SUM(CASE WHEN status = 'in_use' THEN 1 ELSE 0 END) AS in_use,
            SUM(CASE WHEN status = 'maintenance' THEN 1 ELSE 0 END) AS maintenance,
            SUM(CASE WHEN status = 'decommissioned' THEN 1 ELSE 0 END) AS decommissioned
        FROM equipment
    """)[0]

    # Считаем количество резидентов
    residents_count = execute_query("SELECT COUNT(*) AS cnt FROM residents")[0]['cnt']

    # Считаем активные выдачи оборудования
    active_usage = execute_query("""
        SELECT COUNT(*) AS cnt FROM equipment_usage WHERE status = 'active'
    """)[0]['cnt']

    return render_template(
        'dashboard.html',
        labs_count=labs_count,
        equipment_stats=equipment_stats,
        residents_count=residents_count,
        active_usage=active_usage
    )