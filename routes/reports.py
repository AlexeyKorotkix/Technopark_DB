# -*- coding: utf-8 -*-
"""
Модуль отчётов — аналог отчётов MS Access.
Позволяет формировать отчёты по оборудованию, резидентам, использованию
и экспортировать их в CSV.
"""

import csv
import io
from datetime import datetime
from flask import Blueprint, render_template, request, Response, flash, redirect, url_for
from flask_login import login_required, current_user
from database.db import execute_query

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')


# Декоратор для проверки роли администратора
def admin_required(f):
    """Ограничение доступа только для администраторов."""
    from functools import wraps
    from flask import abort
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role != 'admin':
            flash('Доступ запрещён. Требуются права администратора.', 'danger')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function


@reports_bp.route('/')
@login_required
def index():
    """Главная страница модуля отчётов — список доступных отчётов."""
    # Статистика для превью отчётов
    stats = {
        'equipment_total': execute_query("SELECT COUNT(*) AS cnt FROM equipment")[0]['cnt'],
        'equipment_by_status': execute_query("""
            SELECT status, COUNT(*) AS cnt FROM equipment GROUP BY status
        """),
        'residents_total': execute_query("SELECT COUNT(*) AS cnt FROM residents")[0]['cnt'],
        'usage_active': execute_query("""
            SELECT COUNT(*) AS cnt FROM equipment_usage WHERE status = 'active'
        """)[0]['cnt'],
        'usage_completed': execute_query("""
            SELECT COUNT(*) AS cnt FROM equipment_usage WHERE status = 'completed'
        """)[0]['cnt'],
    }
    return render_template('reports/index.html', stats=stats)


@reports_bp.route('/equipment')
@login_required
def equipment_report():
    """Отчёт по оборудованию с фильтрацией."""
    category = request.args.get('category', '').strip()
    status = request.args.get('status', '').strip()
    laboratory = request.args.get('laboratory', '').strip()
    
    query = """
        SELECT e.name, e.category, e.serial_number, e.manufacturer,
               e.purchase_date, e.purchase_price, e.status, e.notes,
               l.name AS laboratory_name, r.name AS room_name
        FROM equipment e
        LEFT JOIN rooms r ON e.room_id = r.id
        LEFT JOIN laboratories l ON r.laboratory_id = l.id
        WHERE 1=1
    """
    params = []
    
    if category:
        query += " AND e.category = ?"
        params.append(category)
    if status:
        query += " AND e.status = ?"
        params.append(status)
    if laboratory:
        query += " AND l.name LIKE ?"
        params.append(f'%{laboratory}%')
    
    query += " ORDER BY e.category, e.name"
    
    equipment = execute_query(query, params)
    categories = execute_query("SELECT DISTINCT category FROM equipment WHERE category IS NOT NULL ORDER BY category")
    laboratories = execute_query("SELECT DISTINCT name FROM laboratories ORDER BY name")
    
    return render_template(
        'reports/equipment.html',
        equipment=equipment,
        categories=categories,
        laboratories=laboratories,
        filters={'category': category, 'status': status, 'laboratory': laboratory}
    )


@reports_bp.route('/equipment/export')
@login_required
def export_equipment():
    """Экспорт отчёта по оборудованию в CSV."""
    equipment = execute_query("""
        SELECT e.name, e.category, e.serial_number, e.manufacturer,
               e.purchase_date, e.purchase_price, e.status,
               l.name AS laboratory_name, r.name AS room_name
        FROM equipment e
        LEFT JOIN rooms r ON e.room_id = r.id
        LEFT JOIN laboratories l ON r.laboratory_id = l.id
        ORDER BY e.category, e.name
    """)
    
    output = io.StringIO()
    output.write('\ufeff')  # BOM для корректного отображения кириллицы в Excel
    writer = csv.writer(output, delimiter=';')
    writer.writerow(['Название', 'Категория', 'Серийный номер', 'Производитель',
                     'Дата покупки', 'Цена', 'Статус', 'Лаборатория', 'Помещение'])
    
    status_names = {
        'available': 'Доступно',
        'in_use': 'В использовании',
        'maintenance': 'В ремонте',
        'decommissioned': 'Списано'
    }
    
    for eq in equipment:
        writer.writerow([
            eq['name'], eq['category'] or '', eq['serial_number'] or '',
            eq['manufacturer'] or '', eq['purchase_date'] or '',
            eq['purchase_price'] or '', status_names.get(eq['status'], eq['status']),
            eq['laboratory_name'] or '', eq['room_name'] or ''
        ])
    
    response = Response(
        output.getvalue(),
        mimetype='text/csv; charset=utf-8',
        headers={'Content-Disposition': 'attachment; filename=equipment_report.csv'}
    )
    return response


