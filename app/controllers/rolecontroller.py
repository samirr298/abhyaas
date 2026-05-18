from flask import render_template
from app.auth import login_required,role_required


class RoleController:
    @role_required("admin")
    @login_required
    
    def admin(self):
        # simple placeholder response for admin
        return render_template("users/admin_dashboard.html")

    @role_required("teacher")
    @login_required
    def teacher(self):
        # simple placeholder response for teacher
           return render_template("users/teacher_dashboard.html")

    @role_required("student")
    @login_required
    def student(self):
        # simple placeholder response for student
        return render_template("users/student_dashboard.html")