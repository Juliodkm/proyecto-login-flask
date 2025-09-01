
from abc import ABC, abstractmethod
from ..models import Checkin
import datetime

class ICheckinRepository(ABC):
    @abstractmethod
    def get_by_user_id_and_date(self, user_id: int, date: datetime.date) -> list[Checkin]:
        pass

    @abstractmethod
    def get_by_user_id_and_type_and_date(self, user_id: int, tipo: str, date: datetime.date) -> Checkin | None:
        pass

    @abstractmethod
    def get_checkins_for_month(self, user_id: int, start_of_month: datetime.date) -> list[Checkin]:
        pass

    @abstractmethod
    def add(self, checkin: Checkin):
        pass

    @abstractmethod
    def commit(self):
        pass

    @abstractmethod
    def count_lateness_for_month(self, user_id: int, start_of_month: datetime.date) -> int:
        pass

    @abstractmethod
    def count_worked_days_for_month(self, user_id: int, start_of_month: datetime.date) -> int:
        pass
