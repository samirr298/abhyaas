from flask import render_template, request, redirect, url_for, flash, session, jsonify
import os
import json
from dotenv import load_dotenv
from google import genai

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
        
        session['quiz_state'] = {
            'source_text': source_text,
            'total_questions': num_questions,
            'generated_questions': [],
            'status': 'generating'
        }
        return render_template('tasks/quiz_interactive.html')

    def generate_next_question(self):
        state = session.get('quiz_state')
        if not state or len(state['generated_questions']) >= state['total_questions']:
            return jsonify({'status': 'complete'})

        idx = len(state['generated_questions']) + 1
        prompt = f"Create ONLY question #{idx} based on this text: {state['source_text']}. Return valid JSON."

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
            'status': state.get('status')
        })