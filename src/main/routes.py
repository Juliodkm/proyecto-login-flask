
from flask import (render_template, redirect, url_for, session, jsonify, 
                   request, send_from_directory, current_app, flash)
from . import main_bp
from ..services.checkin_service import CheckinService
from ..services.horas_extras_service import HorasExtrasService
from ..services.user_service import UserService # For admin check in home route
import datetime
import pytz
import base64
import os

checkin_service = CheckinService()
horas_extras_service = HorasExtrasService()
user_service = UserService()

@main_bp.route('/')
def home():
    if 'user_id' in session:
        user = user_service.get_user_by_id(session['user_id'])
        if user and user.rol == 'admin':
            return redirect(url_for('admin.admin_dashboard'))
        return redirect(url_for('main.dashboard'))
    return render_template('home.html')

@main_bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Debes iniciar sesión para ver esta página.', 'warning')
        return redirect(url_for('auth.login'))
    
    dashboard_data = checkin_service.get_dashboard_data(session['user_id'])
    
    # Get extra hours for the current month
    peru_tz = pytz.timezone('America/Lima')
    today_peru = datetime.datetime.now(peru_tz).date()
    year_month = today_peru.strftime('%Y-%m')
    dashboard_data['horas_extras_mes'] = horas_extras_service.get_total_for_month(session['user_id'], year_month)

    return render_template(
        'dashboard.html', 
        user=dashboard_data['user'], 
        checkins=dashboard_data['checkins'],
        dias_puntuales=dashboard_data['dias_puntuales'],
        dias_tarde=dashboard_data['dias_tarde'],
        dias_almuerzo_extendido=dashboard_data['dias_almuerzo_extendido'],
        horas_extras_mes=round(dashboard_data['horas_extras_mes'], 2),
        proximo_tipo_marcacion=dashboard_data['proximo_tipo_marcacion']
    )

@main_bp.route('/checkin', methods=['POST'])
def checkin():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'No autorizado'}), 401

    data = request.get_json()
    response_data, message, status_code = checkin_service.perform_checkin(session['user_id'], data)
    
    if status_code == 200:
        return jsonify(response_data), status_code
    else:
        return jsonify({'status': 'error', 'message': message}), status_code

@main_bp.route('/marcar_horas_extras', methods=['POST'])
def marcar_horas_extras():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'No autorizado'}), 401

    data = request.get_json()
    horas = data.get('horas')

    try:
        horas = float(horas)
    except (ValueError, TypeError):
        return jsonify({'status': 'error', 'message': 'Horas inválidas.'}), 400

    if horas_extras_service.add_extra_hours(session['user_id'], horas):
        return jsonify({'status': 'success', 'message': f'Se han añadido {horas} horas extras.'})
    else:
        return jsonify({'status': 'error', 'message': 'Error al añadir horas extras o valor inválido.'}), 400

@main_bp.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
