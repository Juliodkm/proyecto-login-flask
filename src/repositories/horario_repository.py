
from ..models import db, Horario
from ..interfaces.horario_repository_interface import IHorarioRepository

class HorarioRepository(IHorarioRepository):
    def get_by_user_id(self, user_id: int) -> Horario | None:
        return Horario.query.filter_by(user_id=user_id).first()

    def add(self, horario: Horario):
        db.session.add(horario)

    def commit(self):
        db.session.commit()

    def update(self, horario: Horario):
        db.session.merge(horario)
