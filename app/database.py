import config
import pymysql

def db():
        connection = pymysql.connect(
         host=config.MYSQL_HOST,
         user=config.MYSQL_USER,
        password=config.MYSQL_PASSWORD,
        database=config.MYSQL_DATABASE,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
        )
        return connection
print("🚀 Connection successful!")