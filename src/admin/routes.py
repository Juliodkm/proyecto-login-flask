

from flask import render_template, redirect, url_for, session, flash, request, jsonify
from functools import wraps
from . import admin_bp
from ..services.user_service import UserService
from ..services.report_service import ReportService
from ..services.dia_descanso_service import DiaDescansoService
import datetime

user_service = UserService()
report_service = ReportService()
dia_descanso_service = DiaDescansoService()

# --- DECORADOR DE ADMINISTRADOR ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Debes iniciar sesión para acceder.', 'warning')
            return redirect(url_for('auth.login'))
        user = user_service.get_user_by_id(session['user_id'])
        if not user or user.rol != 'admin':
            flash('No tienes permiso para acceder a esta página.', 'error')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# --- RUTAS DE ADMINISTRADOR ---
@admin_bp.route('/')
@admin_bp.route('/dashboard')
@admin_required
def admin_dashboard():
    summary_data = report_service.get_admin_dashboard_summary()
    users = user_service.get_all_users() # To pass to the template if needed for user list
    return render_template('admin/dashboard.html', users=users, summary_data=summary_data)

@admin_bp.route('/users')
@admin_required
def admin_users():
    users = user_service.get_all_users()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/user/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def admin_user_detail(user_id):
    user = user_service.get_user_by_id(user_id)
    if not user:
        flash('Usuario no encontrado.', 'error')
        return redirect(url_for('admin.admin_users'))

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'update_profile':
            profile_data = request.form.to_dict()
            updated_user = user_service.update_user_profile(user_id, profile_data)
            if updated_user:
                flash('Perfil actualizado con éxito.', 'success')
            else:
                flash('Error al actualizar el perfil.', 'error')

        elif action == 'update_password':
            new_password = request.form.get('new_password')
            if user_service.update_user_password(user_id, new_password):
                flash('Contraseña actualizada con éxito.', 'success')
            else:
                flash('La contraseña no puede estar vacía o hubo un error.', 'error')

        elif action == 'update_schedule':
            schedule_data = request.form.to_dict()
            if user_service.update_user_schedule(user_id, schedule_data):
                flash('Horario actualizado con éxito.', 'success')
            else:
                flash('Error al actualizar el horario. Verifique el formato de las horas.', 'error')

        return redirect(url_for('admin.admin_user_detail', user_id=user.id))
    
    return render_template('admin/user_detail.html', user=user)

@admin_bp.route('/user/<int:user_id>/set_rest_days', methods=['POST'])
@admin_required
def set_rest_days(user_id):
    user = user_service.get_user_by_id(user_id)
    if not user:
        return jsonify({'status': 'error', 'message': 'Usuario no encontrado.'}), 404

    data = request.get_json()
    fechas = data.get('fechas', [])

    if dia_descanso_service.set_rest_days(user_id, fechas):
        return jsonify({'status': 'success', 'message': 'Días de descanso actualizados.'})
    else:
        return jsonify({'status': 'error', 'message': 'Error al actualizar días de descanso.'}), 500


@admin_bp.route('/report')
@admin_required
def admin_report():
    user_id = request.args.get('user_id', type=int)
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    start_date = None
    end_date = None
    error_message = None

    try:
        if start_date_str:
            start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
        if end_date_str:
            end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        error_message = 'Formato de fecha inválido. Use YYYY-MM-DD.'

    if not start_date or not end_date:
        today = datetime.date.today()
        start_date = today.replace(day=1)
        end_date = (start_date + datetime.timedelta(days=31)).replace(day=1) - datetime.timedelta(days=1)

    if error_message:
        flash(error_message, 'error')

    report_data = report_service.generate_report(user_id, start_date, end_date)

    return render_template('admin/report.html', report_data=report_data, start_date=start_date, end_date=end_date, all_users=user_service.get_all_users())

