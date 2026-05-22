import pymysql
import config
from app.models.user import User


class BaseDatabase:
    def __init__(self):
        self._connection = None
        try:
            self._connection = pymysql.connect(
                host=config.MYSQL_HOST,
                user=config.MYSQL_USER,
                password=config.MYSQL_PASSWORD,
                database=config.MYSQL_DATABASE,
                cursorclass=pymysql.cursors.DictCursor,
            )
            print("✅ Database connected successfully!")
        except pymysql.MySQLError as e:
            print("❌ Database connection failed!")
            print("Error:", e)

    def get_connection(self):
        return self._connection

    def execute(self, query, params=None, commit=False):
        if not self._connection:
            return None

        try:
            cursor = self._connection.cursor()
            cursor.execute(query, params or ())
            if commit:
                self._connection.commit()
            if query.strip().upper().startswith("SELECT"):
                result = cursor.fetchall()
            else:
                result = cursor.lastrowid
            cursor.close()
            return result
        except pymysql.MySQLError as e:
            print("❌ Database query failed:", e)
            if self._connection and commit:
                self._connection.rollback()
            return None


class Database(BaseDatabase):
    pass


class UserRepository(Database):
    def user_exists(self, email):
        result = self.execute(
            "SELECT id FROM users WHERE email = %s",
            (email,),
        )
        return bool(result)

    def create_user(self, user):
        query = (
            "INSERT INTO users (name, email, password, role, created_at) "
            "VALUES (%s, %s, %s, %s, NOW())"
        )
        return self.execute(query, (user.name, user.email, user.password, user.role), commit=True)

    def get_user_by_email(self, email):
        rows = self.execute(
            "SELECT * FROM users WHERE email = %s",
            (email,),
        )
        if rows:
            return User.from_db_row(rows[0])
        return None