@reports_bp.route('/residents')
@login_required
def residents_report():
    """Отчёт по резидентам."""
    role = request.args.get('role', '').strip()
    
    query = """
        SELECT full_name, email, phone, organization, role, registration_date
        FROM residents WHERE 1=1
    """
    params = []
    
    if role:
        query += " AND role = ?"
        params.append(role)
    
    query += " ORDER BY full_name"
    
    residents = execute_query(query, params)
    
    role_names = {
        'student': 'Студент',
        'researcher': 'Исследователь',
        'engineer': 'Инженер',
        'manager': 'Менеджер'
    }
    
    return render_template(
        'reports/residents.html',
        residents=residents,
        role_names=role_names,
        filters={'role': role}
    )


@reports_bp.route('/residents/export')
@login_required
def export_residents():
    """Экспорт отчёта по резидентам в CSV."""
    residents = execute_query("""
        SELECT full_name, email, phone, organization, role, registration_date
        FROM residents ORDER BY full_name
    """)
    
    output = io.StringIO()
    output.write('\ufeff')
    writer = csv.writer(output, delimiter=';')
    writer.writerow(['ФИО', 'Email', 'Телефон', 'Организация', 'Роль', 'Дата регистрации'])
    
    role_names = {
        'student': 'Студент',
        'researcher': 'Исследователь',
        'engineer': 'Инженер',
        'manager': 'Менеджер'
    }
    
    for r in residents:
        writer.writerow([
            r['full_name'], r['email'] or '', r['phone'] or '',
            r['organization'] or '', role_names.get(r['role'], r['role']),
            r['registration_date'] or ''
        ])
    
    response = Response(
        output.getvalue(),
        mimetype='text/csv; charset=utf-8',
        headers={'Content-Disposition': 'attachment; filename=residents_report.csv'}
    )
    return response


@reports_bp.route('/usage')
@login_required
def usage_report():
    """Отчёт по использованию оборудования с фильтрацией по датам."""
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()
    status = request.args.get('status', '').strip()
    
    query = """
        SELECT eu.start_datetime, eu.end_datetime, eu.purpose, eu.status,
               e.name AS equipment_name, e.category, e.serial_number,
               r.full_name AS resident_name, r.organization
        FROM equipment_usage eu
        LEFT JOIN equipment e ON eu.equipment_id = e.id
        LEFT JOIN residents r ON eu.resident_id = r.id
        WHERE 1=1
    """
    params = []
    
    if date_from:
        query += " AND eu.start_datetime >= ?"
        params.append(date_from)
    if date_to:
        query += " AND eu.start_datetime <= ?"
        params.append(date_to + ' 23:59:59')
    if status:
        query += " AND eu.status = ?"
        params.append(status)
    
    query += " ORDER BY eu.start_datetime DESC"
    
    usage = execute_query(query, params)
    
    status_names = {
        'active': 'Активна',
        'completed': 'Завершена',
        'cancelled': 'Отменена'
    }
    
    return render_template(
        'reports/usage.html',
        usage=usage,
        status_names=status_names,
        filters={'date_from': date_from, 'date_to': date_to, 'status': status}
    )


