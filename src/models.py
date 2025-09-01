
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
import pytz

db = SQLAlchemy()

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
    tipo = db.Column(db.String(50), nullable=False, default='Ingreso') # Ingreso, Inicio Almuerzo, Fin Almuerzo, Salida

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
    hora_inicio_almuerzo = db.Column(db.Time, nullable=False, default=datetime.time(13, 0))
    hora_fin_almuerzo = db.Column(db.Time, nullable=False, default=datetime.time(15, 0))

class DiaDescanso(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
