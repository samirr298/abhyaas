from flask import render_template, request, redirect, url_for, flash
from app.controllers.base_controller import BaseController
from app.database import UserRepository
from app.models.user import User


class AuthController(BaseController):
    def __init__(self):
        self.user_repo = UserRepository()

    def login(self):
        # simple placeholder: on POST you would validate credentials
        if request.method == 'POST':
            print('login form', request.form)
            return redirect(url_for('auth.login'))
        return render_template('auth/login.html')

    def register(self):
        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            role = request.form.get('role', 'student').strip().lower()

            if not name or not email or not password:
                self._flash_errors('Please fill in all required fields')
                return render_template('auth/register.html')

            if not self._validate_name(name):
                self._flash_errors('Name must be at least 2 characters long')
                return render_template('auth/register.html')

            if not self._validate_email(email):
                self._flash_errors('Please enter a valid email address')
                return render_template('auth/register.html')

            if role not in ['student', 'teacher']:
                self._flash_errors('Please select a valid role')
                return render_template('auth/register.html')

            if self.user_repo.user_exists(email):
                self._flash_errors('Email already registered. Please login or use a different email.')
                return render_template('auth/register.html')

            password_valid, message = self._validate_password(password)
            if not password_valid:
                self._flash_errors(message)
                return render_template('auth/register.html')

            user = User(name=name, email=email, password=password, role=role)
            user.hash_password()
            user_id = self.user_repo.create_user(user)

            if user_id:
                flash('Registration successful! Please login to continue.', 'success')
                return redirect(url_for('auth.login'))

            self._flash_errors('Registration failed. Please try again later.')
            return render_template('auth/register.html')

        return render_template('auth/register.html')

    def forgot(self):
        if request.method == 'POST':
            print('forgot form', request.form)
            # TODO: lookup email and send reset link
            flash('If that email exists we sent reset instructions (demo)')
            return redirect(url_for('auth.login'))
        return render_template('auth/forgot.html')