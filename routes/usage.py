# -*- coding: utf-8 -*-
"""
Модуль учёта использования оборудования.
Позволяет выдавать оборудование резидентам и возвращать его обратно.
При возврате автоматически меняется статус оборудования на 'available'.
"""

from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from database.db import execute_query, execute_insert, execute_update, get_db

usage_bp = Blueprint('usage', __name__, url_prefix='/usage')


@usage_bp.route('/')
@login_required
def list_usage():
    """
    Отображает список всех выдач оборудования.
    Поддерживает фильтрацию по статусу, резиденту и оборудованию.
    """
    status = request.args.get('status', '').strip()
    resident_id = request.args.get('resident_id', type=int)
    equipment_id = request.args.get('equipment_id', type=int)

    base_query = """
        SELECT eu.*, e.name AS equipment_name, e.serial_number, e.category,
               r.full_name AS resident_name
        FROM equipment_usage eu
        LEFT JOIN equipment e ON eu.equipment_id = e.id
        LEFT JOIN residents r ON eu.resident_id = r.id
        WHERE 1=1
    """
    params = []

    if status:
        base_query += " AND eu.status = ?"
        params.append(status)
    if resident_id:
        base_query += " AND eu.resident_id = ?"
        params.append(resident_id)
    if equipment_id:
        base_query += " AND eu.equipment_id = ?"
        params.append(equipment_id)

    base_query += " ORDER BY eu.start_datetime DESC"

    usage_list = execute_query(base_query, params)

    # Списки для фильтров
    residents = execute_query("SELECT id, full_name FROM residents ORDER BY full_name")
    equipment = execute_query("SELECT id, name FROM equipment ORDER BY name")

    return render_template(
        'usage/list.html',
        usage_list=usage_list,
        residents=residents,
        equipment=equipment,
        filters={
            'status': status,
            'resident_id': resident_id,
            'equipment_id': equipment_id
        }
    )


@usage_bp.route('/issue', methods=['GET', 'POST'])
@login_required
def issue_equipment():
    """
    Форма выдачи оборудования резиденту.
    В списке оборудования показываются только единицы со статусом 'available'.
    """
    # Только доступное оборудование
    available_equipment = execute_query("""
        SELECT id, name, serial_number, category 
        FROM equipment 
        WHERE status = 'available'
        ORDER BY name
    """)
    residents = execute_query("SELECT id, full_name FROM residents ORDER BY full_name")

    if request.method == 'POST':
        equipment_id = request.form.get('equipment_id', type=int)
        resident_id = request.form.get('resident_id', type=int)
        start_datetime = request.form.get('start_datetime')
        end_datetime = request.form.get('end_datetime') or None
        purpose = request.form.get('purpose', '').strip()

        # Валидация
        if not equipment_id or not resident_id or not start_datetime:
            flash('Необходимо выбрать оборудование, резидента и указать дату начала', 'danger')
            return render_template(
                'usage/issue_form.html',
                available_equipment=available_equipment,
                residents=residents,
                form_data=request.form
            )

        try:
            db = get_db()
            with db.cursor() as cursor:
                # Создаём запись о выдаче (с указанием кто выдал)
                cursor.execute("""
                    INSERT INTO equipment_usage 
                    (equipment_id, resident_id, start_datetime, end_datetime, purpose, status, issued_by)
                    VALUES (?, ?, ?, ?, ?, 'active', ?)
                """, (equipment_id, resident_id, start_datetime, end_datetime, purpose or None, current_user.id))

                # Меняем статус оборудования на 'in_use'
                cursor.execute(
                    "UPDATE equipment SET status = 'in_use' WHERE id = ?",
                    (equipment_id,)
                )
                # Коммитим транзакцию
                db.commit()

            flash('Оборудование успешно выдано', 'success')
            return redirect(url_for('usage.list_usage'))
        except Exception as e:
            db.rollback()
            flash(f'Ошибка при выдаче: {e}', 'danger')

    return render_template(
        'usage/issue_form.html',
        available_equipment=available_equipment,
        residents=residents,
        form_data={}
    )


@usage_bp.route('/return/<int:id>', methods=['POST'])
@login_required
def return_equipment(id):
    """
    Возврат оборудования — закрывает запись использования.
    Автоматически меняет статус оборудования на 'available'.
    """
    try:
        db = get_db()
        with db.cursor() as cursor:
            # Получаем ID оборудования из записи
            cursor.execute(
                "SELECT equipment_id, status FROM equipment_usage WHERE id = ?",
                (id,)
            )
            row = cursor.fetchone()

            if not row:
                flash('Запись не найдена', 'warning')
                return redirect(url_for('usage.list_usage'))

            if row['status'] != 'active':
                flash('Эта запись уже закрыта', 'warning')
                return redirect(url_for('usage.list_usage'))

            # Устанавливаем дату возврата, меняем статус записи и сохраняем кто принял
            cursor.execute("""
                UPDATE equipment_usage 
                SET end_datetime = ?, status = 'completed', returned_by = ?
                WHERE id = ?
            """, (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), current_user.id, id))

            # Возвращаем оборудованию статус 'available'
            cursor.execute(
                "UPDATE equipment SET status = 'available' WHERE id = ?",
                (row['equipment_id'],)
            )
            db.commit()

        flash('Оборудование успешно возвращено', 'success')
    except Exception as e:
        db.rollback()
        flash(f'Ошибка при возврате: {e}', 'danger')

    return redirect(url_for('usage.list_usage'))