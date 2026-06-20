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
        return render_template('quiz/quiz_generator.html', quiz_data=None)
    
    def quiz_history_page(self):
        # Optional: Ensure user is logged in before showing the page
        user_id = session.get('user_id') or session.get('id')
        if not user_id:
            # Adjust this redirect to match your actual login route name if needed
            return redirect(url_for('login')) 
            
        return render_template('quiz/quiz_history.html')

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
        return render_template('quiz/quiz_interactive.html')

    def generate_next_question(self):
        state = session.get('quiz_state')
        if not state:
            return jsonify({'status': 'error', 'message': 'No active session'})

        # BUGFIX 1: If questions are already generated (like after a page refresh), 
        # send the whole batch back to the frontend instead of just saying "complete"!
        if len(state['generated_questions']) >= state['total_questions']:
            return jsonify({'status': 'success_batch', 'questions': state['generated_questions']})

        num_needed = state['total_questions'] - len(state['generated_questions'])
        
        # Ask for an ARRAY of all questions in a single API call
        prompt = f"""
        Create exactly {num_needed} multiple-choice questions based on the text below.
        Return ONLY a raw JSON array containing the question objects. Do NOT wrap it in Markdown (```json).
        Each object MUST use exactly these keys:
        {{
            "id": 1,
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
            response = client.models.generate_content(
                model='gemini-2.5-flash', 
                contents=prompt, 
                config={'response_mime_type': 'application/json'}
            )
            
            # BUGFIX 2: Strip Markdown formatting just in case Gemini gets stubborn
            raw_text = response.text.strip()
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
                
            q_list = json.loads(raw_text.strip())
            
            # Failsafe: if the AI ignored instructions and returned a single object
            if isinstance(q_list, dict):
                q_list = [q_list]
                
            model_name = "Gemini 2.5 Flash" if "2.5" in response.model_version else "Gemini 1.5 Flash"
            
            for q in q_list:
                q['model'] = model_name
                state['generated_questions'].append(q)
                
            state['status'] = 'complete'
            session['quiz_state'] = state
            
            # Return the entire array to the frontend in one shot
            return jsonify({'status': 'success_batch', 'questions': q_list})
        except Exception as e:
            error_str = str(e)
            print("\n" + "="*30)
            print(f"🚨 SECRET AI ERROR: {error_str}")
            print("="*30 + "\n")
            
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
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
            print("🚨 ERROR: User ID not found in session! Cannot save quiz.")
            return jsonify({'status': 'error', 'message': 'User not logged in'}), 401

        # 2. Grab the data sent from the browser
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({'status': 'error', 'message': 'No data received'}), 400
            
        score = data.get('score')
        total_questions = data.get('total')
        time_taken = data.get('timeTaken')
        qa_data = json.dumps(data.get('qaData'))

        # 🚨 THE FIX: Force the database to create the table if it's missing!
        Database.create_quiz_history_table()

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
                print("✅ SUCCESS: Quiz saved to database!")
        except Exception as e:
            print(f"🚨 DATABASE ERROR: {e}")
            return jsonify({'status': 'error', 'message': 'Database error'}), 500
        finally:
            connection.close()

        return jsonify({'status': 'success'})
    
    def get_quiz_history(self):
        user_id = session.get('user_id') or session.get('id')
        if not user_id:
            return jsonify({'status': 'error', 'message': 'Not logged in'}), 401

        # 🚨 THE FIX: Force the database to create the table if it's missing!
        Database.create_quiz_history_table()

        connection = Database.db()
        try:
            with connection.cursor() as cursor:
                sql = """
                    SELECT id, title, score, total_questions, time_taken, qa_data, DATE_FORMAT(created_at, '%%b %%d, %%Y at %%h:%%i %%p') as formatted_date
                    FROM quiz_history
                    WHERE student_id = %s
                    ORDER BY created_at DESC
                """
                cursor.execute(sql, (user_id,))
                history_records = cursor.fetchall()

                for record in history_records:
                    if isinstance(record['qa_data'], str):
                        record['qa_data'] = json.loads(record['qa_data'])

                return jsonify({'status': 'success', 'history': history_records})
        except Exception as e:
            print(f"🚨 DATABASE FETCH ERROR: {e}")
            return jsonify({'status': 'error', 'message': 'Failed to fetch history'}), 500
        finally:
            connection.close()

    def update_quiz_title(self):
        user_id = session.get('user_id') or session.get('id')
        data = request.get_json(force=True, silent=True)
        quiz_id = data.get('quiz_id')
        title = data.get('title')

        connection = Database.db()
        try:
            with connection.cursor() as cursor:
                # Update the title, but ONLY if the quiz belongs to the logged-in user (Security!)
                cursor.execute("UPDATE quiz_history SET title = %s WHERE id = %s AND student_id = %s", (title, quiz_id, user_id))
                connection.commit()
            return jsonify({'status': 'success'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
        finally:
            connection.close()

    def delete_quiz(self):
        user_id = session.get('user_id') or session.get('id')
        data = request.get_json(force=True, silent=True)
        quiz_id = data.get('quiz_id')

        connection = Database.db()
        try:
            with connection.cursor() as cursor:
                # Delete the quiz, ensuring it belongs to the user
                cursor.execute("DELETE FROM quiz_history WHERE id = %s AND student_id = %s", (quiz_id, user_id))
                connection.commit()
            return jsonify({'status': 'success'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
        finally:
            connection.close()