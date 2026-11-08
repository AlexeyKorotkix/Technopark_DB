# -*- coding: utf-8 -*-
"""
Модуль для работы с резидентами (пользователями технопарка).
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from database.db import execute_query, execute_insert, execute_update

residents_bp = Blueprint('residents', __name__, url_prefix='/residents')


@residents_bp.route('/')
@login_required
def list_residents():
    """Отображает список всех резидентов."""
    residents = execute_query("""
        SELECT * FROM residents 
        ORDER BY full_name
    """)
    return render_template('residents/list.html', residents=residents)


@residents_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_resident():
    """Добавление нового резидента."""
    if request.method == 'POST':
        data = {
            'full_name': request.form.get('full_name', '').strip(),
            'email': request.form.get('email', '').strip(),
            'phone': request.form.get('phone', '').strip(),
            'organization': request.form.get('organization', '').strip(),
            'role': request.form.get('role', 'student'),
            'registration_date': request.form.get('registration_date') or None
        }

        if not data['full_name']:
            flash('ФИО обязательно', 'danger')
            return render_template('residents/form.html', resident=data, action='add')

        try:
            execute_insert("""
                INSERT INTO residents 
                (full_name, email, phone, organization, role, registration_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                data['full_name'], data['email'] or None,
                data['phone'] or None, data['organization'] or None,
                data['role'], data['registration_date']
            ))
            flash('Резидент успешно добавлен', 'success')
            return redirect(url_for('residents.list_residents'))
        except Exception as e:
            flash(f'Ошибка при добавлении: {e}', 'danger')

    return render_template('residents/form.html', resident=None, action='add')


@residents_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_resident(id):
    """Редактирование резидента."""
    res = execute_query("SELECT * FROM residents WHERE id = ?", (id,))
    if not res:
        flash('Резидент не найден', 'warning')
        return redirect(url_for('residents.list_residents'))
    res = res[0]

    if request.method == 'POST':
        data = {
            'full_name': request.form.get('full_name', '').strip(),
            'email': request.form.get('email', '').strip(),
            'phone': request.form.get('phone', '').strip(),
            'organization': request.form.get('organization', '').strip(),
            'role': request.form.get('role', 'student'),
            'registration_date': request.form.get('registration_date') or None
        }

        if not data['full_name']:
            flash('ФИО обязательно', 'danger')
            return render_template('residents/form.html', resident=data, action='edit')

        try:
            execute_update("""
                UPDATE residents 
                SET full_name=?, email=?, phone=?, organization=?, role=?,
                    registration_date=?
                WHERE id=?
            """, (
                data['full_name'], data['email'] or None,
                data['phone'] or None, data['organization'] or None,
                data['role'], data['registration_date'], id
            ))
            flash('Резидент успешно обновлён', 'success')
            return redirect(url_for('residents.list_residents'))
        except Exception as e:
            flash(f'Ошибка при обновлении: {e}', 'danger')

    return render_template('residents/form.html', resident=res, action='edit')


@residents_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_resident(id):
    """Удаление резидента."""
    try:
        execute_update("DELETE FROM residents WHERE id = ?", (id,))
        flash('Резидент успешно удалён', 'success')
    except Exception as e:
        flash(f'Не удалось удалить: {e}', 'danger')
    return redirect(url_for('residents.list_residents'))


@residents_bp.route('/<int:id>/history')
@login_required
def history(id):
    """Просмотр истории использования оборудования резидентом."""
    res = execute_query("SELECT * FROM residents WHERE id = ?", (id,))
    if not res:
        flash('Резидент не найден', 'warning')
        return redirect(url_for('residents.list_residents'))
    res = res[0]

    history = execute_query("""
        SELECT eu.*, e.name AS equipment_name, e.serial_number, e.category
        FROM equipment_usage eu
        LEFT JOIN equipment e ON eu.equipment_id = e.id
        WHERE eu.resident_id = ?
        ORDER BY eu.start_datetime DESC
    """, (id,))

    return render_template('residents/history.html', resident=res, history=history)