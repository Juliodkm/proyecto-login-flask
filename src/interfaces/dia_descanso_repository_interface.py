
from abc import ABC, abstractmethod
from ..models import DiaDescanso
import datetime

class IDiaDescansoRepository(ABC):
    @abstractmethod
    def get_by_user_id_and_date(self, user_id: int, date: datetime.date) -> DiaDescanso | None:
        pass

    @abstractmethod
    def delete_by_user_id(self, user_id: int):
        pass

    @abstractmethod
    def add(self, dia_descanso: DiaDescanso):
        pass

    @abstractmethod
    def commit(self):
        pass
