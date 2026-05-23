from app.database import db


class BaseModel:
	@staticmethod
	def get_connection():
		return db()
