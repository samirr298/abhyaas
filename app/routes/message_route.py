from flask import Blueprint
from app.controllers.message_controller import ChatController

# Module-level blueprint and controller instance
message_bp = Blueprint('messages', __name__)
chat_ctrl = ChatController()


# ========================================================
# ROUTE A: DEFAULT STATE (Opening the message landing page)
# ========================================================
@message_bp.route('/messages', methods=['GET'], endpoint='conversations')
def default_messages():
    """Runs when someone clicks 'Messages' from your application sidebar menu."""
    return chat_ctrl.message_center(active_conv_id=None)


# ========================================================
# ROUTE B: DYNAMIC STATE (Opening a specific conversation)
# ========================================================
@message_bp.route('/messages/<int:conversation_id>', methods=['GET'])
def open_conversation(conversation_id):
    """Runs when someone clicks a contact; Flask extracts the conversation ID."""
    return chat_ctrl.message_center(active_conv_id=conversation_id)


@message_bp.route('/messages/search', methods=['GET'])
def search_messages():
    """AJAX endpoint: returns JSON list of matching contacts/conversations."""
    q = None
    from flask import request
    q = request.args.get('q', '').strip()
    return chat_ctrl.search_people(q)


@message_bp.route('/messages/start/<int:user_id>', methods=['GET'])
def start_conversation(user_id):
    """Create a conversation with `user_id` if needed and redirect to it."""
    from flask import redirect, url_for
    conv_id = chat_ctrl.create_or_get_conversation(user_id)
    if conv_id:
        return redirect(url_for('messages.open_conversation', conversation_id=conv_id))
    return redirect(url_for('messages.conversations'))


@message_bp.route('/messages/send', methods=['POST'])
def send_message_http():
    """HTTP fallback to send a message when Socket.IO isn't available. Expects JSON."""
    from flask import request, jsonify
    data = request.get_json() or {}
    conv = data.get('conversation_id')
    msg = data.get('message', '').strip()
    if not conv or not msg:
        return jsonify({'ok': False, 'error': 'missing'}), 400

    new = chat_ctrl.http_send_message(conv, msg)
    if not new:
        return jsonify({'ok': False}), 500
    return jsonify({'ok': True, 'payload': new})