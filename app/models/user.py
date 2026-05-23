from app.models.base_model import BaseModel

class Users(BaseModel):
    
    @staticmethod
    def get_my_email(email):
        connection = None
        try:
            connection = BaseModel.get_connection()

            if connection is None:
                print("🚨 Error: db() returned None. Check app/database.py for a missing return statement!")
                return None

            with connection.cursor() as cursor:
                sql = "SELECT id, name, email, password_hash, role FROM users WHERE email = %s"
                cursor.execute(sql, [email])
                return cursor.fetchone()

        except Exception as e:
            print(f"🚨 Database error occurred: {e}")
            return None

        finally:
            if connection is not None:
                connection.close()

    @staticmethod
    def reset_password(email, password_hash):
        connection = None
        try:
            connection = BaseModel.get_connection()

            if connection is None:
                print("🚨 Error: db() returned None. Check app/database.py for a missing return statement!")
                return False
            
            with connection.cursor() as cursor:
                sql = "UPDATE users SET password_hash = %s WHERE email = %s"
                cursor.execute(sql, [password_hash, email])

            connection.commit()
            return True

        except Exception as e:
            print(f"🚨 Database error occurred while changing password: {e}")
            return False

        finally:
            if connection is not None:
                connection.close()
    @staticmethod
    def change_my_password(email):
        connection = BaseModel()
        if connection == None:
            print("RETURNED NONE  ")
            return None
        with connection.cursor() as cursor:
        # Example SELECT query
            sql = "SELECT password_hash, id FROM users WHERE email = %s"
            cursor.execute(sql, [email])
            result = cursor.fetchone()
            return result
    @staticmethod
    def finally_change_my_password(hashedpassword,email):
        connection = BaseModel()
        if connection == None:
            print("RETURNED NONE  ")
            return None
        with connection.cursor() as cursor:
        # Example SELECT query
            sql = "update users set password_hash = %s WHERE email = %s"
            cursor.execute(sql,(hashedpassword,email))
            
            return "Successfully Changed the password ! "

