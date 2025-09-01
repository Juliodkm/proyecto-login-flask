
from flask import render_template, request, redirect, url_for, flash, session
from . import auth_bp
from ..services.auth_service import AuthService

auth_service = AuthService()

@auth_bp.route('/')
def index():
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user_data = request.form.to_dict()
        user, message = auth_service.register_user(user_data)
        
        if user:
            flash(message, 'success')
            return redirect(url_for('auth.login'))
        else:
            flash(message, 'error')
            return redirect(url_for('auth.register'))

    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = auth_service.login_user(username, password)

        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            if user.rol == 'admin':
                return redirect(url_for('admin.admin_dashboard'))
            return redirect(url_for('main.dashboard'))
        else:
            flash('Usuario o contraseña incorrectos.', 'error')
            
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('Has cerrado sesión.', 'success')
    return redirect(url_for('auth.login'))
