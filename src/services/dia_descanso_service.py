
import datetime
from ..repositories.dia_descanso_repository import DiaDescansoRepository
from ..models import DiaDescanso

class DiaDescansoService:
    def __init__(self):
        self.dia_descanso_repo = DiaDescansoRepository()

    def set_rest_days(self, user_id: int, dates: list[str]) -> bool:
        try:
            self.dia_descanso_repo.delete_by_user_id(user_id)
            for fecha_str in dates:
                fecha = datetime.datetime.strptime(fecha_str, '%Y-%m-%d').date()
                descanso = DiaDescanso(user_id=user_id, fecha=fecha)
                self.dia_descanso_repo.add(descanso)
            self.dia_descanso_repo.commit()
            return True
        except (ValueError, TypeError):
            return False
