
from abc import ABC, abstractmethod
from ..models import Horario

class IHorarioRepository(ABC):
    @abstractmethod
    def get_by_user_id(self, user_id: int) -> Horario | None:
        pass

    @abstractmethod
    def add(self, horario: Horario):
        pass

    @abstractmethod
    def commit(self):
        pass

    @abstractmethod
    def update(self, horario: Horario):
        pass