@reports_bp.route('/usage/export')
@login_required
def export_usage():
    """Экспорт отчёта по использованию в CSV."""
    usage = execute_query("""
        SELECT eu.start_datetime, eu.end_datetime, eu.purpose, eu.status,
               e.name AS equipment_name, e.category,
               r.full_name AS resident_name, r.organization
        FROM equipment_usage eu
        LEFT JOIN equipment e ON eu.equipment_id = e.id
        LEFT JOIN residents r ON eu.resident_id = r.id
        ORDER BY eu.start_datetime DESC
    """)
    
    output = io.StringIO()
    output.write('\ufeff')
    writer = csv.writer(output, delimiter=';')
    writer.writerow(['Дата начала', 'Дата окончания', 'Оборудование', 'Категория',
                     'Резидент', 'Организация', 'Цель', 'Статус'])
    
    status_names = {
        'active': 'Активна',
        'completed': 'Завершена',
        'cancelled': 'Отменена'
    }
    
    for u in usage:
        writer.writerow([
            u['start_datetime'] or '', u['end_datetime'] or '',
            u['equipment_name'] or '', u['category'] or '',
            u['resident_name'] or '', u['organization'] or '',
            u['purpose'] or '', status_names.get(u['status'], u['status'])
        ])
    
    response = Response(
        output.getvalue(),
        mimetype='text/csv; charset=utf-8',
        headers={'Content-Disposition': 'attachment; filename=usage_report.csv'}
    )
    return response


@reports_bp.route('/summary')
@login_required
def summary_report():
    """Сводный отчёт — общая статистика по системе."""
    # Статистика по оборудованию
    equipment_stats = execute_query("""
        SELECT 
            COUNT(*) AS total,
            SUM(CASE WHEN status = 'available' THEN 1 ELSE 0 END) AS available,
            SUM(CASE WHEN status = 'in_use' THEN 1 ELSE 0 END) AS in_use,
            SUM(CASE WHEN status = 'maintenance' THEN 1 ELSE 0 END) AS maintenance,
            SUM(CASE WHEN status = 'decommissioned' THEN 1 ELSE 0 END) AS decommissioned,
            SUM(purchase_price) AS total_value
        FROM equipment
    """)[0]
    
    # Оборудование по категориям
    equipment_by_category = execute_query("""
        SELECT category, COUNT(*) AS cnt, SUM(purchase_price) AS total_value
        FROM equipment
        WHERE category IS NOT NULL
        GROUP BY category
        ORDER BY cnt DESC
    """)
    
    # Резиденты по ролям
    residents_by_role = execute_query("""
        SELECT role, COUNT(*) AS cnt
        FROM residents
        GROUP BY role
        ORDER BY cnt DESC
    """)
    
    # Использование по месяцам (последние 6 месяцев)
    usage_by_month = execute_query("""
        SELECT strftime('%Y-%m', start_datetime) AS month, COUNT(*) AS cnt
        FROM equipment_usage
        WHERE start_datetime >= date('now', '-6 months')
        GROUP BY month
        ORDER BY month
    """)
    
    # Лаборатории и их оборудование
    labs_stats = execute_query("""
        SELECT l.name, COUNT(e.id) AS equipment_count,
               SUM(CASE WHEN e.status = 'available' THEN 1 ELSE 0 END) AS available
        FROM laboratories l
        LEFT JOIN rooms r ON r.laboratory_id = l.id
        LEFT JOIN equipment e ON e.room_id = r.id
        GROUP BY l.id
        ORDER BY equipment_count DESC
    """)
    
    role_names = {
        'student': 'Студент',
        'researcher': 'Исследователь',
        'engineer': 'Инженер',
        'manager': 'Менеджер'
    }
    
    status_names = {
        'available': 'Доступно',
        'in_use': 'В использовании',
        'maintenance': 'В ремонте',
        'decommissioned': 'Списано'
    }
    
    return render_template(
        'reports/summary.html',
        equipment_stats=equipment_stats,
        equipment_by_category=equipment_by_category,
        residents_by_role=residents_by_role,
        usage_by_month=usage_by_month,
        labs_stats=labs_stats,
        role_names=role_names,
        status_names=status_names
    )