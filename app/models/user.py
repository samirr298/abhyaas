from app.models.base_model import BaseModel

class Users(Basemodel):

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

