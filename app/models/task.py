from app.models.base_model import BaseModel


class Task(BaseModel):
    @classmethod
    def create_task(cls, title, description, created_by, due_date, attached_filename, subject):
        sql = """
            INSERT INTO tasks (title, description, created_by, due_date, completed_by_students, attached_filename, subject)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        connection = cls.get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql, [title, description, created_by, due_date, '', attached_filename, subject])
                task_id = cursor.lastrowid
            connection.commit()
            return task_id
        finally:
            if connection is not None:
                connection.close()

    @classmethod
    def get_teacher_tasks(cls, teacher_id):
        sql = "SELECT * FROM tasks WHERE created_by = %s ORDER BY created_at DESC"
        return cls.fetch_all(sql, [teacher_id]) or []

    @classmethod
    def get_today_tasks(cls, student_id):
        sql = """
            SELECT t.*, 
                   s.id AS submission_id,
                   s.status AS submission_status,
                   s.submitted_at,
                   s.submitted_filename
            FROM tasks t
            LEFT JOIN submissions s
                ON s.task_id = t.id AND s.student_id = %s
            WHERE (
                    DATE(t.due_date) = CURDATE()
                    OR s.status IS NULL
                    OR s.status != 'Reviewed'
                  )
            ORDER BY t.due_date ASC, t.created_at ASC
        """
        return cls.fetch_all(sql, [student_id]) or []

    @classmethod
    def get_task(cls, task_id):
        sql = "SELECT * FROM tasks WHERE id = %s LIMIT 1"
        return cls.fetch_one(sql, [task_id])


class TaskBookmark(BaseModel):
    @staticmethod
    def get_bookmarked_task_ids(user_id):
        sql = "SELECT task_id FROM task_bookmarks WHERE user_id = %s"
        rows = TaskBookmark.fetch_all(sql, [user_id]) or []
        return {int(row['task_id']) for row in rows if row.get('task_id') is not None}

    @staticmethod
    def is_bookmarked(user_id, task_id):
        sql = "SELECT id FROM task_bookmarks WHERE user_id = %s AND task_id = %s LIMIT 1"
        return TaskBookmark.fetch_one(sql, [user_id, task_id]) is not None

    @staticmethod
    def toggle(user_id, task_id):
        if TaskBookmark.is_bookmarked(user_id, task_id):
            sql = "DELETE FROM task_bookmarks WHERE user_id = %s AND task_id = %s"
            TaskBookmark.execute_write(sql, [user_id, task_id])
            return False

        sql = "INSERT INTO task_bookmarks (user_id, task_id) VALUES (%s, %s)"
        TaskBookmark.execute_write(sql, [user_id, task_id])
        return True

    @staticmethod
    def get_bookmarks_for_user(user_id):
        sql = """
            SELECT
                t.*,
                b.created_at AS bookmarked_at,
                s.id AS submission_id,
                s.status AS submission_status,
                s.submitted_at,
                s.submitted_filename
            FROM task_bookmarks b
            JOIN tasks t ON t.id = b.task_id
            LEFT JOIN submissions s
                ON s.task_id = t.id AND s.student_id = b.user_id
            WHERE b.user_id = %s
            ORDER BY b.created_at DESC
        """
        return TaskBookmark.fetch_all(sql, [user_id]) or []


class TaskSubmission(BaseModel):
    @classmethod
    def get_submission_for_task(cls, task_id, student_id):
        sql = "SELECT * FROM submissions WHERE task_id = %s AND student_id = %s LIMIT 1"
        return cls.fetch_one(sql, [task_id, student_id])

    @classmethod
    def save_submission(cls, task_id, student_id, submitted_filename, status='Pending'):
        sql = """
            INSERT INTO submissions (task_id, student_id, submitted_filename, status)
            VALUES (%s, %s, %s, %s)
        """
        return cls.execute_write(sql, [task_id, student_id, submitted_filename, status])

    @classmethod
    def update_submission(cls, submission_id, submitted_filename, status='Pending'):
        sql = """
            UPDATE submissions
            SET submitted_filename = %s, status = %s
            WHERE id = %s
        """
        return cls.execute_write(sql, [submitted_filename, status, submission_id])
