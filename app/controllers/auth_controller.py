from flask import render_template, request, redirect, url_for, flash,session
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.user import Users
class AuthController:
    def login(self):
        if request.method == 'POST':
            print('login form data received:', request.form)
            email = request.form.get('email')
            password = request.form.get('password')
            
            # 1. Fetch user data from database
            user_details = Users.get_by_email(email)
            print("What Python sees from DB:", user_details)
            
            # ==========================================================
            # 🛡️ THE CRITICAL SAFETY GUARD:
            # ==========================================================
            if user_details is not None:
                # This block ONLY runs if a user row was actually found!
                if user_details['password_hash'] == password:
                    session['user_id'] = user_details['id']
                    session['role'] = user_details['role']
                    session['username'] = user_details['name'] 
                    if user_details['role'] == 'teacher':
                        return redirect(url_for('auth.teacher')) # Replace with your actual teacher route
                    elif user_details['role'] == 'student':
                        return redirect(url_for('auth.student')) # Goes to student dashboard
                    else:
                        return redirect(url_for('auth.student'))
                else:
                    flash("Incorrect password.", "error")
                    print("🛑 Password did not match!")
            else:
                # This runs safely instead of crashing if the email doesn't exist
                flash("No account found with that email.", "error")
                print("🛑 Email not found in database!")
            # ==========================================================
                
            return redirect(url_for('auth.login'))
            
        return render_template('auth/login.html')

    def register(self):
        if request.method == 'POST':
            print('register form', request.form)
            return redirect(url_for('auth.login'))
        return render_template('auth/register.html')

    def forgot(self):
        if request.method == 'POST':
            print('forgot form', request.form)
            # TODO: lookup email and send reset link
            flash('If that email exists we sent reset instructions (demo)')
            return redirect(url_for('auth.login'))
        return render_template('auth/forgot.html')