
from abc import ABC, abstractmethod
from ..models import HorasExtras
import datetime

class IHorasExtrasRepository(ABC):
    @abstractmethod
    def get_by_user_id_and_date(self, user_id: int, date: datetime.date) -> HorasExtras | None:
        pass

    @abstractmethod
    def get_total_for_month(self, user_id: int, year_month: str) -> float:
        pass

    @abstractmethod
    def add(self, horas_extras: HorasExtras):
        pass

    @abstractmethod
    def commit(self):
        pass

    @abstractmethod
    def update(self, horas_extras: HorasExtras):
        pass
