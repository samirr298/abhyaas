from flask import render_template

from app.auth import login_required, role_required
from app.controllers.task_controller import TaskController


class RoleController:
    @login_required ##completed
    @role_required("admin")
    
    def admin(self):
        
        return render_template("users/admin_dashboard.html")

    @login_required
    @role_required("teacher")
    def teacher(self):
        return TaskController().teacher_dashboard()

    @login_required
    @role_required("student")
    def student(self):
        return TaskController().student_dashboard()