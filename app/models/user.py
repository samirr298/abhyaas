from werkzeug.security import generate_password_hash, check_password_hash
from app.models.base_model import BaseModel


class User(BaseModel):
    def __init__(self, name=None, email=None, password=None, role=None, user_id=None):
        super().__init__(name=name, email=email, password=password, role=role, user_id=user_id)
        self.name = name
        self.email = email
        self.password = password
        self.role = role
        self.user_id = user_id

    def hash_password(self):
        if self.password:
            self.password = generate_password_hash(self.password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    @classmethod
    def from_db_row(cls, row):
        return cls(
            user_id=row.get('id'),
            name=row.get('name'),
            email=row.get('email'),
            password=row.get('password'),
            role=row.get('role'),
        )
