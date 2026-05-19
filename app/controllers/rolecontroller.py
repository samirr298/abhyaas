from flask import render_template
from app.auth import login_required,role_required


class RoleController:
    @login_required
    @role_required("admin")
    
    def admin(self):
        
        return render_template("users/admin_dashboard.html")
    @login_required
    @role_required("teacher")
    
    def teacher(self):
        # simple placeholder response for teacher
           return render_template("users/teacher_dashboard.html")
    @login_required
    @role_required("student")
    
    def student(self):
        # simple placeholder response for student
        return render_template("users/student_dashboard.html")