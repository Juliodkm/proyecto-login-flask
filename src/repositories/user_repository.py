
from ..models import db, User
from ..interfaces.user_repository_interface import IUserRepository

class UserRepository(IUserRepository):
    def get_all(self) -> list[User]:
        return User.query.all()

    def get_by_id(self, user_id: int) -> User | None:
        return User.query.get(user_id)

    def get_by_username(self, username: str) -> User | None:
        return User.query.filter_by(username=username).first()

    def get_by_email(self, email: str) -> User | None:
        return User.query.filter_by(correo=email).first()

    def add(self, user: User):
        db.session.add(user)

    def commit(self):
        db.session.commit()

    def update(self, user: User):
        db.session.merge(user)

    def delete(self, user: User):
        db.session.delete(user)
