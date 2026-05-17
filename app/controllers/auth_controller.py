from flask import render_template,request


class AuthController:
    def login(self):
        print(request.form)
        return render_template("auth/login.html")

    def register(self):
        return render_template("auth/register.html")