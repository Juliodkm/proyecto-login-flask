# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
import datetime
import pytz
import base64
from functools import wraps

# --- CONFIGURACIÓN ---
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(app.instance_path, 'uploads')
db = SQLAlchemy(app)

# Crear carpeta de uploads si no existe
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# --- DECORADORES ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if user.rol != 'admin':
            flash('No tienes permiso para acceder a esta página.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# --- MODELOS DE BASE DE DATOS ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombres = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    fecha_nacimiento = db.Column(db.String(20), nullable=False)
    area = db.Column(db.String(100), nullable=False)
    departamento = db.Column(db.String(100), nullable=False)
    cargo = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    rol = db.Column(db.String(20), nullable=False, default='user') # user o admin
    checkins = db.relationship('Checkin', backref='user', lazy=True)
    horario = db.relationship('Horario', backref='user', uselist=False)
    dias_descanso = db.relationship('DiaDescanso', backref='user', lazy='dynamic')


    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Checkin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp_utc = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    photo_filename = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    tipo = db.Column(db.String(50), nullable=False, default='Ingreso') # Ingreso, Almuerzo, Salida

    @property
    def timestamp_peru(self):
        peru_tz = pytz.timezone('America/Lima')
        return self.timestamp_utc.replace(tzinfo=pytz.utc).astimezone(peru_tz)

class HorasExtras(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    horas = db.Column(db.Float, nullable=False)
    user = db.relationship('User', backref=db.backref('horas_extras', lazy=True))

class Horario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    hora_entrada = db.Column(db.Time, nullable=False, default=datetime.time(8, 0))
    hora_salida = db.Column(db.Time, nullable=False, default=datetime.time(18, 0))

class DiaDescanso(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    fecha = db.Column(db.Date, nullable=False)


# --- RUTAS DE LA APLICACIÓN ---
@app.route('/')
def home():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user.rol == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('dashboard'))
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # ... (código de registro sin cambios)
        nombres = request.form['nombres']
        apellidos = request.form['apellidos']
        fecha_nacimiento = request.form['fecha_nacimiento']
        area = request.form['area']
        departamento = request.form['departamento']
        cargo = request.form['cargo']
        correo = request.form['correo']
        username = request.form['username']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash('El nombre de usuario ya existe.', 'error')
            return redirect(url_for('register'))
        if User.query.filter_by(correo=correo).first():
            flash('La dirección de correo electrónico ya está en uso.', 'error')
            return redirect(url_for('register'))

        new_user = User(
            nombres=nombres,
            apellidos=apellidos,
            fecha_nacimiento=fecha_nacimiento,
            area=area,
            departamento=departamento,
            cargo=cargo,
            correo=correo,
            username=username
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('¡Registro exitoso! Por favor, inicia sesión.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            if user.rol == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('dashboard'))
        else:
            flash('Usuario o contraseña incorrectos.', 'error')
            
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    
    # Obtener la fecha actual en la zona horaria de Perú
    peru_tz = pytz.timezone('America/Lima')
    now_peru = datetime.datetime.now(peru_tz)
    today_peru = now_peru.date()
    
    # --- CÁLCULO DE ESTADÍSTICAS ---
    
    # 1. Días puntuales y tardanzas del mes actual
    primer_dia_mes = today_peru.replace(day=1)
    checkins_mes = Checkin.query.filter(
        Checkin.user_id == user.id,
        Checkin.timestamp_utc >= primer_dia_mes,
        Checkin.tipo == 'Ingreso'
    ).all()
    
    dias_puntuales = 0
    dias_tarde = 0
    for checkin in checkins_mes:
        if checkin.status == 'A Tiempo':
            dias_puntuales += 1
        elif checkin.status == 'Tardanza':
            dias_tarde += 1

    # 2. Días con almuerzo extendido
    dias_almuerzo_extendido = 0
    # (Lógica a implementar: requiere registrar inicio y fin de almuerzo)

    # 3. Días no marcados
    # (Lógica a implementar: requiere comparar con días laborables esperados)

    # 4. Horas extras del mes
    horas_extras_mes = db.session.query(db.func.sum(HorasExtras.horas)).filter(
        HorasExtras.user_id == user.id,
        db.func.strftime('%Y-%m', HorasExtras.fecha) == today_peru.strftime('%Y-%m')
    ).scalar() or 0

    # --- ESTADO ACTUAL DE MARCACIÓN ---
    checkin_ingreso_hoy = Checkin.query.filter_by(user_id=user.id, tipo='Ingreso').filter(db.func.date(Checkin.timestamp_utc) == today_peru).first()
    checkin_almuerzo_hoy = Checkin.query.filter_by(user_id=user.id, tipo='Almuerzo').filter(db.func.date(Checkin.timestamp_utc) == today_peru).order_by(Checkin.timestamp_utc.desc()).first()
    checkin_salida_hoy = Checkin.query.filter_by(user_id=user.id, tipo='Salida').filter(db.func.date(Checkin.timestamp_utc) == today_peru).first()

    proximo_tipo_marcacion = 'Ingreso'
    if checkin_ingreso_hoy:
        proximo_tipo_marcacion = 'Almuerzo'
    if checkin_almuerzo_hoy:
        # Si la última marcación de almuerzo fue hace más de 1h, el próximo es Salida
        if (now_peru - checkin_almuerzo_hoy.timestamp_peru).total_seconds() > 3600:
             proximo_tipo_marcacion = 'Salida'
        else:
             proximo_tipo_marcacion = 'Almuerzo' # Para marcar el fin
    if checkin_salida_hoy:
        proximo_tipo_marcacion = 'Finalizado'


    checkins_today = Checkin.query.filter(Checkin.user_id == user.id, db.func.date(Checkin.timestamp_utc) == today_peru).all()


    return render_template(
        'dashboard.html', 
        user=user, 
        checkins=checkins_today,
        dias_puntuales=dias_puntuales,
        dias_tarde=dias_tarde,
        dias_almuerzo_extendido=dias_almuerzo_extendido,
        horas_extras_mes=round(horas_extras_mes, 2),
        proximo_tipo_marcacion=proximo_tipo_marcacion
    )


@app.route('/checkin', methods=['POST'])
def checkin():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'No autorizado'}), 401

    data = request.get_json()
    lat = data.get('lat')
    lon = data.get('lon')
    img_data_url = data.get('img')
    tipo_marcacion = data.get('tipo') # 'Ingreso', 'Almuerzo', 'Salida'

    if not all([lat, lon, img_data_url, tipo_marcacion]):
        return jsonify({'status': 'error', 'message': 'Faltan datos'}), 400

    # --- LÓGICA DE MARCACIÓN ---
    peru_tz = pytz.timezone('America/Lima')
    timestamp_utc = datetime.datetime.utcnow()
    now_peru = timestamp_utc.replace(tzinfo=pytz.utc).astimezone(peru_tz)
    
    status = ''
    
    if tipo_marcacion == 'Ingreso':
        hora_limite_puntual = now_peru.replace(hour=8, minute=5, second=0, microsecond=0)
        if now_peru <= hora_limite_puntual:
            status = 'A Tiempo'
        else:
            status = 'Tardanza'
    
    elif tipo_marcacion == 'Almuerzo':
        # Se podría añadir lógica para controlar la duración del almuerzo
        status = 'Almuerzo'

    elif tipo_marcacion == 'Salida':
        hora_minima_salida = now_peru.replace(hour=18, minute=0, second=0, microsecond=0)
        if now_peru >= hora_minima_salida:
            status = 'Salida'
        else:
            status = 'Salida (Antes de hora)'

    # --- GUARDAR FOTO ---
    try:
        img_str = img_data_url.split(',')[1]
        img_bytes = base64.b64decode(img_str)
        filename = f"{session['user_id']}_{timestamp_utc.strftime('%Y%m%d%H%M%S')}.jpg"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        with open(filepath, 'wb') as f:
            f.write(img_bytes)
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error al guardar la imagen: {e}'}), 500

    # --- GUARDAR EN BD ---
    new_checkin = Checkin(
        user_id=session['user_id'],
        timestamp_utc=timestamp_utc,
        latitude=lat,
        longitude=lon,
        photo_filename=filename,
        status=status,
        tipo=tipo_marcacion
    )
    db.session.add(new_checkin)
    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': f'Marcación de {tipo_marcacion} registrada con éxito.',
        'checkin': {
            'time': new_checkin.timestamp_peru.strftime('%H:%M:%S'),
            'status': new_checkin.status,
            'tipo': new_checkin.tipo,
            'photo_url': url_for('uploaded_file', filename=new_checkin.photo_filename)
        }
    })

