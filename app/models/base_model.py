from abc import ABC,abstractmethod

from app.database import Database


class BaseModel(ABC):
 
	@staticmethod
    
	def get_connection():
		return Database.db()

	@classmethod
	def fetch_one(cls, sql, params=None):
		connection = None
		try:
			connection = cls.get_connection()
			if connection is None:
				return None

			with connection.cursor() as cursor:
				cursor.execute(sql, params or [])
				return cursor.fetchone()
		finally:
			if connection is not None:
				connection.close()
	@classmethod
	def fetch_all(cls, sql, params=None):
		connection = None
		try:
			connection = cls.get_connection()
			if connection is None:
				return None

			with connection.cursor() as cursor:
				cursor.execute(sql, params or [])
				return cursor.fetchall()
		finally:
			if connection is not None:
				connection.close()
	@classmethod
	def execute_write(cls, sql, params=None):
		connection = None
		try:
			connection = cls.get_connection()
			if connection is None:
				return False

			with connection.cursor() as cursor:
				cursor.execute(sql, params or [])

			connection.commit()
			return True
		finally:
			if connection is not None:
				connection.close()
