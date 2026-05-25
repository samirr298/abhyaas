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
    def get_status_count(cls, user_id, status):
        """Counts total days for a specific status ('present' or 'absent')."""
        sql = "SELECT COUNT(*) AS count FROM attendance WHERE user_id = %s AND status = %s"
        result = cls.fetch_one(sql, [user_id, status])
        return result['count'] if result else 0