@app.route('/marcar_horas_extras', methods=['POST'])
def marcar_horas_extras():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'No autorizado'}), 401

    data = request.get_json()
    horas = data.get('horas')

    if not horas:
        return jsonify({'status': 'error', 'message': 'Faltan datos'}), 400

    try:
        horas = float(horas)
        if horas <= 0:
            raise ValueError("Las horas deben ser un número positivo")
    except ValueError as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

    peru_tz = pytz.timezone('America/Lima')
    today_peru = datetime.datetime.now(peru_tz).date()

    # Opcional: Validar que no se registren horas extras en el mismo día dos veces
    existing_record = HorasExtras.query.filter_by(user_id=session['user_id'], fecha=today_peru).first()
    if existing_record:
        existing_record.horas += horas
    else:
        new_extra_hours = HorasExtras(
            user_id=session['user_id'],
            fecha=today_peru,
            horas=horas
        )
        db.session.add(new_extra_hours)
    
    db.session.commit()

    return jsonify({'status': 'success', 'message': f'Se han añadido {horas} horas extras.'})

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

# --- RUTAS DE ADMINISTRADOR ---
@app.route('/admin')
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    users = User.query.all()
    return render_template('admin/dashboard.html', users=users)

@app.route('/admin/users')
@admin_required
def admin_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/user/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def admin_user_detail(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        # Actualizar horario
        hora_entrada = request.form.get('hora_entrada')
        hora_salida = request.form.get('hora_salida')
        if hora_entrada and hora_salida:
            if not user.horario:
                user.horario = Horario()
            user.horario.hora_entrada = datetime.datetime.strptime(hora_entrada, '%H:%M').time()
            user.horario.hora_salida = datetime.datetime.strptime(hora_salida, '%H:%M').time()
            db.session.commit()
            flash('Horario actualizado con éxito.', 'success')

        return redirect(url_for('admin_user_detail', user_id=user.id))
    
    return render_template('admin/user_detail.html', user=user)

@app.route('/admin/user/<int:user_id>/set_rest_days', methods=['POST'])
@admin_required
def set_rest_days(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    fechas = data.get('fechas', [])

    # Eliminar días de descanso anteriores para este mes y usuario
    # (Se podría mejorar para solo añadir/quitar los cambiados)
    user.dias_descanso.delete()

    for fecha_str in fechas:
        fecha = datetime.datetime.strptime(fecha_str, '%Y-%m-%d').date()
        descanso = DiaDescanso(user_id=user.id, fecha=fecha)
        db.session.add(descanso)
    
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Días de descanso actualizados.'})


# --- INICIAR LA APP Y CREAR LA BD ---
def setup_database(app):
    with app.app_context():
        db.create_all()
        
        # Comprobar si el usuario admin ya existe
        if User.query.filter_by(username='admin').first() is None:
            # Crear usuario admin
            admin_user = User(
                nombres='Admin', 
                apellidos='User', 
                fecha_nacimiento='2000-01-01',
                area='Sistemas',
                departamento='IT',
                cargo='Administrador', 
                correo='admin@example.com',
                username='admin',
                rol='admin'
            )
            admin_user.set_password('admin')
            db.session.add(admin_user)

        # Comprobar si hay más de 1 usuario (el admin) para no volver a poblar
        if User.query.count() <= 1:
            # Crear 5 usuarios de ejemplo
            users_data = [
                { 'nombres': 'Carlos', 'apellidos': 'Gomez', 'area': 'Ventas', 'departamento': 'Retail', 'cargo': 'Vendedor' },
                { 'nombres': 'Lucia', 'apellidos': 'Fernandez', 'area': 'Marketing', 'departamento': 'Digital', 'cargo': 'Community Manager' },
                { 'nombres': 'Javier', 'apellidos': 'Rodriguez', 'area': 'Logística', 'departamento': 'Almacén', 'cargo': 'Operario' },
                { 'nombres': 'Maria', 'apellidos': 'Lopez', 'area': 'Contabilidad', 'departamento': 'Finanzas', 'cargo': 'Asistente Contable' },
                { 'nombres': 'Pedro', 'apellidos': 'Martinez', 'area': 'Recursos Humanos', 'departamento': 'Gestión Humana', 'cargo': 'Reclutador' },
            ]

            for data in users_data:
                username = f'{data["nombres"].lower()}{data["apellidos"].lower().replace(" ", "")}'
                email = f'{username}@example.com'
                
                # Asegurarse de que el username y correo no existan
                if User.query.filter_by(username=username).first() or User.query.filter_by(correo=email).first():
                    continue

                new_user = User(
                    nombres=data['nombres'],
                    apellidos=data['apellidos'],
                    fecha_nacimiento='1995-05-10',
                    area=data['area'],
                    departamento=data['departamento'],
                    cargo=data['cargo'],
                    correo=email,
                    username=username
                )
                new_user.set_password('password123')
                db.session.add(new_user)

        db.session.commit()

        # Asignar horarios por defecto a usuarios que no lo tengan
        for user in User.query.filter(User.horario == None).all():
            default_schedule = Horario(user_id=user.id)
            db.session.add(default_schedule)
        db.session.commit()

if __name__ == '__main__':
    setup_database(app)
    app.run(debug=True)
