# -*- coding: utf-8 -*-
"""
Модуль для работы с лабораториями.
Реализует CRUD-операции: создание, чтение, обновление, удаление.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from database.db import execute_query, execute_insert, execute_update

laboratories_bp = Blueprint('laboratories', __name__, url_prefix='/laboratories')


@laboratories_bp.route('/')
@login_required
def list_laboratories():
    """Отображает список всех лабораторий."""
    labs = execute_query("""
        SELECT id, name, location, description, created_at 
        FROM laboratories 
        ORDER BY name
    """)
    return render_template('laboratories/list.html', laboratories=labs)


@laboratories_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_laboratory():
    """Добавление новой лаборатории."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        location = request.form.get('location', '').strip()
        description = request.form.get('description', '').strip()

        # Простая валидация — название обязательно
        if not name:
            flash('Название лаборатории обязательно', 'danger')
            return render_template('laboratories/form.html', laboratory=None, action='add')

        try:
            execute_insert(
                "INSERT INTO laboratories (name, location, description) VALUES (?, ?, ?)",
                (name, location or None, description or None)
            )
            flash('Лаборатория успешно добавлена', 'success')
            return redirect(url_for('laboratories.list_laboratories'))
        except Exception as e:
            flash(f'Ошибка при добавлении: {e}', 'danger')

    return render_template('laboratories/form.html', laboratory=None, action='add')


@laboratories_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_laboratory(id):
    """Редактирование существующей лаборатории."""
    # Получаем данные лаборатории
    lab = execute_query("SELECT * FROM laboratories WHERE id = ?", (id,))
    if not lab:
        flash('Лаборатория не найдена', 'warning')
        return redirect(url_for('laboratories.list_laboratories'))
    lab = lab[0]

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        location = request.form.get('location', '').strip()
        description = request.form.get('description', '').strip()

        if not name:
            flash('Название лаборатории обязательно', 'danger')
            return render_template('laboratories/form.html', laboratory=lab, action='edit')

        try:
            execute_update(
                "UPDATE laboratories SET name=?, location=?, description=? WHERE id=?",
                (name, location or None, description or None, id)
            )
            flash('Лаборатория успешно обновлена', 'success')
            return redirect(url_for('laboratories.list_laboratories'))
        except Exception as e:
            flash(f'Ошибка при обновлении: {e}', 'danger')

    return render_template('laboratories/form.html', laboratory=lab, action='edit')


@laboratories_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_laboratory(id):
    """Удаление лаборатории."""
    try:
        execute_update("DELETE FROM laboratories WHERE id = ?", (id,))
        flash('Лаборатория успешно удалена', 'success')
    except Exception as e:
        # Если есть связанные записи (помещения, оборудование) — удаление не сработает
        flash(f'Не удалось удалить: {e}', 'danger')
    return redirect(url_for('laboratories.list_laboratories'))