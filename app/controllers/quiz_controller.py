from flask import render_template, request, redirect, url_for, flash, session, jsonify
import os
import json
from dotenv import load_dotenv
from google import genai
from app.database import Database # NEW: Import the database connection

# Load environment variables and initialize Gemini
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

class QuizController:
    def quiz_generator_page(self):
        return render_template('tasks/quiz_generator.html', quiz_data=None)

    def start_quiz_session(self):
        # 1. Initialize the session state
        source_text = request.form.get('source_text', '').strip()
        num_questions = int(request.form.get('num_questions', 3))
        
        # Read the new timer configurations
        enable_timer = request.form.get('enable_timer') == 'true'
        total_seconds = 0
        
        if enable_timer:
            minutes = int(request.form.get('timer_min', 0))
            seconds = int(request.form.get('timer_sec', 30))
            # Convert everything into total seconds for easier JavaScript tracking
            total_seconds = (minutes * 60) + seconds
            
            # Enforce your boundaries (30 seconds to 5 minutes)
            if total_seconds < 30:
                total_seconds = 30
            elif total_seconds > 300:
                total_seconds = 300

        session['quiz_state'] = {
            'source_text': source_text,
            'total_questions': num_questions,
            'generated_questions': [],
            'status': 'generating',
            'time_limit_per_question': total_seconds if enable_timer else None,
            'hide_answers': request.form.get('hide_answers') == 'true'
        }
        return render_template('tasks/quiz_interactive.html')

    def generate_next_question(self):
        state = session.get('quiz_state')
        if not state or len(state['generated_questions']) >= state['total_questions']:
            return jsonify({'status': 'complete'})

        # Generate ONLY the next question index with STRICT JSON rules
        idx = len(state['generated_questions']) + 1
        prompt = f"""
        Create ONLY multiple-choice question #{idx} based on the text below.
        Return ONLY a SINGLE JSON object (do not put it inside an array).
        You MUST use exactly these keys:
        {{
            "id": {idx},
            "question_text": "the actual question here",
            "option_a": "first choice",
            "option_b": "second choice",
            "option_c": "third choice",
            "option_d": "fourth choice",
            "correct_answer": "exact string text of the correct choice"
        }}
        
        Text: {state['source_text']}
        """

        try:
            response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt, config={'response_mime_type': 'application/json'})
            q_data = json.loads(response.text.strip())
            
            # Identify model
            model_name = "Gemini 2.5 Flash" if "2.5" in response.model_version else "Gemini 1.5 Flash"
            
            # Attach model name to the question data
            q_data['model'] = model_name
            
            state['generated_questions'].append(q_data)
            if len(state['generated_questions']) >= state['total_questions']:
                state['status'] = 'complete'
            session['quiz_state'] = state
            
            return jsonify({'status': 'success', 'question': q_data})
        except Exception as e:
            # Check if it's a Rate Limit error (429)
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                print("⚠️ Rate limit hit! Waiting 60 seconds...")
                # Tell the frontend to wait 60 seconds
                return jsonify({'status': 'wait', 'retry_after': 60})
            return jsonify({'status': 'error', 'message': error_str})

    def get_quiz_status(self):
        state = session.get('quiz_state', {})
        return jsonify({
            'count': len(state.get('generated_questions', [])),
            'total': state.get('total_questions'),
            'status': state.get('status'),
            'time_limit': state.get('time_limit_per_question') # Send timer value to UI
        })

    def save_quiz_history(self):
        # 1. Ensure the user is logged in
        user_id = session.get('user_id') or session.get('id') 
        if not user_id:
            return jsonify({'status': 'error', 'message': 'User not logged in'}), 401

        # 2. Grab the data sent from the browser
        data = request.get_json()
        score = data.get('score')
        total_questions = data.get('total')
        time_taken = data.get('timeTaken')
        qa_data = json.dumps(data.get('qaData')) # Convert array to string

        # 3. Save to MySQL Database
        connection = Database.db()
        try:
            with connection.cursor() as cursor:
                sql = """
                    INSERT INTO quiz_history (student_id, score, total_questions, time_taken, qa_data) 
                    VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (user_id, score, total_questions, time_taken, qa_data))
                connection.commit()
        except Exception as e:
            print(f"Database error: {e}")
            return jsonify({'status': 'error', 'message': 'Database error'}), 500
        finally:
            connection.close()

        return jsonify({'status': 'success'})
    
    def get_quiz_history(self):
        user_id = session.get('user_id') or session.get('id')
        if not user_id:
            return jsonify({'status': 'error', 'message': 'Not logged in'}), 401

        connection = Database.db()
        try:
            with connection.cursor() as cursor:
                # Fetch history and format the date beautifully
                sql = """
                    SELECT score, total_questions, time_taken, qa_data, DATE_FORMAT(created_at, '%%b %%d, %%Y at %%h:%%i %%p') as formatted_date
                    FROM quiz_history
                    WHERE student_id = %s
                    ORDER BY created_at DESC
                """
                cursor.execute(sql, (user_id,))
                history_records = cursor.fetchall()

                # Convert the saved JSON text back into a real Python dictionary
                for record in history_records:
                    if isinstance(record['qa_data'], str):
                        record['qa_data'] = json.loads(record['qa_data'])

                return jsonify({'status': 'success', 'history': history_records})
        except Exception as e:
            print(f"Database error: {e}")
            return jsonify({'status': 'error', 'message': 'Failed to fetch history'}), 500
        finally:
            connection.close()