
import os
from flask import Flask
from config import config
from .models import db
from .commands import register_commands # Import the new function

def create_app(config_name='default'):
    app = Flask(__name__,
                template_folder='templates',
                static_folder='static')

    # Cargar configuración
    app.config.from_object(config[config_name])

    # Inicializar extensiones
    db.init_app(app)

    # Crear carpeta de uploads si no existe
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Registrar Blueprints
    from .auth.routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from .main.routes import main_bp
    app.register_blueprint(main_bp, url_prefix='/')

    from .admin.routes import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # Register CLI commands
    register_commands(app)

    return app
