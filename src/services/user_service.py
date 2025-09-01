
from ..models import User, Horario
from ..repositories.user_repository import UserRepository
from ..repositories.horario_repository import HorarioRepository
import datetime

class UserService:
    def __init__(self):
        self.user_repo = UserRepository()
        self.horario_repo = HorarioRepository()

    def get_all_users(self) -> list[User]:
        return self.user_repo.get_all()

    def get_user_by_id(self, user_id: int) -> User | None:
        return self.user_repo.get_by_id(user_id)

    def update_user_profile(self, user_id: int, profile_data: dict) -> User | None:
        user = self.user_repo.get_by_id(user_id)
        if user:
            user.nombres = profile_data.get('nombres')
            user.apellidos = profile_data.get('apellidos')
            user.correo = profile_data.get('correo')
            user.username = profile_data.get('username')
            user.area = profile_data.get('area')
            user.departamento = profile_data.get('departamento')
            user.cargo = profile_data.get('cargo')
            user.rol = profile_data.get('rol')
            self.user_repo.update(user)
            self.user_repo.commit()
        return user

    def update_user_password(self, user_id: int, new_password: str) -> bool:
        user = self.user_repo.get_by_id(user_id)
        if user and new_password:
            user.set_password(new_password)
            self.user_repo.update(user)
            self.user_repo.commit()
            return True
        return False

    def update_user_schedule(self, user_id: int, schedule_data: dict) -> bool:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return False

        horario = self.horario_repo.get_by_user_id(user_id)
        if not horario:
            horario = Horario(user_id=user_id)
            self.horario_repo.add(horario)

        try:
            horario.hora_entrada = datetime.datetime.strptime(schedule_data.get('hora_entrada'), '%H:%M').time()
            horario.hora_salida = datetime.datetime.strptime(schedule_data.get('hora_salida'), '%H:%M').time()
            horario.hora_inicio_almuerzo = datetime.datetime.strptime(schedule_data.get('hora_inicio_almuerzo'), '%H:%M').time()
            horario.hora_fin_almuerzo = datetime.datetime.strptime(schedule_data.get('hora_fin_almuerzo'), '%H:%M').time()
            self.horario_repo.update(horario)
            self.horario_repo.commit()
            return True
        except (ValueError, TypeError):
            return False
