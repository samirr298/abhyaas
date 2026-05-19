from app.database import db

class Users:
    
    def get_by_email(email):
        connection = None
        try:
            # 1. Grab the connection (Make sure app/database.py returns it!)
            connection = db() 
            
            # If your db() returned None, raise an error immediately before trying to use it
            if connection is None:
                print("🚨 Error: db() returned None. Check app/database.py for a missing return statement!")
                return None

            # 2. FIXED: Added .cursor() here
            with connection.cursor() as cursor:
                sql = "SELECT id, name, email, password_hash, role FROM users WHERE email = %s"
                
                # Using a list [email] here is cleaner than the (email,) tuple syntax!
                cursor.execute(sql, [email])
                return cursor.fetchone()
                
        except Exception as e:
            print(f"🚨 Database error occurred: {e}")
            return None
            
        finally:
            # 3. FIXED: Only close if the connection was actually established
            if connection is not None:
                connection.close()