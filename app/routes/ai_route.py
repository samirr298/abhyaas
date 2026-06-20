from flask import Blueprint, render_template, request, jsonify

from app.auth import login_required
from app.controllers.ai_controller import AIController


class AIRoutes:
    def __init__(self):
        self.bp = Blueprint("ai", __name__, url_prefix="")
        self.controller = AIController()

    def register(self):
        # AI page
        @self.bp.route("/ai", methods=["GET"])
        @login_required
        def ai_page():
            return render_template("ai_assistant.html")

        # AI ask endpoint
        @self.bp.route("/ai/ask", methods=["POST"])
        @login_required
        def ai_ask():
            return self.controller.ask()

        return self.bp

