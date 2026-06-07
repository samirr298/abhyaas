from app.models.base_model import BaseModel

class Attendance(BaseModel):
    
    @classmethod
    def get_today_record(cls, user_id, today_date):
        """Checks if an attendance record exists for a specific user today."""
        sql = "SELECT * FROM attendance WHERE user_id = %s AND attendance_date = %s"
        return cls.fetch_one(sql, [user_id, today_date])

    @classmethod
    def mark_present(cls, user_id, today_date):
        """Inserts a physical 'present' row for the user."""
        sql = "INSERT INTO attendance (user_id, attendance_date, status) VALUES (%s, %s, 'present')"
        return cls.execute_write(sql, [user_id, today_date])
    @classmethod
    def mark_absent(cls, user_id, today_date):
        """Inserts a physical 'present' row for the user."""
        sql = "INSERT INTO attendance (user_id, attendance_date, status) VALUES (%s, %s, 'absent')"
        return cls.execute_write(sql, [user_id, today_date])

    @classmethod
    def get_status_count(cls, user_id, status, start_date=None, end_date=None):
        """Counts total days for a specific status ('present' or 'absent') within an optional date range."""
        sql = "SELECT COUNT(*) AS count FROM attendance WHERE user_id = %s AND status = %s"
        params = [user_id, status]

        if start_date:
            sql += " AND attendance_date >= %s"
            params.append(start_date)

        if end_date:
            sql += " AND attendance_date < %s"
            params.append(end_date)

        result = cls.fetch_one(sql, params)
        return result['count'] if result else 0

    @classmethod
    def get_latest_date(cls,user_id):
        sql = "select max(attendance_date) as latest_record from attendance where user_id = %s"
        result = cls.fetch_one(sql,[user_id])
        return result['latest_record'] if result and result['latest_record'] else 0  
    @classmethod
    def insert_automatic_absents(cls, today_date):
       
        sql = """
            INSERT INTO attendance (user_id, attendance_date, status)
            SELECT id, %s, 'absent'
            FROM users 
            WHERE id NOT IN (
                SELECT user_id FROM attendance WHERE attendance_date = %s
            )
        """
        return cls.execute_write(sql, [today_date, today_date])
    
    @classmethod
    def get_paginated_history(cls, user_id, page, per_page, start_date=None, end_date=None):
        """Fetches a paginated, month-filtered attendance history using SQL pagination."""
        offset = (page - 1) * per_page
        sql = """
            SELECT *
            FROM attendance
            WHERE user_id = %s
        """
        params = [user_id]

        if start_date:
            sql += " AND attendance_date >= %s"
            params.append(start_date)

        if end_date:
            sql += " AND attendance_date < %s"
            params.append(end_date)

        sql += " ORDER BY attendance_date DESC LIMIT %s OFFSET %s"
        params.extend([per_page, offset])
        return cls.fetch_all(sql, params)

    @classmethod
    def get_total_history_count(cls, user_id, start_date=None, end_date=None):
        """Counts the total number of records in the selected history window."""
        sql = "SELECT COUNT(*) as count FROM attendance WHERE user_id = %s"
        params = [user_id]

        if start_date:
            sql += " AND attendance_date >= %s"
            params.append(start_date)

        if end_date:
            sql += " AND attendance_date < %s"
            params.append(end_date)

        result = cls.fetch_one(sql, params)
        return result['count'] if result else 0

    @classmethod
    def get_students_attendance_for_date(cls, attendance_date):
        sql = """
            SELECT u.id AS student_id, u.name, u.username, u.email,
                   COALESCE(a.status, 'not_marked') AS status,
                   a.id AS attendance_id,
                   a.marked_at
            FROM users u
            LEFT JOIN attendance a
              ON a.user_id = u.id AND a.attendance_date = %s
            WHERE u.role = 'student'
            ORDER BY u.name ASC
        """
        return cls.fetch_all(sql, [attendance_date]) or []

    @classmethod
    def set_attendance_status(cls, user_id, attendance_date, status):
        existing = cls.get_today_record(user_id, attendance_date)
        if existing:
            sql = "UPDATE attendance SET status = %s WHERE user_id = %s AND attendance_date = %s"
            return cls.execute_write(sql, [status, user_id, attendance_date])

        sql = "INSERT INTO attendance (user_id, attendance_date, status) VALUES (%s, %s, %s)"
        return cls.execute_write(sql, [user_id, attendance_date, status])

        if start_date:
            sql += " AND attendance_date >= %s"
            params.append(start_date)

        if end_date:
            sql += " AND attendance_date < %s"
            params.append(end_date)

        result = cls.fetch_one(sql, params)
        return result['count'] if result else 0