# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os # Necesario para la llave secreta

# --- CONFIGURACIÓN ---
app = Flask(__name__)
# Genera una llave secreta segura. En un entorno real, esto debería ser más complejo y estar fuera del código.
app.config['SECRET_KEY'] = os.urandom(24) 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db' # Define la ubicación de la BD
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Desactiva notificaciones innecesarias
db = SQLAlchemy(app)

# --- MODELO DE BASE DE DATOS ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    # Función para establecer la contraseña, aplicando un hash de seguridad
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # Función para verificar la contraseña
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# --- RUTAS DE LA APLICACIÓN ---
@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash('El nombre de usuario ya existe.', 'error')
            return redirect(url_for('register'))

        new_user = User(username=username)
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
            return redirect(url_for('dashboard'))
        else:
            flash('Usuario o contraseña incorrectos.', 'error')
            
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

# --- INICIAR LA APP Y CREAR LA BD ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all() # Crea las tablas de la base de datos si no existen
    app.run(debug=True)