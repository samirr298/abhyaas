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
def create_tables():
        connection = pymysql.connect(
        host=config.MYSQL_HOST,
        user=config.MYSQL_USER,
        password=config.MYSQL_PASSWORD,
        database=config.MYSQL_DATABASE,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor)

        try:
            with connection.cursor() as cursor:
            # Create Users Table
             cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    email VARCHAR(50) NOT NULL UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    role VARCHAR(20) NOT NULL DEFAULT 'student',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    name varchar(30) not null
                    )
                """)
            connection.commit()
            print("🎉 Tables initialized successfully!")
        finally:
            connection.close()