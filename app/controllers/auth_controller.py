from flask import render_template, request, redirect, url_for, flash, jsonify
from app.controllers.base_controller import BaseController
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.user import Users
from app import mail
from app.auth import login_required
from flask_mail import Message
import random
import time
from app.models.base_model import BaseModel
import os

class AuthController(BaseController):
    
    def login(self):
        if request.method == 'POST':
            print('login form data received:', request.form)
            email = request.form.get('email')
            password = request.form.get('password')
            
            user_details = Users.get_my_email(email)
            print("What Python sees from DB:", user_details)
            
            if user_details is not None:
                if check_password_hash(user_details['password_hash'], password):
                    self.session['user_id'] = user_details['id']
                    self.session['role'] = user_details['role']
                    # prefer username if set otherwise use name
                    self.session['username'] = user_details.get('username') or user_details.get('name')
                    self.session['name'] = user_details.get('name')
                    self.session['email'] = email
                    self.session['profile_pic'] = user_details.get('profile_pic')
                    
                    if user_details['role'] == 'teacher':
                        return self.redirect_to('auth.teacher_dashboard')
                    else:
                        return self.redirect_to('auth.student_dashboard')
                else:
                    self.flash("Incorrect password.", "error")
            else:
                self.flash("No account found with that email.", "error")
                
            return self.redirect_to('auth.login')
            
        return self.render('auth/login.html')

    def register(self):
        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            role = request.form.get('role', 'student').strip().lower()

            if not name or not email or not password or not username:
                flash('Please fill in all required fields', 'error')
                return self.render('auth/register.html')

            if not self._validate_name(name):
                flash('Name must be at least 2 characters long', 'error')
                return self.render('auth/register.html')

            if not self._validate_email(email):
                flash('Please enter a valid email address', 'error')
                return self.render('auth/register.html')

            if role not in ['student', 'teacher']:
                flash('Please select a valid role', 'error')
                return self.render('auth/register.html')

            sql = "select id from users where email = %s"
            if BaseModel.fetch_one(sql, [email]):
                self.flash('Email already registered. Please login or use a different email.', 'error')
                return self.render('auth/register.html')

            # validate username (3-30 chars, letters/numbers/underscores)
            import re
            if not re.match(r'^[A-Za-z0-9_]{3,30}$', username):
                flash('Username must be 3-30 chars and contain only letters, numbers, and underscores.', 'error')
                return self.render('auth/register.html')

            if Users.is_username_taken(username):
                flash('Username already taken. Please choose another one.', 'error')
                return self.render('auth/register.html')

            password_valid, message = self._validate_password(password)
            if not password_valid:
                flash(message, 'error')
                return self.render('auth/register.html')
            user_created = Users.create_user(name, username, email, generate_password_hash(password), role)

            if user_created:
                flash('Registration successful! Please login to continue.', 'success')
                return redirect(url_for('auth.login'))

            flash('Registration failed. Please try again later.', 'error')
            return self.render('auth/register.html')

        return self.render('auth/register.html')

    def check_username(self):
        username = request.args.get('username', '').strip()
        import re
        if not username or not re.match(r'^[A-Za-z0-9_]{3,30}$', username):
            return jsonify({'available': False})

        # If logged in and checking the same username as the current user, consider it available
        current_user_id = self.session.get('user_id')
        existing = Users.get_by_username(username)
        if existing:
            if current_user_id and existing.get('id') == current_user_id:
                return jsonify({'available': True})
            return jsonify({'available': False})

        return jsonify({'available': True})

    def forgot(self):
        if request.method == 'POST':
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

                self.session['otp_purpose'] = 'reset_password'
                self.session['otp_email'] = email
                self.session['otp_code'] = otp
                self.session['otp_time'] = time.time()
                return self.redirect_to('auth.verifyotp')
                
            except Exception as e:
                self.flash(f"Failed to send email: {str(e)}", "error")
                return self.redirect_to('auth.forgot')

        return self.render('auth/forgot.html')

    def verifyotp(self):
        if request.method == "POST":
            purpose = self.session.get('otp_purpose')
            newpass = request.form.get('new_password')
            user_entered = request.form.get('otp')
            
            if user_entered != self.session.get('otp_code') or (time.time() - self.session.get('otp_time', 0)) > 120:
                self.session.pop('otp_purpose', None)
                self.session.pop('otp_email', None)
                self.session.pop('otp_code', None)
                self.session.pop('otp_time', None)
                self.session.flash("Time expired or OTP wrong", 'error')
                return self.redirect_to('auth.forgot')
                
            if purpose == 'reset_password':
                if not newpass:
                    self.flash("Please enter a new password.", "error")
                    return self.redirect_to('auth.verifyotp')

                if Users.get_my_email(self.session['otp_email']) is not None:
                    hashed_password = generate_password_hash(newpass)
                    Users.reset_password(self.session['otp_email'], hashed_password)

                    self.session.pop('otp_purpose', None)
                    self.session.pop('otp_email', None)
                    self.session.pop('otp_code', None)
                    self.session.pop('otp_time', None)

                    self.flash("Password changed successfully. Please sign in again.", "success")
                    return self.redirect_to("auth.login")
                
        return self.render('auth/verify_otp.html', otp_purpose=self.session.get('otp_purpose'))

    @login_required
    def profile(self):
        if request.method == 'POST':
            user_id = self.session.get('user_id')
            profile_updated = False

            # Handle profile-picture-only uploads from the inline upload form.
            # That form sends only file + upload_only flag, without profile text fields.
            upload_only = request.form.get('upload_only') == '1'
            valid_extensions = ['.jpg', '.jpeg', '.png']

            if upload_only:
                filee = request.files.get('profile_image')
                if not filee or filee.filename == '':
                    flash('Please choose an image to upload.', 'error')
                    return redirect(url_for('auth.profile'))

                file_extension = os.path.splitext(filee.filename)[1].lower()
                if file_extension not in valid_extensions:
                    flash('Wrong file format. Please choose a JPG, JPEG, or PNG image.', 'error')
                    return redirect(url_for('auth.profile'))

                upload_folder = os.path.join('app', 'static', 'images', 'profile_pics')
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)

                filename = f"user_{user_id}_profile{file_extension}"
                destination_path = os.path.join(upload_folder, filename)
                filee.save(destination_path)

                if Users.update_profile_pic(user_id, filename):
                    self.session['profile_pic'] = filename
                    flash('Profile picture updated successfully!', 'success')
                else:
                    flash('Profile picture database update failed.', 'error')
                return redirect(url_for('auth.profile'))

            full_name = request.form.get('full_name', '').strip()
            email = request.form.get('email', '').strip()
            new_username = request.form.get('username', '').strip()

            if not full_name or not email or not new_username:
                flash('Please fill in full name, email, and username.', 'error')
                return redirect(url_for('auth.profile'))

            if not self._validate_name(full_name):
                flash('Name must be at least 2 characters long.', 'error')
                return redirect(url_for('auth.profile'))

            if not self._validate_email(email):
                flash('Please enter a valid email address.', 'error')
                return redirect(url_for('auth.profile'))

            import re
            if not re.match(r'^[A-Za-z0-9_]{3,30}$', new_username):
                flash('Username must be 3-30 chars and contain only letters, numbers, and underscores.', 'error')
                return redirect(url_for('auth.profile'))

            existing = Users.get_by_username(new_username)
            if existing and existing['id'] != user_id:
                flash('Username already taken. Please choose another one.', 'error')
                return redirect(url_for('auth.profile'))

            db_updated = Users.update_profile_details(user_id, full_name, email)
            if db_updated:
                self.session['email'] = email
                self.session['name'] = full_name
                profile_updated = True
            else:
                flash('Profile details could not be saved.', 'error')
                return redirect(url_for('auth.profile'))

            if Users.set_username(user_id, new_username):
                self.session['username'] = new_username
                profile_updated = True
            else:
                flash('Failed to update username. Try again later.', 'error')
                return redirect(url_for('auth.profile'))

            # Profile image upload (when saving details form with an optional new image)
            filee = request.files.get('profile_image')
            if filee and filee.filename != '':
                upload_folder = os.path.join('app', 'static', 'images', 'profile_pics')
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
                file_extension = os.path.splitext(filee.filename)[1].lower()
                if file_extension not in valid_extensions:
                    flash("Wrong file format. Please choose a JPG, JPEG, or PNG image.", "error")
                    return redirect(url_for('auth.profile'))

                filename = f"user_{user_id}_profile{file_extension}"
                destination_path = os.path.join(upload_folder, filename)
                filee.save(destination_path)

                db_updated = Users.update_profile_pic(user_id, filename)
                if db_updated:
                    self.session['profile_pic'] = filename
                    profile_updated = True
                else:
                    flash("Profile picture database update failed.", "error")
                    return redirect(url_for('auth.profile'))

            if profile_updated:
                flash("Profile updated successfully!", "success")
            elif not full_name and not email and not new_username and (not filee or filee.filename == ''):
                flash("No changes were submitted.", "info")

            return redirect(url_for('auth.profile'))

        # --- GET Request Render Execution ---
        profile_pic_name = self.session.get('profile_pic')
        return self.render(
            "users/profile.html",
            email=self.session.get('email'),
            role=self.session.get('role'),
            username=self.session.get('username'),
            full_name=self.session.get('name') or self.session.get('username'),
            profile_url=url_for('static', filename=f"images/profile_pics/{profile_pic_name}") if profile_pic_name else None,
            filename=profile_pic_name
        )

    @login_required        
    def logout(self):
        self.session.clear()
        return self.redirect_to("auth.login")

    @login_required    
    def change_my_password(self):
        if request.method == 'POST':
            current_password = request.form.get('currentPassword', '').strip()
            new_password = request.form.get('newPassword', '').strip()
            confirm_password = request.form.get('confirmPassword', '').strip()
            
            if not current_password or not new_password or not confirm_password:
                flash('Please fill in all password fields.', 'error')
                return redirect(url_for('auth.change_my_password'))

            if new_password != confirm_password:
                flash('New password and confirm password do not match.', 'error')
                return redirect(url_for('auth.change_my_password'))

            if len(new_password) < 8:
                flash('New password must be at least 8 characters long.', 'error')
                return redirect(url_for('auth.change_my_password'))

            if current_password == new_password:
                flash('Your new password must be different from your current password.', 'error')
                return redirect(url_for('auth.change_my_password'))
                
            email = self.session['email']
            user_details = Users.get_my_email(email)
            if check_password_hash(user_details['password_hash'], current_password):
                msg = Users.finally_change_my_password(generate_password_hash(new_password), email)
                flash(msg, 'success')
                self.session.clear()
                return redirect(url_for('auth.login'))
            else:
                flash('Incorrect current password.', 'error')
                
        return self.render('auth/changemypassword.html')