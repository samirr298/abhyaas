from flask import Blueprint
from app.controllers.task_controller import TaskController
from app.auth import login_required
class TaskRoutes:
    def __init__(self):
        self.bp = Blueprint('tasks', __name__)
        self.controller = TaskController()

    def register(self):
        # Teacher workspace
        self.bp.route("/teacher/tasks", methods=["GET", "POST"])(
            login_required(TaskController().teacher_task)
        )
        self.bp.route("/student/tasks", methods=["GET", "POST"])(
            login_required(TaskController().student_task)
        )
        self.bp.route("/task/<int:task_id>", methods=["GET", "POST"])(
            login_required(TaskController().view_task)
        )
        self.bp.route("/delete-task/<int:task_id>", methods=["GET", "POST"])(
            login_required(TaskController().task_delete)
        )
        self.bp.route("/task/<int:task_id>/bookmark", methods=["POST"])(
            login_required(TaskController().toggle_bookmark)
        )
        self.bp.route("/bookmarks", methods=["GET"])(
            login_required(TaskController().bookmarks)
        )
        self.bp.route('/notifications', methods=['GET'])(
            login_required(TaskController().notifications)
        )
        self.bp.route('/notifications/mark-all-read', methods=['POST'])(
            login_required(TaskController().mark_all_notifications)
        )
        
        return self.bp