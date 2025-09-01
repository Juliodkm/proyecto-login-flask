
import datetime
import pytz
from ..repositories.horas_extras_repository import HorasExtrasRepository
from ..models import HorasExtras

class HorasExtrasService:
    def __init__(self):
        self.horas_extras_repo = HorasExtrasRepository()

    def add_extra_hours(self, user_id: int, hours: float) -> bool:
        if hours <= 0:
            return False

        peru_tz = pytz.timezone('America/Lima')
        today_peru = datetime.datetime.now(peru_tz).date()

        existing_record = self.horas_extras_repo.get_by_user_id_and_date(user_id, today_peru)
        if existing_record:
            existing_record.horas += hours
            self.horas_extras_repo.update(existing_record)
        else:
            new_extra_hours = HorasExtras(
                user_id=user_id,
                fecha=today_peru,
                horas=hours
            )
            self.horas_extras_repo.add(new_extra_hours)
        
        self.horas_extras_repo.commit()
        return True
    
    def get_total_for_month(self, user_id: int, year_month: str) -> float:
        return self.horas_extras_repo.get_total_for_month(user_id, year_month)
