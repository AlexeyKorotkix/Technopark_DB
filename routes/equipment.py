# -*- coding: utf-8 -*-
"""
Модуль для работы с оборудованием — основной раздел системы.
Поддерживает фильтрацию, поиск, сортировку и пагинацию.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from database.db import execute_query, execute_insert, execute_update, get_db
from flask import current_app

equipment_bp = Blueprint('equipment', __name__, url_prefix='/equipment')


@equipment_bp.route('/')
@login_required
def list_equipment():
    """
    Отображает список оборудования с поддержкой:
    - фильтрации по категории, статусу, лаборатории
    - поиска по названию или серийному номеру
    - сортировки
    - пагинации
    """
    # Получаем параметры фильтрации из GET-запроса
    category = request.args.get('category', '').strip()
    status = request.args.get('status', '').strip()
    laboratory_id = request.args.get('laboratory_id', type=int)
    search = request.args.get('search', '').strip()
    sort_by = request.args.get('sort_by', 'name')
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ITEMS_PER_PAGE']

    # Базовый SQL-запрос
    base_query = """
        SELECT e.*, l.name AS laboratory_name, r.name AS room_name
        FROM equipment e
        LEFT JOIN laboratories l ON e.laboratory_id = l.id
        LEFT JOIN rooms r ON e.room_id = r.id
        WHERE 1=1
    """
    params = []

    # Применяем фильтры
    if category:
        base_query += " AND e.category = ?"
        params.append(category)
    if status:
        base_query += " AND e.status = ?"
        params.append(status)
    if laboratory_id:
        base_query += " AND e.laboratory_id = ?"
        params.append(laboratory_id)
    if search:
        base_query += " AND (e.name LIKE ? OR e.serial_number LIKE ?)"
        params.extend([f'%{search}%', f'%{search}%'])

    # Применяем сортировку (безопасно — только разрешённые поля)
    allowed_sorts = {
        'name': 'e.name',
        'category': 'e.category',
        'status': 'e.status',
        'purchase_date': 'e.purchase_date',
        'laboratory': 'l.name'
    }
    order_col = allowed_sorts.get(sort_by, 'e.name')
    base_query += f" ORDER BY {order_col}"

    # Считаем общее количество записей (для пагинации)
    count_query = f"SELECT COUNT(*) AS cnt FROM ({base_query}) AS t"
    total = execute_query(count_query, params)[0]['cnt']

    # Добавляем LIMIT и OFFSET для пагинации
    offset = (page - 1) * per_page
    base_query += " LIMIT ? OFFSET ?"
    params.extend([per_page, offset])

    # Выполняем запрос
    equipment_list = execute_query(base_query, params)

    # Получаем списки для фильтров
    categories = execute_query("SELECT DISTINCT category FROM equipment WHERE category IS NOT NULL ORDER BY category")
    laboratories = execute_query("SELECT id, name FROM laboratories ORDER BY name")

    # Рассчитываем количество страниц
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1

    return render_template(
        'equipment/list.html',
        equipment_list=equipment_list,
        categories=categories,
        laboratories=laboratories,
        filters={
            'category': category,
            'status': status,
            'laboratory_id': laboratory_id,
            'search': search,
            'sort_by': sort_by
        },
        pagination={
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': total_pages
        }
    )


@equipment_bp.route('/<int:id>')
@login_required
def view_equipment(id):
    """Детальный просмотр оборудования."""
    eq = execute_query("""
        SELECT e.*, l.name AS laboratory_name, r.name AS room_name
        FROM equipment e
        LEFT JOIN laboratories l ON e.laboratory_id = l.id
        LEFT JOIN rooms r ON e.room_id = r.id
        WHERE e.id = ?
    """, (id,))

    if not eq:
        flash('Оборудование не найдено', 'warning')
        return redirect(url_for('equipment.list_equipment'))

    # Получаем историю использования этого оборудования
    usage_history = execute_query("""
        SELECT eu.*, r.full_name AS resident_name
        FROM equipment_usage eu
        LEFT JOIN residents r ON eu.resident_id = r.id
        WHERE eu.equipment_id = ?
        ORDER BY eu.start_datetime DESC
        LIMIT 20
    """, (id,))

    return render_template(
        'equipment/view.html',
        equipment=eq[0],
        usage_history=usage_history
    )


@equipment_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_equipment():
    """Добавление новой единицы оборудования."""
    laboratories = execute_query("SELECT id, name FROM laboratories ORDER BY name")
    rooms = execute_query("""
        SELECT r.id, r.name, l.name AS laboratory_name
        FROM rooms r
        LEFT JOIN laboratories l ON r.laboratory_id = l.id
        ORDER BY l.name, r.name
    """)

    if request.method == 'POST':
        # Собираем данные из формы
        data = {
            'name': request.form.get('name', '').strip(),
            'category': request.form.get('category', '').strip(),
            'serial_number': request.form.get('serial_number', '').strip(),
            'manufacturer': request.form.get('manufacturer', '').strip(),
            'purchase_date': request.form.get('purchase_date') or None,
            'purchase_price': request.form.get('purchase_price') or None,
            'status': request.form.get('status', 'available'),
            'room_id': request.form.get('room_id', type=int),
            'laboratory_id': request.form.get('laboratory_id', type=int),
            'notes': request.form.get('notes', '').strip()
        }

        # Валидация
        if not data['name']:
            flash('Название оборудования обязательно', 'danger')
            return render_template(
                'equipment/form.html', equipment=data, laboratories=laboratories,
                rooms=rooms, action='add'
            )

        try:
            execute_insert("""
                INSERT INTO equipment 
                (name, category, serial_number, manufacturer, purchase_date, 
                 purchase_price, status, room_id, laboratory_id, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['name'], data['category'] or None,
                data['serial_number'] or None, data['manufacturer'] or None,
                data['purchase_date'], data['purchase_price'],
                data['status'], data['room_id'], data['laboratory_id'],
                data['notes'] or None
            ))
            flash('Оборудование успешно добавлено', 'success')
            return redirect(url_for('equipment.list_equipment'))
        except Exception as e:
            flash(f'Ошибка при добавлении: {e}', 'danger')

    return render_template(
        'equipment/form.html', equipment=None, laboratories=laboratories,
        rooms=rooms, action='add'
    )


