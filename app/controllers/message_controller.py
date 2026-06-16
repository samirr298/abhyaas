from flask import session, redirect, url_for
from flask import jsonify
from app.controllers.base_controller import BaseController
from app.models.base_model import BaseModel

class ChatController(BaseController):

    def message_center(self, active_conv_id=None):
        """
        The core engine method that extracts chat metrics 
        and passes them down into your messages.html view template.
        """
        # 1️⃣ Securely extract authentication states from session memory
        current_user_id = session.get('user_id')
        user_role = session.get('role') # Assumes 'student' or 'teacher' saved at login
        
        if not current_user_id:
            return redirect(url_for('auth.login'))

        # 2️⃣ FETCH SIDEBAR CONTACTS: Identify who this user has open channels with
        # If a student is logged in, look up their teachers. If a teacher is logged in, look up their students.
        # Build a sidebar query that also fetches the last message and its time per conversation
        if user_role == 'teacher':
            sidebar_sql = """
                  SELECT c.id AS conversation_id,
                      u.id AS user_id,
                      u.name AS name,
                       lm.message_text AS last_message,
                       DATE_FORMAT(lm.created_at, '%%h:%%i %%p') AS last_message_time
                FROM conversations c
                JOIN users u ON c.student_id = u.id
                LEFT JOIN (
                    SELECT m1.conversation_id, m1.message_text, m1.created_at
                    FROM messages m1
                    JOIN (
                        SELECT conversation_id, MAX(created_at) AS max_created
                        FROM messages
                        GROUP BY conversation_id
                    ) m2 ON m1.conversation_id = m2.conversation_id AND m1.created_at = m2.max_created
                ) lm ON lm.conversation_id = c.id
                WHERE c.teacher_id = %s
                ORDER BY lm.created_at DESC
            """
        else:
            sidebar_sql = """
                  SELECT c.id AS conversation_id,
                      u.id AS user_id,
                      u.name AS name,
                       lm.message_text AS last_message,
                       DATE_FORMAT(lm.created_at, '%%h:%%i %%p') AS last_message_time
                FROM conversations c
                JOIN users u ON c.teacher_id = u.id
                LEFT JOIN (
                    SELECT m1.conversation_id, m1.message_text, m1.created_at
                    FROM messages m1
                    JOIN (
                        SELECT conversation_id, MAX(created_at) AS max_created
                        FROM messages
                        GROUP BY conversation_id
                    ) m2 ON m1.conversation_id = m2.conversation_id AND m1.created_at = m2.max_created
                ) lm ON lm.conversation_id = c.id
                WHERE c.student_id = %s
                ORDER BY lm.created_at DESC
            """

        # Execute the query against your BaseModel handler engine
        teachers_list = BaseModel.fetch_all(sidebar_sql, [current_user_id]) or []

        # 3️⃣ FETCH HISTORY THREAD: If a target conversation window is open, extract the text logs
        history = []
        partner_name = None

        if active_conv_id:
            # Fetch all messages matching this unique conversation ID primary key channel
            history_sql = """
                SELECT m.sender_id, m.message_text, DATE_FORMAT(m.created_at, '%%h:%%i %%p') AS msg_time
                FROM messages m
                WHERE m.conversation_id = %s
                ORDER BY m.created_at ASC
            """
            history = BaseModel.fetch_all(history_sql, [active_conv_id]) or []

            # Identify the partner's name for your chat banner 🖥️
            meta_sql = """
                SELECT t.name AS teacher_name, s.name AS student_name 
                FROM conversations c
                JOIN users t ON c.teacher_id = t.id
                JOIN users s ON c.student_id = s.id
                WHERE c.id = %s
            """
            meta = BaseModel.fetch_one(meta_sql, [active_conv_id])
            if meta:
                partner_name = meta['student_name'] if user_role == 'teacher' else meta['teacher_name']

        # 4️⃣ TRANSMIT VALS TO JINJA: Ship the structured metrics directly into your custom HTML view template
        return self.render(
            'chat/message.html',
            teachers=teachers_list,       # Matches your {% for teacher in teachers %} loop!
            history=history,               # Matches your {% for msg in history %} loop!
            active_conv_id=active_conv_id, # Injected straight into your JavaScript variables!
            partner_name=partner_name,
            current_user_id=current_user_id
        )

    def search_people(self, query):
        """Search contacts and messages for the current user. Returns JSON."""
        current_user_id = session.get('user_id')
        user_role = session.get('role')
        if not current_user_id:
            return jsonify([])

        q_param = f"%{query}%" if query else '%'

        # Search users (opposite role) and left-join to any existing conversation + last message
        if user_role == 'teacher':
            # search students
            search_sql = """
                SELECT u.id AS user_id,
                       u.name AS name,
                       c.id AS conversation_id,
                       lm.message_text AS last_message,
                       DATE_FORMAT(lm.created_at, '%%h:%%i %%p') AS last_message_time
                FROM users u
                LEFT JOIN conversations c ON c.student_id = u.id AND c.teacher_id = %s
                LEFT JOIN (
                    SELECT m1.conversation_id, m1.message_text, m1.created_at
                    FROM messages m1
                    JOIN (
                        SELECT conversation_id, MAX(created_at) AS max_created
                        FROM messages
                        GROUP BY conversation_id
                    ) m2 ON m1.conversation_id = m2.conversation_id AND m1.created_at = m2.max_created
                ) lm ON lm.conversation_id = c.id
                WHERE u.role = 'student' AND u.id != %s
                  AND (u.name LIKE %s OR EXISTS(
                       SELECT 1 FROM messages mm WHERE mm.conversation_id = c.id AND mm.message_text LIKE %s
                  ))
                ORDER BY lm.created_at DESC
            """
            params = [current_user_id, current_user_id, q_param, q_param]
        else:
            # search teachers
            search_sql = """
                SELECT u.id AS user_id,
                       u.name AS name,
                       c.id AS conversation_id,
                       lm.message_text AS last_message,
                       DATE_FORMAT(lm.created_at, '%%h:%%i %%p') AS last_message_time
                FROM users u
                LEFT JOIN conversations c ON c.teacher_id = u.id AND c.student_id = %s
                LEFT JOIN (
                    SELECT m1.conversation_id, m1.message_text, m1.created_at
                    FROM messages m1
                    JOIN (
                        SELECT conversation_id, MAX(created_at) AS max_created
                        FROM messages
                        GROUP BY conversation_id
                    ) m2 ON m1.conversation_id = m2.conversation_id AND m1.created_at = m2.max_created
                ) lm ON lm.conversation_id = c.id
                WHERE u.role = 'teacher' AND u.id != %s
                  AND (u.name LIKE %s OR EXISTS(
                       SELECT 1 FROM messages mm WHERE mm.conversation_id = c.id AND mm.message_text LIKE %s
                  ))
                ORDER BY lm.created_at DESC
            """
            params = [current_user_id, current_user_id, q_param, q_param]

        results = BaseModel.fetch_all(search_sql, params) or []
        # Normalize keys to simple JSON-friendly structure
        out = []
        for r in results:
            out.append({
                'conversation_id': r.get('conversation_id'),
                'user_id': r.get('user_id'),
                'name': r.get('name'),
                'last_message': r.get('last_message') or '',
                'last_message_time': r.get('last_message_time') or ''
            })
        return jsonify(out)

    def create_or_get_conversation(self, other_user_id):
        """Create or return existing conversation between current user and other_user_id."""
        current_user_id = session.get('user_id')
        user_role = session.get('role')
        if not current_user_id:
            return None

        if user_role == 'teacher':
            teacher_id = current_user_id
            student_id = other_user_id
        else:
            teacher_id = other_user_id
            student_id = current_user_id

        # Check existing
        sel_sql = "SELECT id FROM conversations WHERE student_id = %s AND teacher_id = %s"
        existing = BaseModel.fetch_one(sel_sql, [student_id, teacher_id])
        if existing:
            return existing.get('id')

        # create
        ins_sql = "INSERT INTO conversations (student_id, teacher_id) VALUES (%s, %s)"
        ok = BaseModel.execute_write(ins_sql, [student_id, teacher_id])
        if not ok:
            return None
        # fetch id
        existing = BaseModel.fetch_one(sel_sql, [student_id, teacher_id])
        return existing.get('id') if existing else None

    def http_send_message(self, conversation_id, message_text):
        """Insert a message via HTTP fallback and return payload dict."""
        sender_id = session.get('user_id')
        if not sender_id:
            return None
        insert_sql = """
            INSERT INTO messages (conversation_id, sender_id, message_text)
            VALUES (%s, %s, %s)
        """
        ok = BaseModel.execute_write(insert_sql, [conversation_id, sender_id, message_text])
        if not ok:
            return None
        # return payload similar to socket event
        from datetime import datetime
        return {
            'sender_id': sender_id,
            'sender_name': session.get('username') or session.get('name'),
            'message': message_text,
            'time': datetime.now().strftime('%I:%M %p')
        }