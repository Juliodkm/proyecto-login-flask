
from ..models import User
from ..repositories.user_repository import UserRepository

class AuthService:
    def __init__(self):
        self.user_repo = UserRepository()

    def register_user(self, user_data: dict) -> tuple[User | None, str]:
        username = user_data.get('username')
        email = user_data.get('correo')

        if self.user_repo.get_by_username(username):
            return None, 'El nombre de usuario ya existe.'
        if self.user_repo.get_by_email(email):
            return None, 'La dirección de correo electrónico ya está en uso.'

        new_user = User(
            nombres=user_data.get('nombres'),
            apellidos=user_data.get('apellidos'),
            fecha_nacimiento=user_data.get('fecha_nacimiento'),
            area=user_data.get('area'),
            departamento=user_data.get('departamento'),
            cargo=user_data.get('cargo'),
            correo=email,
            username=username
        )
        new_user.set_password(user_data.get('password'))
        
        self.user_repo.add(new_user)
        self.user_repo.commit()
        
        return new_user, '¡Registro exitoso! Por favor, inicia sesión.'

    def login_user(self, username: str, password: str) -> User | None:
        user = self.user_repo.get_by_username(username)
        if user and user.check_password(password):
            return user
        return None
