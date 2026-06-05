from flask import Blueprint
from app.controllers.task_controller import TaskController

class TaskRoutes:
    def __init__(self):
        self.bp = Blueprint('tasks', __name__)
        self.controller = TaskController()

    def register(self):
        # Teacher workspace
        self.bp.route('/teacher_task', methods=['GET', 'POST'])(self.controller.teacher_dashboard)
        # Student workspace
        self.bp.route('/student_task', methods=['GET', 'POST'])(self.controller.student_dashboard)
        # Single task detail (student-facing)
        self.bp.route('/task/<int:task_id>', methods=['GET', 'POST'])(self.controller.task_detail)
        
        self.bp.route('/delete_task/<int:task_id>', methods=['GET', 'POST'])(self.controller.task_delete)
        
        return self.bp
