from datetime import timedelta
import pymysql

from app.models.base_model import BaseModel


class LeaveRequest(BaseModel):
    @staticmethod
    def create(user_id, leave_date, end_date, leave_type, reason):
        sql = """
            INSERT INTO leave_requests (user_id, leave_date, end_date, leave_type, reason, status, is_read)
            VALUES (%s, %s, %s, %s, %s, 'pending', FALSE)
        """
        return LeaveRequest.execute_write(sql, [user_id, leave_date, end_date, leave_type, reason])

    @staticmethod
    def get_by_user(user_id, status_filter=None):
        sql = """
            SELECT
                id,
                leave_date,
                end_date,
                leave_type,
                reason,
                status,
                DATE_FORMAT(submitted_at, '%%Y-%%m-%%d %%H:%%i') AS submitted_on,
                DATE_FORMAT(updated_at, '%%Y-%%m-%%d %%H:%%i') AS updated_on
            FROM leave_requests
            WHERE user_id = %s
        """
        params = [user_id]

        if status_filter:
            sql += " AND status = %s"
            params.append(status_filter.lower())

        sql += " ORDER BY submitted_at DESC"
        return LeaveRequest.fetch_all(sql, params) or []

    @staticmethod
    def get_all_requests(status_filter=None):
        sql = """
            SELECT
                l.id,
                l.user_id,
                u.name AS student_name,
                u.username,
                l.leave_date,
                l.end_date,
                l.leave_type,
                l.reason,
                l.status,
                DATE_FORMAT(l.submitted_at, '%%Y-%%m-%%d %%H:%%i') AS submitted_on,
                DATE_FORMAT(l.updated_at, '%%Y-%%m-%%d %%H:%%i') AS updated_on
            FROM leave_requests l
            JOIN users u ON u.id = l.user_id
            WHERE 1 = 1
        """
        params = []

        if status_filter:
            sql += " AND l.status = %s"
            params.append(status_filter.lower())

        sql += " ORDER BY FIELD(l.status, 'pending', 'approved', 'rejected'), l.leave_date DESC"
        return LeaveRequest.fetch_all(sql, params) or []

    @staticmethod
    def get_by_id(request_id):
        sql = "SELECT * FROM leave_requests WHERE id = %s LIMIT 1"
        return LeaveRequest.fetch_one(sql, [request_id])

    @staticmethod
    def update_status(request_id, status):
        sql = """
            UPDATE leave_requests
            SET status = %s,
                is_read = FALSE,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        return LeaveRequest.execute_write(sql, [status.lower(), request_id])

    @staticmethod
    def get_pending_requests():
        sql = """
            SELECT
                l.id,
                l.user_id,
                u.name AS student_name,
                u.username,
                l.leave_date,
                l.end_date,
                l.leave_type,
                l.reason,
                l.status,
                DATE_FORMAT(l.submitted_at, '%%Y-%%m-%%d %%H:%%i') AS submitted_on,
                DATE_FORMAT(l.updated_at, '%%Y-%%m-%%d %%H:%%i') AS updated_on
            FROM leave_requests l
            JOIN users u ON u.id = l.user_id
            WHERE l.status = 'pending'
            ORDER BY l.leave_date ASC, l.submitted_at ASC
        """
        return LeaveRequest.fetch_all(sql) or []

    @staticmethod
    def apply_leave_to_attendance(user_id, start_date, end_date):
        connection = LeaveRequest.get_connection()
        try:
            with connection.cursor() as cursor:
                current_date = start_date
                while current_date <= end_date:
                    cursor.execute(
                        "SELECT id FROM attendance WHERE user_id = %s AND attendance_date = %s LIMIT 1",
                        [user_id, current_date]
                    )
                    existing = cursor.fetchone()
                    if existing:
                        try:
                            cursor.execute(
                                "UPDATE attendance SET status = 'leave' WHERE id = %s",
                                [existing['id']]
                            )
                        except pymysql.err.DataError:
                            # Fallback if DB enum doesn't include 'leave'
                            cursor.execute(
                                "UPDATE attendance SET status = 'absent' WHERE id = %s",
                                [existing['id']]
                            )
                    else:
                        try:
                            cursor.execute(
                                "INSERT INTO attendance (user_id, attendance_date, status) VALUES (%s, %s, 'leave')",
                                [user_id, current_date]
                            )
                        except pymysql.err.DataError:
                            # Fallback if DB enum doesn't include 'leave'
                            cursor.execute(
                                "INSERT INTO attendance (user_id, attendance_date, status) VALUES (%s, %s, 'absent')",
                                [user_id, current_date]
                            )
                    current_date += timedelta(days=1)

            connection.commit()
            return True
        finally:
            if connection is not None:
                connection.close()

    @staticmethod
    def delete_pending(user_id, request_id):
        sql = "DELETE FROM leave_requests WHERE id = %s AND user_id = %s AND status = 'pending'"
        return LeaveRequest.execute_write(sql, [request_id, user_id])

    @staticmethod
    def get_unread_notifications_by_user(user_id):
        sql = """
            SELECT
                id,
                leave_date,
                status,
                DATE_FORMAT(updated_at, '%%Y-%%m-%%d %%H:%%i') AS updated_on
            FROM leave_requests
            WHERE user_id = %s
              AND is_read = FALSE
              AND status != 'pending'
            ORDER BY updated_at DESC
        """
        return LeaveRequest.fetch_all(sql, [user_id]) or []

    @staticmethod
    def mark_notifications_read(user_id):
        sql = "UPDATE leave_requests SET is_read = TRUE WHERE user_id = %s AND is_read = FALSE AND status != 'pending'"
        return LeaveRequest.execute_write(sql, [user_id])