@equipment_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_equipment(id):
    """Редактирование оборудования."""
    eq = execute_query("SELECT * FROM equipment WHERE id = ?", (id,))
    if not eq:
        flash('Оборудование не найдено', 'warning')
        return redirect(url_for('equipment.list_equipment'))
    eq = eq[0]

    laboratories = execute_query("SELECT id, name FROM laboratories ORDER BY name")
    rooms = execute_query("""
        SELECT r.id, r.name, l.name AS laboratory_name
        FROM rooms r
        LEFT JOIN laboratories l ON r.laboratory_id = l.id
        ORDER BY l.name, r.name
    """)

    if request.method == 'POST':
        data = {
            'name': request.form.get('name', '').strip(),
            'category': request.form.get('category', '').strip(),
            'serial_number': request.form.get('serial_number', '').strip(),
            'manufacturer': request.form.get('manufacturer', '').strip(),
            'purchase_date': request.form.get('purchase_date') or None,
            'purchase_price': request.form.get('purchase_price') or None,
            'status': request.form.get('status', 'available'),
            'room_id': request.form.get('room_id', type=int),
            'laboratory_id': request.form.get('laboratory_id', type=int),
            'notes': request.form.get('notes', '').strip()
        }

        if not data['name']:
            flash('Название оборудования обязательно', 'danger')
            return render_template(
                'equipment/form.html', equipment=data, laboratories=laboratories,
                rooms=rooms, action='edit'
            )

        try:
            execute_update("""
                UPDATE equipment 
                SET name=?, category=?, serial_number=?, manufacturer=?,
                    purchase_date=?, purchase_price=?, status=?,
                    room_id=?, laboratory_id=?, notes=?
                WHERE id=?
            """, (
                data['name'], data['category'] or None,
                data['serial_number'] or None, data['manufacturer'] or None,
                data['purchase_date'], data['purchase_price'],
                data['status'], data['room_id'], data['laboratory_id'],
                data['notes'] or None, id
            ))
            flash('Оборудование успешно обновлено', 'success')
            return redirect(url_for('equipment.list_equipment'))
        except Exception as e:
            flash(f'Ошибка при обновлении: {e}', 'danger')

    return render_template(
        'equipment/form.html', equipment=eq, laboratories=laboratories,
        rooms=rooms, action='edit'
    )


@equipment_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_equipment(id):
    """Удаление оборудования."""
    try:
        execute_update("DELETE FROM equipment WHERE id = ?", (id,))
        flash('Оборудование успешно удалено', 'success')
    except Exception as e:
        flash(f'Не удалось удалить: {e}', 'danger')
    return redirect(url_for('equipment.list_equipment'))