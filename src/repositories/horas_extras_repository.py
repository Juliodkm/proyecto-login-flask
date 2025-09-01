
from ..models import db, HorasExtras
from ..interfaces.horas_extras_repository_interface import IHorasExtrasRepository
import datetime

class HorasExtrasRepository(IHorasExtrasRepository):
    def get_by_user_id_and_date(self, user_id: int, date: datetime.date) -> HorasExtras | None:
        return HorasExtras.query.filter_by(user_id=user_id, fecha=date).first()

    def get_total_for_month(self, user_id: int, year_month: str) -> float:
        return db.session.query(db.func.sum(HorasExtras.horas)).filter(
            HorasExtras.user_id == user_id,
            db.func.strftime('%Y-%m', HorasExtras.fecha) == year_month
        ).scalar() or 0.0

    def add(self, horas_extras: HorasExtras):
        db.session.add(horas_extras)

    def commit(self):
        db.session.commit()

    def update(self, horas_extras: HorasExtras):
        db.session.merge(horas_extras)
