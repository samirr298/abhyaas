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
                    INSERT INTO notifications (user_id, task_id, title, subject)
                    VALUES (%s, %s, %s, %s)
                """
                for student in students:
                    cursor.execute(insert_sql, [student['id'], task_id, task_title, subject or 'General'])
            connection.commit()
            return True
        finally:
            if connection is not None:
                connection.close()

    @classmethod
    def get_for_user(cls, user_id):
        sql = "SELECT * FROM notifications WHERE user_id = %s ORDER BY created_at DESC"
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
