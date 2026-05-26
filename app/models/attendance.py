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
    def get_status_count(cls, user_id, status):
        """Counts total days for a specific status ('present' or 'absent')."""
        sql = "SELECT COUNT(*) AS count FROM attendance WHERE user_id = %s AND status = %s"
        result = cls.fetch_one(sql, [user_id, status])
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
    def get_paginated_history(cls, user_id, limit, offset):
        """Fetches a sliced page of attendance records for the history table."""
        sql = """
            SELECT * 
            FROM attendance 
            WHERE user_id = %s 
            ORDER BY attendance_date DESC 
            LIMIT %s OFFSET %s
        """
        return cls.fetch_all(sql, [user_id, limit, offset])

    @classmethod
    def get_total_history_count(cls, user_id):
        """Gets the total number of records to calculate total pages for layout pagination."""
        sql = "SELECT COUNT(*) as count FROM attendance WHERE user_id = %s"
        result = cls.fetch_one(sql, [user_id])
        return result['count'] if result else 0