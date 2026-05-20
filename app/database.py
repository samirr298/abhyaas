import pymysql
import config

class Database:
    def __init__(self):
        """Open a database connection when object is created."""
        try:
            self.__connection = pymysql.connect(
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