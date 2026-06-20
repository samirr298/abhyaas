from app.models.base_model import BaseModel

class Notification(BaseModel):
    @classmethod
    def create_task_notifications(cls, task_id, task_title, subject):
        sql_user_ids = "SELECT id FROM users WHERE role = 'student'"
        students = cls.fetch_all(sql_user_ids) or []
        if not students:
            return False

        connection = cls.get_connection()
        try:
            with connection.cursor() as cursor:
                insert_sql = """
                    INSERT INTO notifications (user_id, task_id, title, subject, notification_type)
                    VALUES (%s, %s, %s, %s, %s)
                """
                for student in students:
                    cursor.execute(insert_sql, [student['id'], task_id, task_title, subject or 'General', 'task_created'])
            connection.commit()
            return True
        finally:
            if connection is not None:
                connection.close()

    @classmethod
    def sync_deadline_reminders(cls, user_id):
        role_row = cls.fetch_one("SELECT role FROM users WHERE id = %s LIMIT 1", [user_id])
        if not role_row or role_row.get('role') != 'student':
            return False

        sql = """
            SELECT
                t.id,
                t.title,
                t.due_date
            FROM tasks t
            LEFT JOIN submissions s
                ON s.task_id = t.id AND s.student_id = %s
            WHERE t.due_date IS NOT NULL
              AND DATE(t.due_date) = DATE_ADD(CURDATE(), INTERVAL 1 DAY)
              AND s.id IS NULL
        """
        due_tasks = cls.fetch_all(sql, [user_id]) or []
        if not due_tasks:
            return False

        connection = cls.get_connection()
        try:
            with connection.cursor() as cursor:
                check_sql = """
                    SELECT id
                    FROM notifications
                    WHERE user_id = %s
                      AND task_id = %s
                      AND notification_type = 'deadline_reminder'
                    LIMIT 1
                """
                insert_sql = """
                    INSERT INTO notifications (user_id, task_id, title, subject, notification_type)
                    VALUES (%s, %s, %s, %s, %s)
                """

                for task in due_tasks:
                    cursor.execute(check_sql, [user_id, task['id']])
                    existing = cursor.fetchone()
                    if existing:
                        continue

                    due_date = task.get('due_date')
                    due_date_text = due_date.strftime('%d %b %Y') if due_date else 'soon'
                    cursor.execute(
                        insert_sql,
                        [user_id, task['id'], task['title'], f"Due on {due_date_text}", 'deadline_reminder']
                    )

            connection.commit()
            return True
        finally:
            if connection is not None:
                connection.close()

    @classmethod
    def get_for_user(cls, user_id):
        sql = """
            SELECT n.*, t.due_date
            FROM notifications n
            LEFT JOIN tasks t ON t.id = n.task_id
            WHERE n.user_id = %s
            ORDER BY n.created_at DESC
        """
        return cls.fetch_all(sql, [user_id]) or []

    @classmethod
    def get_unread_count(cls, user_id):
        sql = "SELECT COUNT(*) AS unread_count FROM notifications WHERE user_id = %s AND is_read = 0"
        row = cls.fetch_one(sql, [user_id]) or {'unread_count': 0}
        return row.get('unread_count', 0)

    @classmethod
    def mark_as_read(cls, notification_id, user_id):
        sql = "UPDATE notifications SET is_read = 1 WHERE id = %s AND user_id = %s"
        return cls.execute_write(sql, [notification_id, user_id])

    @classmethod
    def mark_all_read(cls, user_id):
        sql = "UPDATE notifications SET is_read = 1 WHERE user_id = %s"
        return cls.execute_write(sql, [user_id])
