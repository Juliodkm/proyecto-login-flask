
import click
from flask.cli import with_appcontext
from .models import db, User, Horario
import datetime

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Crea las tablas de la base de datos y datos iniciales."""
    db.create_all()
    click.echo("Base de datos inicializada.")

    if User.query.filter_by(username='admin').first() is None:
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
        click.echo("Usuario administrador creado.")

    if User.query.count() <= 1:
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
        click.echo(f"{len(users_data)} usuarios de ejemplo creados.")

    db.session.commit()

    # Asignar o actualizar horarios para TODOS los usuarios
    for user in User.query.all():
        if not user.horario:
            default_schedule = Horario(
                user_id=user.id,
                hora_entrada=datetime.time(8, 0),
                hora_salida=datetime.time(18, 0),
                hora_inicio_almuerzo=datetime.time(13, 0),
                hora_fin_almuerzo=datetime.time(15, 0)
            )
            db.session.add(default_schedule)
    db.session.commit()
    click.echo("Horarios por defecto asignados a todos los usuarios.")

def register_commands(app):
    app.cli.add_command(init_db_command)
