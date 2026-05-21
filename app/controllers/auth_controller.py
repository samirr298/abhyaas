from flask import render_template, request, redirect, url_for, flash,session
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.user import Users
from app import mail
from flask_mail import Message
import random
import time

class AuthController:
    def login(self):
        if request.method == 'POST':
            print('login form data received:', request.form)
            email = request.form.get('email')
            password = request.form.get('password')
            
            # 1. Fetch user data from database
            user_details = Users.get_my_email(email)
            print("What Python sees from DB:", user_details)
            
            # ==========================================================
            # 🛡️ THE CRITICAL SAFETY GUARD:
            # ==========================================================
            if user_details is not None:
                # This block ONLY runs if a user row was actually found!
                if check_password_hash(user_details['password_hash'], password):
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

    @staticmethod
    def forgot():
        if request.method == 'POST':
            print('forgot form', request.form)
            email = request.form.get('email')
            otp = str(random.randint(100000, 999999))
            
            flash('If that email exists, we sent a reset OTP.', 'info')
            
            try:
                msg = Message(
                    subject="Your Abhyas Password Reset OTP",
                    recipients=[email],
                    body=f"Your OTP is {otp}. It will expire soon."
                )
                
                if Users.get_my_email(email):
                    mail.send(msg)
                    
                session['reset_email'] = email
                session['reset_otp'] = otp
                session['otp_time'] = time.time()
                print(session.get('reset_otp'))
                return redirect(url_for('auth.verifyotp'))
                
            except Exception as e:
                # Flash a message instead of returning raw text to keep presentation in the View layer
                flash(f"Failed to send email: {str(e)}", "error")
                return redirect(url_for('auth.forgot'))
                
        return render_template('auth/forgot.html')

    @staticmethod
    def verifyotp():
        if request.method == "POST":
            newpass = request.form.get('new_password')
            user_entered = request.form.get('otp')
            
            # ⏳ 1. Check if OTP is incorrect or expired
            if user_entered != session.get('reset_otp') or (time.time() - session.get('otp_time', 0)) > 120:
                session.pop('reset_otp', None)
                session.pop('reset_email', None)
                session.pop('otp_time', None)
                flash("Time expired or OTP wrong", 'error')
                return redirect(url_for('auth.forgot'))
                
            # 🎉 2. Success Path
            if Users.get_my_email(session['reset_email']) is not None:              
                hashed_password = generate_password_hash(newpass)
                Users.change_password(session['reset_email'], hashed_password)
                
                # 🧹 Complete Cleanup
                session.pop('reset_otp', None)
                session.pop('reset_email', None)
                session.pop('otp_time', None)
                
                flash("Password changed successfully. Please sign in again.", "success")
                return redirect(url_for("auth.login"))
                
        return render_template('auth/verify_otp.html')
    def logout():
        pass

        
      