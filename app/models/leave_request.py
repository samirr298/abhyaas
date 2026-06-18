from app.models.base_model import BaseModel


class LeaveRequest(BaseModel):
    @staticmethod
    def create(user_id, leave_date, end_date, leave_type, reason):
        sql = """
            INSERT INTO leave_requests (user_id, leave_date, end_date, leave_type, reason, status, is_read)
            VALUES (%s, %s, %s, %s, %s, 'Pending', FALSE)
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
            sql += " AND LOWER(status) = LOWER(%s)"
            params.append(status_filter)

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
            sql += " AND LOWER(l.status) = LOWER(%s)"
            params.append(status_filter)

        sql += " ORDER BY FIELD(l.status, 'Pending', 'Approved', 'Rejected'), l.leave_date DESC"
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
        return LeaveRequest.execute_write(sql, [status.capitalize(), request_id])

    @staticmethod
    def delete_pending(user_id, request_id):
        sql = "DELETE FROM leave_requests WHERE id = %s AND user_id = %s AND LOWER(status) = 'pending'"
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
              AND LOWER(status) != 'pending'
            ORDER BY updated_at DESC
        """
        return LeaveRequest.fetch_all(sql, [user_id]) or []

    @staticmethod
    def mark_notifications_read(user_id):
        sql = "UPDATE leave_requests SET is_read = TRUE WHERE user_id = %s AND is_read = FALSE AND LOWER(status) != 'pending'"
        return LeaveRequest.execute_write(sql, [user_id])
