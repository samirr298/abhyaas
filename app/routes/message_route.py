from flask import Blueprint
from app.controllers.message_controller import MessageController
from app.auth import login_required


class MessageRoutes:
    def __init__(self):
        self.bp = Blueprint('messages', __name__, url_prefix='/messages')
        self.controller = MessageController()

    def register(self):
        self.bp.route('/', methods=['GET'])(
            login_required(self.controller.conversations)
        )
        self.bp.route('/<int:conversation_id>', methods=['GET', 'POST'])(
            login_required(self.controller.conversation)
        )
        return self.bp
