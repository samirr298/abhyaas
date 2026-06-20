from app.models.base_model import BaseModel

class Users(BaseModel):
    
    @staticmethod
    def get_my_email(email):
        sql = "SELECT id, name, username, profile_pic, email, password_hash, role, is_banned FROM users WHERE email = %s"
        return Users.fetch_one(sql, [email])

    @staticmethod
    def reset_password(email, password_hash):
        sql = "UPDATE users SET password_hash = %s WHERE email = %s"
        return Users.execute_write(sql, [password_hash, email])
    @staticmethod
    def change_my_password(email):
        sql = "SELECT password_hash, id FROM users WHERE email = %s"
        return Users.fetch_one(sql, [email])
    @staticmethod
    def finally_change_my_password(hashedpassword,email):
        sql = "update users set password_hash = %s WHERE email = %s"
        if Users.execute_write(sql, (hashedpassword, email)):
            return "Successfully Changed the password ! "
        return None

    @classmethod
    def update_profile_details(cls, user_id, name, email):
        sql = """
        UPDATE users
        SET name = %s, email = %s
        WHERE id = %s
        """
        return Users.execute_write(sql, [name, email, user_id])

    @classmethod
    def update_profile_pic(cls, user_id, filename):
        sql = """
        UPDATE users 
        SET profile_pic = %s 
        WHERE id = %s
        """
        return Users.execute_write(sql, [filename, user_id])

    # --- Username related helpers ---
    @staticmethod
    def is_username_taken(username):
        sql = "SELECT id FROM users WHERE username = %s"
        return Users.fetch_one(sql, [username]) is not None

    @staticmethod
    def create_user(name, username, email, password_hash, role):
        sql = "INSERT INTO users (name, username, email, password_hash, role) VALUES (%s, %s, %s, %s, %s)"
        try:
            return Users.execute_write(sql, [name, username, email, password_hash, role])
        except Exception:
            # If insert fails (e.g., uniqueness violation), return False
            return False

    @staticmethod
    def get_by_username(username):
        sql = "SELECT id, name, username, email, role FROM users WHERE username = %s"
        return Users.fetch_one(sql, [username])

    @staticmethod
    def get_all_students():
        sql = "SELECT id FROM users WHERE role = 'student'"
        return Users.fetch_all(sql) or []

    @staticmethod
    def get_all_users():
        sql = "SELECT id, name, username, email, role, is_banned, created_at FROM users ORDER BY created_at DESC"
        return Users.fetch_all(sql) or []

    @staticmethod
    def get_user_by_id(user_id):
        sql = "SELECT id, name, username, email, role, is_banned, created_at FROM users WHERE id = %s"
        return Users.fetch_one(sql, [user_id])

    @staticmethod
    def ban_user(user_id):
        sql = "UPDATE users SET is_banned = 1 WHERE id = %s"
        return Users.execute_write(sql, [user_id])

    @staticmethod
    def unban_user(user_id):
        sql = "UPDATE users SET is_banned = 0 WHERE id = %s"
        return Users.execute_write(sql, [user_id])

    @staticmethod
    def delete_user(user_id):
        """Permanently delete a user from the system."""
        sql = "DELETE FROM users WHERE id = %s"
        return Users.execute_write(sql, [user_id])

    @staticmethod
    def get_stats():
        """Get aggregate user stats for admin dashboard."""
        sql_total = "SELECT COUNT(*) as total FROM users"
        sql_students = "SELECT COUNT(*) as total FROM users WHERE role = 'student'"
        sql_teachers = "SELECT COUNT(*) as total FROM users WHERE role = 'teacher'"
        sql_admins = "SELECT COUNT(*) as total FROM users WHERE role = 'admin'"
        sql_banned = "SELECT COUNT(*) as total FROM users WHERE is_banned = 1"
        sql_new_today = "SELECT COUNT(*) as total FROM users WHERE DATE(created_at) = CURDATE()"
        
        return {
            'total': Users.fetch_one(sql_total)['total'],
            'students': Users.fetch_one(sql_students)['total'],
            'teachers': Users.fetch_one(sql_teachers)['total'],
            'admins': Users.fetch_one(sql_admins)['total'],
            'banned': Users.fetch_one(sql_banned)['total'],
            'new_today': Users.fetch_one(sql_new_today)['total'],
        }

    @staticmethod
    def is_user_banned(user_id):
        sql = "SELECT is_banned FROM users WHERE id = %s"
        result = Users.fetch_one(sql, [user_id])
        return result and result['is_banned'] == 1

    @staticmethod
    def is_email_banned(email):
        sql = "SELECT is_banned FROM users WHERE email = %s"
        result = Users.fetch_one(sql, [email])
        return result and result['is_banned'] == 1

    @staticmethod
    def update_role(user_id, role):
        sql = "UPDATE users SET role = %s WHERE id = %s"
        return Users.execute_write(sql, [role, user_id])

    @staticmethod
    def set_username(user_id, username):
        sql = "UPDATE users SET username = %s WHERE id = %s"
        try:
            return Users.execute_write(sql, [username, user_id])
        except Exception:
            # Likely a UNIQUE constraint violation — caller will handle False
            return False

    @staticmethod
    def get_all_students(fee_filter=None):
        """
        Fetch all students with their fee details.
        fee_filter: None (all), 'paid', or 'unpaid'
        """
        sql = """
            SELECT 
                id, name, username, email,
                fee_status, fee_updated_at,
                fee_amount, fee_due_date, fee_paid_amount, fee_last_payment_at
            FROM users
            WHERE role = 'student'
        """
        params = []

        if fee_filter == 'unpaid':
            sql += " AND fee_status = 'unpaid'"
        elif fee_filter == 'paid':
            sql += " AND fee_status = 'paid'"

        sql += " ORDER BY name ASC"
        return Users.fetch_all(sql, params) or []


    @staticmethod
    def get_student_by_id(student_id):
        """Fetch a specific student by ID."""
        sql = """
            SELECT 
                id, name, username, email,
                fee_status, fee_updated_at,
                fee_amount, fee_due_date, fee_paid_amount, fee_last_payment_at
            FROM users
            WHERE id = %s AND role = 'student'
        """
        return Users.fetch_one(sql, [student_id])


    @staticmethod
    def update_fee_status(student_id, fee_status):
        """Update fee status and timestamp for a student."""
        sql = "UPDATE users SET fee_status = %s, fee_updated_at = CURRENT_TIMESTAMP WHERE id = %s AND role = 'student'"
        return Users.execute_write(sql, [fee_status, student_id])

    @staticmethod
    def record_fee_payment(student_id, paid_amount, payment_at=None):
        """Record a payment for the student and update fee status/timestamps."""
        # payment_at is optional; if not provided we use CURRENT_TIMESTAMP.
        if payment_at is None:
            sql = """
                UPDATE users
                SET 
                    fee_paid_amount = %s,
                    fee_last_payment_at = CURRENT_TIMESTAMP,
                    fee_status = CASE 
                        WHEN fee_amount IS NULL OR fee_amount = 0 THEN 'paid'
                        WHEN %s >= fee_amount THEN 'paid'
                        ELSE 'unpaid'
                    END,
                    fee_updated_at = CURRENT_TIMESTAMP
                WHERE id = %s AND role = 'student'
            """
            return Users.execute_write(sql, [paid_amount, paid_amount, student_id])

        sql = """
            UPDATE users
            SET 
                fee_paid_amount = %s,
                fee_last_payment_at = %s,
                fee_status = CASE 
                    WHEN fee_amount IS NULL OR fee_amount = 0 THEN 'paid'
                    WHEN %s >= fee_amount THEN 'paid'
                    ELSE 'unpaid'
                END,
                fee_updated_at = CURRENT_TIMESTAMP
            WHERE id = %s AND role = 'student'
        """
        return Users.execute_write(sql, [paid_amount, payment_at, paid_amount, student_id])

    @staticmethod
    def reset_fee(student_id):
        """Reset fee payment amounts and mark as unpaid."""
        sql = """
            UPDATE users
            SET 
                fee_status = 'unpaid',
                fee_paid_amount = 0,
                fee_last_payment_at = NULL,
                fee_updated_at = CURRENT_TIMESTAMP
            WHERE id = %s AND role = 'student'
        """
        return Users.execute_write(sql, [student_id])

    @staticmethod
    def set_fee_details(student_id, fee_amount, fee_due_date=None):
        """Set total fee amount and due date for a student.

        Resets paid amount/payment info and marks fee as unpaid.
        """
        sql = """
            UPDATE users
            SET 
                fee_amount = %s,
                fee_due_date = %s,
                fee_status = 'unpaid',
                fee_paid_amount = 0,
                fee_last_payment_at = NULL,
                fee_updated_at = CURRENT_TIMESTAMP
            WHERE id = %s AND role = 'student'
        """
        return Users.execute_write(sql, [fee_amount, fee_due_date, student_id])

    @staticmethod
    def get_fee_status(user_id):
        """Fetch a user's fee status and related fee details."""
        sql = """
            SELECT 
                fee_status, fee_updated_at,
                fee_amount, fee_due_date, fee_paid_amount, fee_last_payment_at
            FROM users
            WHERE id = %s
        """
        return Users.fetch_one(sql, [user_id])

