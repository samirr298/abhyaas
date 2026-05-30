from app.models.base_model import BaseModel


class Task(BaseModel):
    @classmethod
    def create_task(cls, teacher_id, title, description, subject, deadline):
        connection = None
        try:
            connection = cls.get_connection()
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO tasks (teacher_id, title, description, subject, deadline, created_at, is_active)
                    VALUES (%s, %s, %s, %s, %s, NOW(), 1)
                    """,
                    [teacher_id, title, description, subject, deadline],
                )
                task_id = cursor.lastrowid
            connection.commit()
            return task_id
        finally:
            if connection is not None:
                connection.close()

    @classmethod
    def get_teacher_tasks(cls, teacher_id):
        sql = """
            SELECT t.*, 
                   COUNT(ts.id) AS total_submissions,
                   SUM(CASE WHEN ts.status = 'submitted' THEN 1 ELSE 0 END) AS submitted_count,
                   (COUNT(ts.id) - SUM(CASE WHEN ts.status = 'submitted' THEN 1 ELSE 0 END)) AS pending_count
            FROM tasks t
            LEFT JOIN task_submissions ts ON ts.task_id = t.id
            WHERE t.teacher_id = %s
            GROUP BY t.id
            ORDER BY t.created_at DESC
        """
        return cls.fetch_all(sql, [teacher_id])

    @classmethod
    def get_today_tasks(cls, student_id):
        sql = """
            SELECT t.*, 
                   ts.id AS submission_id,
                   ts.status AS submission_status,
                   ts.submitted_at,
                   ts.submission_text,
                   ts.teacher_feedback,
                   ts.submission_file_path
            FROM tasks t
            LEFT JOIN task_submissions ts
                ON ts.task_id = t.id AND ts.student_id = %s
            WHERE t.is_active = 1
            ORDER BY t.deadline ASC, t.created_at ASC
        """
        return cls.fetch_all(sql, [student_id])

    @classmethod
    def get_task(cls, task_id):
        sql = "SELECT * FROM tasks WHERE id = %s"
        return cls.fetch_one(sql, [task_id])


class TaskSubmission(BaseModel):
    @classmethod
    def create_submission(cls, task_id, student_id, submission_text, submission_file_path=None):
        connection = None
        try:
            connection = cls.get_connection()
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO task_submissions (task_id, student_id, submission_text, submission_file_path, status, submitted_at)
                    VALUES (%s, %s, %s, %s, 'submitted', NOW())
                    """,
                    [task_id, student_id, submission_text, submission_file_path],
                )
                submission_id = cursor.lastrowid
            connection.commit()
            return submission_id
        finally:
            if connection is not None:
                connection.close()

    @classmethod
    def get_submission_for_task(cls, task_id, student_id):
        sql = "SELECT * FROM task_submissions WHERE task_id = %s AND student_id = %s"
        return cls.fetch_one(sql, [task_id, student_id])

    @classmethod
    def update_submission(cls, submission_id, submission_text, submission_file_path=None):
        sql = """
            UPDATE task_submissions
            SET submission_text = %s,
                submission_file_path = %s,
                status = 'submitted',
                submitted_at = NOW()
            WHERE id = %s
        """
        return cls.execute_write(sql, [submission_text, submission_file_path, submission_id])

    @classmethod
    def get_submissions_for_task(cls, task_id):
        sql = """
            SELECT ts.*, u.name AS student_name, u.email
            FROM task_submissions ts
            JOIN users u ON u.id = ts.student_id
            WHERE ts.task_id = %s
            ORDER BY ts.submitted_at DESC, ts.id DESC
        """
        return cls.fetch_all(sql, [task_id])

    @classmethod
    def save_feedback(cls, submission_id, teacher_feedback):
        sql = "UPDATE task_submissions SET teacher_feedback = %s WHERE id = %s"
        return cls.execute_write(sql, [teacher_feedback, submission_id])
