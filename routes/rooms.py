# -*- coding: utf-8 -*-
"""
Модуль для работы с помещениями.
Помещения привязаны к лабораториям через laboratory_id.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from database.db import execute_query, execute_insert, execute_update

rooms_bp = Blueprint('rooms', __name__, url_prefix='/rooms')


@rooms_bp.route('/')
@login_required
def list_rooms():
    """
    Отображает список всех помещений с названием лаборатории.
    Поддерживает фильтрацию по лаборатории через GET-параметр ?laboratory_id=...
    """
    laboratory_id = request.args.get('laboratory_id', type=int)

    if laboratory_id:
        rooms = execute_query("""
            SELECT r.*, l.name AS laboratory_name
            FROM rooms r
            LEFT JOIN laboratories l ON r.laboratory_id = l.id
            WHERE r.laboratory_id = ?
            ORDER BY l.name, r.name
        """, (laboratory_id,))
    else:
        rooms = execute_query("""
            SELECT r.*, l.name AS laboratory_name
            FROM rooms r
            LEFT JOIN laboratories l ON r.laboratory_id = l.id
            ORDER BY l.name, r.name
        """)

    # Получаем список всех лабораторий для фильтра
    laboratories = execute_query("SELECT id, name FROM laboratories ORDER BY name")

    return render_template(
        'rooms/list.html',
        rooms=rooms,
        laboratories=laboratories,
        current_lab_id=laboratory_id
    )


@rooms_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_room():
    """Добавление нового помещения."""
    laboratories = execute_query("SELECT id, name FROM laboratories ORDER BY name")

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        laboratory_id = request.form.get('laboratory_id', type=int)
        capacity = request.form.get('capacity', type=int)
        floor = request.form.get('floor', type=int)

        if not name or not laboratory_id:
            flash('Название помещения и лаборатория обязательны', 'danger')
            return render_template(
                'rooms/form.html', room=None, laboratories=laboratories, action='add'
            )

        try:
            execute_insert(
                "INSERT INTO rooms (name, laboratory_id, capacity, floor) VALUES (?, ?, ?, ?)",
                (name, laboratory_id, capacity, floor)
            )
            flash('Помещение успешно добавлено', 'success')
            return redirect(url_for('rooms.list_rooms'))
        except Exception as e:
            flash(f'Ошибка при добавлении: {e}', 'danger')

    return render_template('rooms/form.html', room=None, laboratories=laboratories, action='add')


@rooms_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_room(id):
    """Редактирование помещения."""
    room = execute_query("SELECT * FROM rooms WHERE id = ?", (id,))
    if not room:
        flash('Помещение не найдено', 'warning')
        return redirect(url_for('rooms.list_rooms'))
    room = room[0]

    laboratories = execute_query("SELECT id, name FROM laboratories ORDER BY name")

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        laboratory_id = request.form.get('laboratory_id', type=int)
        capacity = request.form.get('capacity', type=int)
        floor = request.form.get('floor', type=int)

        if not name or not laboratory_id:
            flash('Название помещения и лаборатория обязательны', 'danger')
            return render_template(
                'rooms/form.html', room=room, laboratories=laboratories, action='edit'
            )

        try:
            execute_update(
                """UPDATE rooms 
                   SET name=?, laboratory_id=?, capacity=?, floor=? 
                   WHERE id=?""",
                (name, laboratory_id, capacity, floor, id)
            )
            flash('Помещение успешно обновлено', 'success')
            return redirect(url_for('rooms.list_rooms'))
        except Exception as e:
            flash(f'Ошибка при обновлении: {e}', 'danger')

    return render_template('rooms/form.html', room=room, laboratories=laboratories, action='edit')


@rooms_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_room(id):
    """Удаление помещения."""
    try:
        execute_update("DELETE FROM rooms WHERE id = ?", (id,))
        flash('Помещение успешно удалено', 'success')
    except Exception as e:
        flash(f'Не удалось удалить: {e}', 'danger')
    return redirect(url_for('rooms.list_rooms'))