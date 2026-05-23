from flask import request
from app.controllers.base_controller import BaseController
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.user import Users
from app import mail
from flask_mail import Message
import random
import time

class AuthController(BaseController):
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
                    self.session['user_id'] = user_details['id']
                    self.session['role'] = user_details['role']
                    self.session['username'] = user_details['name']
                    self.session['email'] = email
                    if user_details['role'] == 'teacher':
                        return self.redirect_to('auth.teacher')
                    elif user_details['role'] == 'student':
                        return self.redirect_to('auth.student')
                    else:
                        return self.redirect_to('auth.student')
                else:
                    self.flash("Incorrect password.", "error")
                    print("🛑 Password did not match!")
            else:
                # This runs safely instead of crashing if the email doesn't exist
                self.flash("No account found with that email.", "error")
                print("🛑 Email not found in database!")
            # ==========================================================
                
            return self.redirect_to('auth.login')
            
        return self.render('auth/login.html')

    def register(self):
        if request.method == 'POST':
            print('register form', request.form)
            return self.redirect_to('auth.login')
        return self.render('auth/register.html')

    def forgot(self):
        if request.method == 'POST':
            print('forgot form', request.form)
            email = request.form.get('email')
            otp = str(random.randint(100000, 999999))
            
            self.flash('If that email exists, we sent a reset OTP.', 'info')
            
            try:
                msg = Message(
                    subject="Your Abhyas Password Reset OTP",
                    recipients=[email],
                    body=f"Your OTP is {otp}. It will expire soon."
                )
                
                if Users.get_my_email(email):
                    mail.send(msg)

                self.session['reset_email'] = email
                self.session['reset_otp'] = otp
                self.session['otp_time'] = time.time()
                print(self.session.get('reset_otp'))
                return self.redirect_to('auth.verifyotp')
                
            except Exception as e:
                # Flash a message instead of returning raw text to keep presentation in the View layer
                self.flash(f"Failed to send email: {str(e)}", "error")
                return self.redirect_to('auth.forgot')
                
            return self.render('auth/forgot.html')

    def verifyotp(self):
        if request.method == "POST":
            newpass = request.form.get('new_password')
            user_entered = request.form.get('otp')
            
            # ⏳ 1. Check if OTP is incorrect or expired
            if user_entered != self.session.get('reset_otp') or (time.time() - self.session.get('otp_time', 0)) > 120:
                self.session.pop('reset_otp', None)
                self.session.pop('reset_email', None)
                self.session.pop('otp_time', None)
                self.flash("Time expired or OTP wrong", 'error')
                return self.redirect_to('auth.forgot')
                
            # 🎉 2. Success Path
            if Users.get_my_email(self.session['reset_email']) is not None:              
                hashed_password = generate_password_hash(newpass)
                Users.reset_password(self.session['reset_email'], hashed_password)

                # 🧹 Complete Cleanup
                self.session.pop('reset_otp', None)
                self.session.pop('reset_email', None)
                self.session.pop('otp_time', None)

                self.flash("Password changed successfully. Please sign in again.", "success")
                return self.redirect_to("auth.login")
                
        return self.render('auth/verify_otp.html')
    def logout(self):
        self.session.clear()
        return self.redirect_to("auth.login")
        pass

        
      