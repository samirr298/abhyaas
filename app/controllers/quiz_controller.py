from flask import render_template, request, redirect, url_for, flash
import os
import json
from dotenv import load_dotenv
from google import genai

# Load environment variables and initialize Gemini
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

class QuizController:
    def quiz_generator_page(self):
        # State 1: Just loads the empty form
        return render_template('tasks/quiz_generator.html', quiz_data=None)

    def generate_quiz(self):
        source_text = request.form.get('source_text', '').strip()
        
        # Validation: Check if text is < 50 words
        word_count = len(source_text.split())
        if word_count < 50:
            error_msg = f"Please enter more text. You provided {word_count} words, but we need at least 50."
            return render_template('tasks/quiz_generator.html', quiz_data=None, error_msg=error_msg)

        try:
            requested_num = int(request.form.get('num_questions', 3))
        except ValueError:
            requested_num = 3

        # Craft the prompt telling Gemini to act as a strict examiner returning JSON
        prompt = f"""
        You are an expert educator. Create a multiple-choice practice quiz based strictly on the following study material.
        
        CRITICAL RULES:
        1. Do NOT just copy and paste direct sentences. Rephrase the concepts creatively into clear, challenging questions.
        2. Generate exactly {requested_num} questions.
        3. Return the response as a valid JSON array of objects. Do not wrap it in markdown code blocks like ```json.
        
        Each object in the array MUST have exactly these keys:
        - "id": a number starting from 1
        - "question_text": the rephrased question string
        - "option_a": first choice
        - "option_b": second choice
        - "option_c": third choice
        - "option_d": fourth choice
        - "correct_answer": the exact string text of the correct option
        
        Study Material:
        {source_text}
        """

        try:
            # First attempt: Try the newest 2.5 Flash model
            try:
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                    config={'response_mime_type': 'application/json'}
                )
            except Exception as e_25:
                # If 2.5 fails (likely due to traffic), automatically fallback to 1.5 Flash
                print(f"⚠️ 2.5 Flash busy ({e_25}). Falling back to 1.5 Flash...")
                response = client.models.generate_content(
                    model='gemini-1.5-flash',
                    contents=prompt,
                    config={'response_mime_type': 'application/json'}
                )
            
            # Clean up and parse the JSON payload from the AI
            clean_json_str = response.text.strip().lstrip('```json').rstrip('```').strip()
            quiz_data = json.loads(clean_json_str)
            
            # Determine which model succeeded based on the response model attribute
            model_used = "Gemini 2.5 Flash" if "2.5" in response.model_version else "Gemini 1.5 Flash"
            
            return render_template('tasks/quiz_generator.html', 
                                   quiz_data=quiz_data, 
                                   original_text=source_text,
                                   generated_by=model_used)
            
        except Exception as e:
            # If BOTH models fail, show a professional, user-friendly error
            error_msg = "Our AI servers are currently experiencing unusually high traffic. Please wait a few seconds and try generating your quiz again!"
            
            # Keep the real error in the terminal so you can still debug it
            print(f"❌ Total AI Failure: {str(e)}") 
            
            return render_template('tasks/quiz_generator.html', quiz_data=None, error_msg=error_msg)

    def submit_quiz(self):
        try:
            num_questions = int(request.form.get('num_questions', 3))
        except ValueError:
            num_questions = 3
            
        score = 0
        results = []
        
        # Grade the questions dynamically from the hidden form data
        for i in range(num_questions):
            question_num = i + 1
            user_choice = request.form.get(f'question_{question_num}')
            correct_answer = request.form.get(f'correct_answer_{question_num}')
            
            is_correct = (user_choice == correct_answer)
            if is_correct:
                score += 1
                
            results.append({
                "question_num": question_num,
                "user_choice": user_choice,
                "correct_choice": correct_answer,
                "is_correct": is_correct,
                "answer_text": correct_answer
            })

        return render_template('tasks/quiz_generator.html', results=results, score=score, total=num_questions)