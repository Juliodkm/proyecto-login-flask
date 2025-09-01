
import os
from src import create_app

# Obtener la configuración del entorno o usar la de desarrollo por defecto
env = os.getenv('FLASK_ENV', 'development')
app = create_app(env)

if __name__ == '__main__':
    app.run()
