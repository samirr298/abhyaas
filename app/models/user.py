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
    def set_username(user_id, username):
        sql = "UPDATE users SET username = %s WHERE id = %s"
        try:
            return Users.execute_write(sql, [username, user_id])
        except Exception:
            # Likely a UNIQUE constraint violation — caller will handle False
            return False
