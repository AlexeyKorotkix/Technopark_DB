# -*- coding: utf-8 -*-
"""
Модуль авторизации пользователей.
Использует Flask-Login для управления сессиями.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from database.db import execute_query

# Создаём Blueprint для маршрутов авторизации
auth_bp = Blueprint('auth', __name__)


class User:
    """
    Класс пользователя для Flask-Login.
    Реализует интерфейс, требуемый библиотекой Flask-Login.
    """
    def __init__(self, user_id, username, role):
        self.id = user_id
        self.username = username
        self.role = role
        # Flask-Login требует, чтобы пользователь был аутентифицирован
        self.is_authenticated = True
        self.is_active = True
        self.is_anonymous = False

    def get_id(self):
        """Возвращает ID пользователя в виде строки (требование Flask-Login)."""
        return str(self.id)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Страница входа в систему.
    При GET — показывает форму, при POST — проверяет учётные данные.
    """
    # Если пользователь уже вошёл — перенаправляем на главную
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        # Ищем пользователя в БД
        user_row = execute_query(
            "SELECT id, username, password_hash, role FROM users WHERE username = ?",
            (username,)
        )

        # Проверяем, найден ли пользователь и совпадает ли пароль
        if user_row and check_password_hash(user_row[0]['password_hash'], password):
            row = user_row[0]
            user = User(row['id'], row['username'], row['role'])
            login_user(user)  # создаём сессию
            flash('Вы успешно вошли в систему', 'success')
            # Перенаправляем на страницу, которую запрашивали до входа (или на главную)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard.index'))
        else:
            flash('Неверное имя пользователя или пароль', 'danger')

    return render_template('login.html')


@auth_bp.route('/logout')
@login_required  # только для авторизованных пользователей
def logout():
    """Выход из системы — уничтожает сессию."""
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('auth.login'))