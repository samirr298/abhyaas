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
                                    username VARCHAR(50) UNIQUE,
                                    email VARCHAR(255) NOT NULL UNIQUE,
                                    password_hash VARCHAR(255) NOT NULL,
                                    role VARCHAR(50) NOT NULL,
                                    profile_pic VARCHAR(255),
                                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                    fee_status ENUM('paid', 'unpaid') DEFAULT 'unpaid',
                                    fee_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                                )
                                """
                        )
                        connection.commit()
                finally:
                        pass
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
                        pass
                        connection.close()
        def create_announcement_table():
                connection =  Database.db()
                try:
                        with connection.cursor() as cursor:
                                cursor.execute(
                               ''' CREATE TABLE if not exists announcements (
                                        id INT AUTO_INCREMENT PRIMARY KEY,
                                        title VARCHAR(255) NOT NULL,
                                         summary VARCHAR(255) NOT NULL, -- [NEW] Holds the short one-line description Teaser
                                        category VARCHAR(50) NOT NULL,  -- Holds 'Academic', 'Events', 'Exams'
                                        author_id INT NOT NULL,         -- Links back to the user who wrote it
                                         body TEXT NOT NULL,             -- Holds the full message content
                                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                                        FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE CASCADE
                                         );''')
                                connection.commit()
                finally:
                        pass
                        connection.close()
                 # tasks and task_submissions are deleted by project cleanup.
        def create_task_tables():
                connection =  Database.db()
                try:
                        with connection.cursor() as cursor:
                                cursor.execute(
                               ''' CREATE TABLE if not exists tasks (
                                                id INT AUTO_INCREMENT PRIMARY KEY,
                                                title VARCHAR(255) NOT NULL,
                                                description TEXT NULL,
                                                created_by INT NOT NULL,  -- Teacher's user ID
                                                due_date DATETIME NULL,
                                                attached_filename varchar(255) null,
                                                completed_by_students TEXT NULL,
                                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                                subject varchar(255),
                                                CONSTRAINT fk_task_teacher FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE
                                                );''')
                                connection.commit()
                finally:
                        pass
                        connection.close()
        def create_submission_table():
                connection =  Database.db()
                try:
                        with connection.cursor() as cursor:
                                cursor.execute(
                               '''CREATE TABLE IF NOT EXISTS submissions
                                (
                                id INT AUTO_INCREMENT PRIMARY KEY,
                                task_id INT NOT NULL,
                                student_id INT NOT NULL,
                                submitted_filename VARCHAR(255) NOT NULL,
                                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                status VARCHAR(50) DEFAULT 'Not Reviewed',
                                CONSTRAINT fk_sub_task FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
                                CONSTRAINT fk_sub_student FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
                                );''')
                                connection.commit()
                finally:
                        pass
                        connection.close() 
        def create_feedback_table():
                connection =  Database.db()
                try:
                        with connection.cursor() as cursor:
                                cursor.execute(
                               '''CREATE TABLE if not exists feedback (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    teacher_id INT NOT NULL,
        task_id INT NOT NULL,  -- key column for task id
    feedback_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_feedback_student FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_feedback_teacher FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_feedback_task FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);;''')
                                connection.commit()
                finally:
                        pass
                        connection.close()
        def create_notification_table():
                connection =  Database.db()
                try:
                        with connection.cursor() as cursor:
                                cursor.execute(
                               '''CREATE TABLE IF NOT EXISTS notifications (
                                    id INT AUTO_INCREMENT PRIMARY KEY,
                                    user_id INT NOT NULL,
                                    task_id INT NOT NULL,
                                    title VARCHAR(255) NOT NULL,
                                    subject VARCHAR(255) NOT NULL,
                                    is_read TINYINT(1) NOT NULL DEFAULT 0,
                                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                    CONSTRAINT fk_notification_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                                    CONSTRAINT fk_notification_task FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
                                );''')
                                connection.commit()
                finally:
                        pass
                        connection.close()
        def create_leave_request_table():
                connection = Database.db()
                try:
                        with connection.cursor() as cursor:
                                # Check if table exists
                                cursor.execute("SHOW TABLES LIKE 'leave_requests'")
                                if not cursor.fetchone():
                                        cursor.execute('''
                                            CREATE TABLE leave_requests (
                                                id INT AUTO_INCREMENT PRIMARY KEY,
                                                user_id INT NOT NULL,
                                                leave_date DATE NOT NULL,
                                                end_date DATE NOT NULL,
                                                leave_type VARCHAR(50) NOT NULL DEFAULT 'General',
                                                reason TEXT NOT NULL,
                                                status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
                                                is_read TINYINT(1) DEFAULT 0,
                                                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                                                CONSTRAINT fk_leave_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                                            )
                                        ''')
                                        connection.commit()
                                else:
                                        # Table exists, check for missing columns
                                        cursor.execute("SHOW COLUMNS FROM leave_requests")
                                        columns = {row['Field'] for row in cursor.fetchall()}
                                        
                                        # Add missing columns if needed
                                        if 'end_date' not in columns:
                                                cursor.execute("ALTER TABLE leave_requests ADD COLUMN end_date DATE NULL")
                                                cursor.execute("UPDATE leave_requests SET end_date = leave_date WHERE end_date IS NULL")
                                                cursor.execute("ALTER TABLE leave_requests MODIFY COLUMN end_date DATE NOT NULL")
                                                connection.commit()
                                        
                                        if 'leave_type' not in columns:
                                                cursor.execute("ALTER TABLE leave_requests ADD COLUMN leave_type VARCHAR(50) DEFAULT 'General'")
                                                connection.commit()
                finally:
                        connection.close()
# Connection debug message removed during cleanup
