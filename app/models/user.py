from app.models.base_model import BaseModel

class Users(BaseModel):
    
    @staticmethod
    def get_my_email(email):
        sql = "SELECT id, name, username, profile_pic, email, password_hash, role FROM users WHERE email = %s"
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
    def get_all_users():
        sql = "SELECT id, name, username, email, role FROM users ORDER BY created_at DESC"
        return Users.fetch_all(sql) or []

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
        Fetch all students with their fee status.
        fee_filter: None (all), 'paid', or 'unpaid'
        """
        sql = "SELECT id, name, username, email, fee_status, fee_updated_at FROM users WHERE role = 'student'"
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
        sql = "SELECT id, name, username, email, fee_status, fee_updated_at FROM users WHERE id = %s AND role = 'student'"
        return Users.fetch_one(sql, [student_id])

    @staticmethod
    def update_fee_status(student_id, fee_status):
        """Update fee status and timestamp for a student."""
        sql = "UPDATE users SET fee_status = %s, fee_updated_at = CURRENT_TIMESTAMP WHERE id = %s AND role = 'student'"
        return Users.execute_write(sql, [fee_status, student_id])

    @staticmethod
    def get_fee_status(user_id):
        """Fetch a user's fee status and last update timestamp."""
        sql = "SELECT fee_status, fee_updated_at FROM users WHERE id = %s"
        return Users.fetch_one(sql, [user_id])
