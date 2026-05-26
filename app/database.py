import config
import pymysql
class Database:
        def db():
                connection = pymysql.connect(
                host=config.MYSQL_HOST,
                user=config.MYSQL_USER,
                password=config.MYSQL_PASSWORD,
                database=config.MYSQL_DATABASE,
                charset ='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
                )
                
                return connection

      


        def create_users_table():
                connection =   Database.db()
                try:
                        with connection.cursor() as cursor:
                                cursor.execute(
                                """
                                CREATE TABLE IF NOT EXISTS users (
                                    id INT AUTO_INCREMENT PRIMARY KEY,
                                    name VARCHAR(255) NOT NULL,
                                    email VARCHAR(255) NOT NULL UNIQUE,
                                    password_hash VARCHAR(255) NOT NULL,
                                    role VARCHAR(50) NOT NULL,
                                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                )
                                """
                        )
                        connection.commit()
                finally:
                        print('table created')
                        connection.close()

        def create_attendance_table():
                connection =  Database.db()
                try:
                        with connection.cursor() as cursor:
                                cursor.execute(
                                """
                                CREATE TABLE IF NOT EXISTS attendance (
                                        id INT AUTO_INCREMENT PRIMARY KEY,
                                        user_id INT NOT NULL,
                                        attendance_date DATE NOT NULL,          
                                        marked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                        status ENUM('present', 'absent', 'not_marked') NOT NULL DEFAULT 'not_marked',
                                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                                        );
                                """
                        )
                        
                        connection.commit()
                finally:
                        print('table created')
                        connection.close()


print("🚀 Connection successful!")
