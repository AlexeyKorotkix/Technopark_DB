# -*- coding: utf-8 -*-
"""
SQL-консоль — позволяет выполнять произвольные SELECT-запросы к БД.
Предназначена для демонстрации в курсовой работе.
ВАЖНО: разрешены только SELECT-запросы для безопасности.
Доступно только пользователям с ролью 'admin'.
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from database.db import execute_query

sql_console_bp = Blueprint('sql_console', __name__, url_prefix='/sql')


@sql_console_bp.route('/', methods=['GET', 'POST'])
@login_required
def console():
    """
    Страница SQL-консоли.
    Принимает SQL-запрос, проверяет его безопасность и выполняет.
    Доступно только администраторам.
    """
    # Проверка роли — SQL-консоль только для admin
    if current_user.role != 'admin':
        flash('SQL-консоль доступна только администраторам', 'warning')
        return redirect(url_for('dashboard.index'))

    query = ''
    results = None
    columns = None
    error = None

    if request.method == 'POST':
        query = request.form.get('query', '').strip()

        # Проверка: разрешены только SELECT-запросы
        query_upper = query.upper().strip()
        if not query_upper.startswith('SELECT') and not query_upper.startswith('SHOW') \
                and not query_upper.startswith('DESCRIBE') and not query_upper.startswith('PRAGMA'):
            error = 'Разрешены только SELECT, SHOW, DESCRIBE и PRAGMA запросы'
            flash(error, 'danger')
        else:
            # Проверка на опасные ключевые слова (дополнительная защита)
            forbidden = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'CREATE', 'TRUNCATE', 'REPLACE']
            forbidden_found = False
            for word in forbidden:
                if word in query_upper:
                    error = f'Обнаружено запрещённое ключевое слово: {word}'
                    flash(error, 'danger')
                    forbidden_found = True
                    break
            
            if not forbidden_found:
                try:
                    results = execute_query(query)
                    if results:
                        columns = list(results[0].keys())
                    else:
                        columns = []
                    flash(f'Запрос выполнен успешно. Найдено записей: {len(results) if results else 0}', 'success')
                except Exception as e:
                    error = f'Ошибка выполнения запроса: {e}'
                    flash(error, 'danger')

    return render_template(
        'sql_console.html',
        query=query,
        results=results,
        columns=columns,
        error=error
    )