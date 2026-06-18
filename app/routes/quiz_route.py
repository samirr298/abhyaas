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
        
        self.bp.route("/student/start-quiz", methods=["POST"])(
            login_required(self.controller.start_quiz_session)
        )
        
        self.bp.route("/student/next-question", methods=["GET"])(
            login_required(self.controller.generate_next_question)
        )
        
        self.bp.route("/student/check-status", methods=["GET"])(
            login_required(self.controller.get_quiz_status)
        )
        
        self.bp.route("/student/save-quiz-history", methods=["POST"])(
            login_required(self.controller.save_quiz_history)
        )
        
        self.bp.route("/student/get-quiz-history", methods=["GET"])(
            login_required(self.controller.get_quiz_history)
        )

        return self.bp