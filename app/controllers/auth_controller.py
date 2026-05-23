from flask import render_template, request, redirect, url_for, flash


class AuthController:
    def login(self):
        # simple placeholder: on POST you would validate credentials
        if request.method == 'POST':
            print('login form', request.form)
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

    def change_my_password(self):
        if request.method == 'POST':
            current_password = request.form.get('currentPassword', '').strip()
            new_password = request.form.get('newPassword', '').strip()
            confirm_password = request.form.get('confirmPassword', '').strip()

            if not current_password or not new_password or not confirm_password:
                flash('Please fill in all password fields.')
                return redirect(url_for('auth.change_my_password'))

            if new_password != confirm_password:
                flash('New password and confirm password do not match.')
                return redirect(url_for('auth.change_my_password'))

            if len(new_password) < 8:
                flash('New password must be at least 8 characters long.')
                return redirect(url_for('auth.change_my_password'))

            if current_password == new_password:
                flash('Your new password must be different from your current password.')
                return redirect(url_for('auth.change_my_password'))

            flash('Password change request received. The actual password update is not implemented yet.')
            return redirect(url_for('auth.change_my_password'))

        return render_template('auth/changemypassword.html')