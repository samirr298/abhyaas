from app.models.base_model import BaseModel

class Users(BaseModel):
    
    @staticmethod
    def get_my_email(email):
        sql = "SELECT id, name, username, email, password_hash, role FROM users WHERE email = %s"
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
    # Execute the query using your base framework data handler
        return Users.execute_write(sql, [filename, user_id])
