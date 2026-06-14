from flask import session
from flask_socketio import join_room, emit
from app.models.base_model import BaseModel
from datetime import datetime

def init_chat_sockets(socketio):
    """
    This function hooks our listeners up to the socketio instance 
    when the application boots up.
    """

    @socketio.on('join_private_room')
    def handle_join(data):
        conversation_id = data.get('conversation_id')
        room_name = f"chat_{conversation_id}"
        join_room(room_name)
        print(f"🔒 Secure real-time pipe opened for Room: {room_name}")


    @socketio.on('send_live_msg')
    def handle_message(data):
        conversation_id = data.get('conversation_id')
        message_text = data.get('message', '').strip()
        
        sender_id = session.get('user_id')
        sender_name = session.get('username') or session.get('name')

        print(f"[socket] recv send_live_msg: conv={conversation_id} sender={sender_id} msg='{message_text}'")

        if not message_text or not conversation_id:
            print("[socket] missing message_text or conversation_id")
            return

        # 1️⃣ Save to MySQL ledger instantly
        insert_sql = """
            INSERT INTO messages (conversation_id, sender_id, message_text) 
            VALUES (%s, %s, %s)
        """
        BaseModel.execute_write(insert_sql, [conversation_id, sender_id, message_text])
        print(f"[socket] saved message to DB for conv={conversation_id}")

        # 2️⃣ Package data with timestamp for UI ingestion
        payload = {
            'sender_id': sender_id,
            'sender_name': sender_name,
            'message': message_text,
            'time': datetime.now().strftime('%I:%M %p')
        }

        # 3️⃣ Broadcast securely down the private channel line
        room_name = f"chat_{conversation_id}"
        emit('receive_live_msg', payload, to=room_name)
        print(f"[socket] emitted receive_live_msg to {room_name}")