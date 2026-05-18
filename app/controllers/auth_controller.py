from flask import render_template, request, redirect, url_for, flash


class AuthController:
    def login(self):
        # simple placeholder: on POST you would validate credentials
        if request.method == 'POST':
            print('login form', request.form)
            # TODO: authenticate user here
            flash('Logged in (demo)')
            return redirect(url_for('auth.login'))
        return render_template("auth/login.html")

    def register(self):
        if request.method == 'POST':
            print('register form', request.form)
            # TODO: create user here
            flash('Account created (demo)')
            return redirect(url_for('auth.login'))
        return render_template("auth/register.html")

    def forgot(self):
        if request.method == 'POST':
            print('forgot form', request.form)
            # TODO: lookup email and send reset link
            flash('If that email exists we sent reset instructions (demo)')
            return redirect(url_for('auth.login'))
        return render_template('auth/forgot.html')