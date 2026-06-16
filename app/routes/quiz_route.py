from flask import Blueprint
from app.controllers.quiz_controller import QuizController
from app.auth import login_required

class QuizRoutes:
    def __init__(self):
        self.bp = Blueprint('quiz', __name__)
        self.controller = QuizController()

    def register(self):
        self.bp.route("/student/quiz-generator", methods=["GET"])(
            login_required(self.controller.quiz_generator_page)
        )
        self.bp.route("/student/generate-quiz", methods=["POST"])(
            login_required(self.controller.generate_quiz)
        )
        self.bp.route("/student/submit-quiz", methods=["POST"])(
            login_required(self.controller.submit_quiz)
        )
        
        return self.bp