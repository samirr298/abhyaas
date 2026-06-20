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
        """Fetch all students with consolidated fee details from `fees` ledger.

        fee_filter: None (all), 'paid', or 'unpaid'
        """
        sql = """
            SELECT
                u.id, u.name, u.username, u.email,
                COALESCE(SUM(f.amount), 0) AS fee_amount,
                COALESCE(SUM(f.paid_amount), 0) AS fee_paid_amount,
                MAX(f.due_date) AS fee_due_date,
                CASE
                    WHEN COALESCE(SUM(f.amount), 0) = 0 THEN 'paid'
                    WHEN COALESCE(SUM(f.paid_amount), 0) >= COALESCE(SUM(f.amount), 0) THEN 'paid'
                    ELSE 'unpaid'
                END AS fee_status,
                MAX(f.updated_at) AS fee_updated_at,
                MAX(
                    CASE
                        WHEN t.payment_date IS NOT NULL THEN t.payment_date
                        ELSE NULL
                    END
                ) AS fee_last_payment_at
            FROM users u
            LEFT JOIN fees f ON f.student_id = u.id
            LEFT JOIN fee_transactions t ON t.fee_id = f.id
            WHERE u.role = 'student'
            GROUP BY u.id, u.name, u.username, u.email
        """

        params = []
        if fee_filter in ['paid', 'unpaid']:
            sql += " HAVING (CASE WHEN COALESCE(SUM(f.amount), 0) = 0 THEN 'paid' WHEN COALESCE(SUM(f.paid_amount), 0) >= COALESCE(SUM(f.amount), 0) THEN 'paid' ELSE 'unpaid' END) = %s"
            params = [fee_filter]

        sql += " ORDER BY u.name ASC"
        rows = Users.fetch_all(sql, params) or []
        # Normalize potential datetime/date fields to strings so templates
        # won't need to call .strftime (which can error if values are strings).
        for r in rows:
            if r.get('fee_due_date') and hasattr(r['fee_due_date'], 'strftime'):
                try:
                    r['fee_due_date'] = r['fee_due_date'].strftime('%Y-%m-%d')
                except Exception:
                    r['fee_due_date'] = str(r['fee_due_date'])
            if r.get('fee_updated_at') and hasattr(r['fee_updated_at'], 'strftime'):
                try:
                    r['fee_updated_at'] = r['fee_updated_at'].strftime('%b %d, %Y')
                except Exception:
                    r['fee_updated_at'] = str(r['fee_updated_at'])
            if r.get('fee_last_payment_at') and hasattr(r['fee_last_payment_at'], 'strftime'):
                try:
                    r['fee_last_payment_at'] = r['fee_last_payment_at'].strftime('%b %d, %Y')
                except Exception:
                    r['fee_last_payment_at'] = str(r['fee_last_payment_at'])

        return rows


    @staticmethod
    def get_student_by_id(student_id):
        """Fetch a specific student by ID."""
        sql = """
            SELECT id, name, username, email
            FROM users
            WHERE id = %s AND role = 'student'
        """
        return Users.fetch_one(sql, [student_id])


    @staticmethod
    def update_fee_status(student_id, fee_status):
        """Update fee status and timestamp for a student."""
        # Operate on the multi-invoice ledger. If setting to 'paid', mark all
        # fee rows for the student as paid (paid_amount = amount). If setting to
        # 'unpaid', reset paid_amount to 0 and mark unpaid. This keeps the
        # historical fees table consistent instead of relying on removed user
        # table columns.
        if fee_status == 'paid':
            sql = """
                UPDATE fees
                SET paid_amount = amount, status = 'paid', updated_at = CURRENT_TIMESTAMP
                WHERE student_id = %s
            """
            return Users.execute_write(sql, [student_id])

        if fee_status == 'unpaid':
            # remove transaction history for this user's fees and mark unpaid
            try:
                # delete transactions for all fees of this student
                tx_sql = "DELETE t FROM fee_transactions t JOIN fees f ON t.fee_id = f.id WHERE f.student_id = %s"
                Users.execute_write(tx_sql, [student_id])
            except Exception:
                pass

            sql = """
                UPDATE fees
                SET paid_amount = 0.00, status = 'unpaid', updated_at = CURRENT_TIMESTAMP
                WHERE student_id = %s
            """
            return Users.execute_write(sql, [student_id])

        # Unknown status — no-op
        return False

    @staticmethod
    def record_fee_payment(student_id, paid_amount, payment_at=None):
        """Record a payment for the student and update fee status/timestamps."""
        # Route this to the ledger by creating a payment against the oldest unpaid fee.
        return Users.add_fee_payment(student_id, paid_amount, payment_at)

    @staticmethod
    def reset_fee(student_id):
        """Reset fee payment amounts and mark as unpaid."""
        # Reset all fee ledger rows for the student
        try:
            Users.execute_write("DELETE t FROM fee_transactions t JOIN fees f ON t.fee_id = f.id WHERE f.student_id = %s", [student_id])
        except Exception:
            pass
        sql = "UPDATE fees SET paid_amount = 0.00, status = 'unpaid', updated_at = CURRENT_TIMESTAMP WHERE student_id = %s"
        return Users.execute_write(sql, [student_id])

    @staticmethod
    def set_fee_details(student_id, fee_amount, fee_due_date=None):
        """Set total fee amount and due date for a student.

        Resets paid amount/payment info and marks fee as unpaid.
        """
        # Replace single-field user fee with a single invoice on fees table.
        return Users.add_student_due(student_id, 'Manual Fee Update', fee_amount, fee_due_date)

    @staticmethod
    def add_fee_amount(student_id, fee_amount, fee_due_date=None):
        """Accumulate total fee amount for a student.

        Adds to existing fee_amount and keeps current paid amounts.
        Updates fee_due_date if provided.
        """
        # Create a new fee line instead of mutating legacy user columns
        return Users.add_student_due(student_id, 'Bulk/Incremental Charge', fee_amount, fee_due_date)

    @staticmethod
    def add_fee_payment(student_id, payment_amount, payment_at=None):
        """Accumulate paid amount for a student (reduces dues).

        fee_paid_amount is increased by payment_amount. fee_status updates based on whether paid >= fee_amount.
        """
        # Route this to the ledger by creating a new payment against the oldest unpaid fee.
        # Find an unpaid fee for the student
        fee = Users.fetch_one("SELECT id, amount, paid_amount FROM fees WHERE student_id = %s AND status = 'unpaid' ORDER BY created_at ASC LIMIT 1", [student_id])
        if not fee:
            return False

        new_paid = float(fee['paid_amount'] or 0) + float(payment_amount)
        new_status = 'paid' if new_paid >= float(fee['amount'] or 0) else 'unpaid'
        Users.execute_write("UPDATE fees SET paid_amount = %s, status = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s", [new_paid, new_status, fee['id']])
        Users.execute_write("INSERT INTO fee_transactions (fee_id, amount_paid) VALUES (%s, %s)", [fee['id'], payment_amount])
        return True


    @staticmethod
    def get_fee_status(user_id):
        """Fetch a user's fee status and related fee details."""
        sql = """
            SELECT
                COALESCE(SUM(f.amount), 0) AS fee_amount,
                COALESCE(SUM(f.paid_amount), 0) AS fee_paid_amount,
                CASE
                    WHEN COALESCE(SUM(f.amount), 0) = 0 THEN 'paid'
                    WHEN COALESCE(SUM(f.paid_amount), 0) >= COALESCE(SUM(f.amount), 0) THEN 'paid'
                    ELSE 'unpaid'
                END AS fee_status,
                MIN(CASE WHEN f.status != 'paid' THEN f.due_date ELSE NULL END) AS fee_due_date,
                MAX(f.updated_at) AS fee_updated_at
            FROM fees f
            WHERE f.student_id = %s
        """
        result = Users.fetch_one(sql, [user_id])
        return result or {'fee_status': 'unpaid', 'fee_amount': 0, 'fee_paid_amount': 0, 'fee_due_date': None, 'fee_updated_at': None}

    # --- Multi-Invoice Fees Ledger Helpers ---
    @staticmethod
    def add_student_due(student_id, title, amount, due_date=None):
        """Insert a brand new dynamic due invoice line for a student."""
        sql = """
            INSERT INTO fees (student_id, title, amount, due_date, status)
            VALUES (%s, %s, %s, %s, 'unpaid')
        """
        return Users.execute_write(sql, [student_id, title, amount, due_date])

    @staticmethod
    def get_fees_by_student_id(student_id):
        """Fetch all individual invoice due lines assigned to a specific student."""
        sql = "SELECT id, title, amount, paid_amount, status, due_date, updated_at FROM fees WHERE student_id = %s ORDER BY created_at DESC"
        rows = Users.fetch_all(sql, [student_id]) or []
        # Normalize date/datetime fields to simple strings for templates to avoid
        # calling .strftime() in templates (which can fail if values are already strings).
        for r in rows:
            if r.get('updated_at') and hasattr(r['updated_at'], 'strftime'):
                try:
                    r['updated_at'] = r['updated_at'].strftime('%b %d, %Y')
                except Exception:
                    r['updated_at'] = str(r['updated_at'])
            if r.get('due_date') and hasattr(r['due_date'], 'strftime'):
                try:
                    r['due_date'] = r['due_date'].strftime('%Y-%m-%d')
                except Exception:
                    r['due_date'] = str(r['due_date'])
        return rows

    @staticmethod
    def record_payment_on_fee(fee_id, payment_amount):
        """Record payment collection and log the specific transaction receipt."""
        sql_fetch = "SELECT amount, paid_amount FROM fees WHERE id = %s"
        fee = Users.fetch_one(sql_fetch, [fee_id])
        if not fee:
            return False
            
        new_paid = float(fee['paid_amount'] or 0) + float(payment_amount)
        new_status = 'paid' if new_paid >= float(fee['amount'] or 0) else 'unpaid'
        
        sql_update = """
            UPDATE fees 
            SET paid_amount = %s, status = %s, updated_at = CURRENT_TIMESTAMP 
            WHERE id = %s
        """
        success = Users.execute_write(sql_update, [new_paid, new_status, fee_id])
        
        if success:
            sql_log = "INSERT INTO fee_transactions (fee_id, amount_paid) VALUES (%s, %s)"
            Users.execute_write(sql_log, [fee_id, payment_amount])
            
        return success

    @staticmethod
    def reset_single_fee(fee_id):
        """Flush transaction history for a single invoice row line item back to 0."""
        Users.execute_write("DELETE FROM fee_transactions WHERE fee_id = %s", [fee_id])
        
        sql = "UPDATE fees SET paid_amount = 0.00, status = 'unpaid' WHERE id = %s"
        return Users.execute_write(sql, [fee_id])
    
    @staticmethod
    def get_transactions_by_student_id(student_id):
        """Fetch every individual partial payment receipt for a student."""
        sql = """
            SELECT t.fee_id, t.amount_paid, t.payment_date 
            FROM fee_transactions t
            JOIN fees f ON t.fee_id = f.id
            WHERE f.student_id = %s
            ORDER BY t.payment_date DESC
        """
        rows = Users.fetch_all(sql, [student_id]) or []
        for r in rows:
            if r.get('payment_date') and hasattr(r['payment_date'], 'strftime'):
                try:
                    r['payment_date'] = r['payment_date'].strftime('%b %d, %Y')
                except Exception:
                    r['payment_date'] = str(r['payment_date'])
        return rows
    
    @staticmethod
    def delete_fee(fee_id):
        """Permanently delete an invoice and all cascaded payment receipts."""
        sql = "DELETE FROM fees WHERE id = %s"
        return Users.execute_write(sql, [fee_id])