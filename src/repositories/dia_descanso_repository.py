
from ..models import db, DiaDescanso
from ..interfaces.dia_descanso_repository_interface import IDiaDescansoRepository
import datetime

class DiaDescansoRepository(IDiaDescansoRepository):
    def get_by_user_id_and_date(self, user_id: int, date: datetime.date) -> DiaDescanso | None:
        return DiaDescanso.query.filter_by(user_id=user_id, fecha=date).first()

    def delete_by_user_id(self, user_id: int):
        DiaDescanso.query.filter_by(user_id=user_id).delete()

    def add(self, dia_descanso: DiaDescanso):
        db.session.add(dia_descanso)

    def commit(self):
        db.session.commit()
