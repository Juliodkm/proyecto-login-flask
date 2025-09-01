
from ..models import db, Checkin
from ..interfaces.checkin_repository_interface import ICheckinRepository
import datetime

class CheckinRepository(ICheckinRepository):
    def get_by_user_id_and_date(self, user_id: int, date: datetime.date) -> list[Checkin]:
        return Checkin.query.filter(
            Checkin.user_id == user_id,
            db.func.date(Checkin.timestamp_utc) == date
        ).order_by(Checkin.timestamp_utc).all()

    def get_by_user_id_and_type_and_date(self, user_id: int, tipo: str, date: datetime.date) -> Checkin | None:
        return Checkin.query.filter_by(user_id=user_id, tipo=tipo).filter(db.func.date(Checkin.timestamp_utc) == date).first()

    def get_checkins_for_month(self, user_id: int, start_of_month: datetime.date) -> list[Checkin]:
        return Checkin.query.filter(
            Checkin.user_id == user_id,
            Checkin.timestamp_utc >= start_of_month,
            Checkin.tipo == 'Ingreso'
        ).all()

    def add(self, checkin: Checkin):
        db.session.add(checkin)

    def commit(self):
        db.session.commit()

    def count_lateness_for_month(self, user_id: int, start_of_month: datetime.date) -> int:
        return Checkin.query.filter(
            Checkin.user_id == user_id,
            Checkin.status == 'Tardanza',
            db.func.date(Checkin.timestamp_utc) >= start_of_month
        ).count()

    def count_worked_days_for_month(self, user_id: int, start_of_month: datetime.date) -> int:
                return db.session.query(db.func.count(db.func.distinct(db.func.date(Checkin.timestamp_utc)))).filter(
            Checkin.user_id == user_id,
            db.func.date(Checkin.timestamp_utc) >= start_of_month
        ).scalar()
