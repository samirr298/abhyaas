from flask import render_template, request, redirect, url_for, flash
import re
import random

class QuizController:
    def quiz_generator_page(self):
        # State 1: Just loads the empty form
        return render_template('tasks/quiz_generator.html', quiz_data=None)

    def generate_quiz(self):
        # 1. Grab the text the student pasted into the form
        source_text = request.form.get('source_text', '').strip()
        
        # 2. VALIDATION (User Story 4): Check if text is < 50 words
        word_count = len(source_text.split())
        if word_count < 50:
            error_msg = f"Please enter more text. You provided {word_count} words, but we need at least 50."
            return render_template('tasks/quiz_generator.html', quiz_data=None, error_msg=error_msg)

        # 3. GENERATION (User Story 2 & 3): Simple Python text parser
        sentences = re.split(r'(?<=[.!?]) +', source_text)
        valid_sentences = [s for s in sentences if len(s.split()) > 7] 
        
        # Grab the requested number, default to 3
        try:
            requested_num = int(request.form.get('num_questions', 3))
        except ValueError:
            requested_num = 3
            
        # Ensure we don't try to generate more questions than sentences
        num_questions = min(requested_num, len(valid_sentences))
        
        if num_questions < 1:
            error_msg = "Please provide text with clearer, distinct sentences to generate a quiz."
            return render_template('tasks/quiz_generator.html', quiz_data=None, error_msg=error_msg)

        quiz_data = []
        
        # Create questions dynamically
        for i in range(num_questions):
            sentence = valid_sentences[i]
            words = sentence.split()
            
            # Find the longest word to use as the "answer"
            target_word = max(words, key=len).strip('.,!?()')
            question_text = sentence.replace(target_word, "________", 1)
            
            # Create a list of our 4 options and shuffle them!
            options = [target_word, "Concept", "Theory", "Application"]
            random.shuffle(options)
            
            quiz_data.append({
                "id": i + 1,
                "question_text": question_text,
                "option_a": options[0], 
                "option_b": options[1],
                "option_c": options[2],
                "option_d": options[3],
                "correct_answer": target_word # Track the actual word
            })

        # 4. State 2: Render the page with the generated questions!
        return render_template('tasks/quiz_generator.html', quiz_data=quiz_data, original_text=source_text)

    def submit_quiz(self):
        # 1. Grab the hidden original text and re-parse it to get the correct answers
        original_text = request.form.get('original_text', '')
        sentences = re.split(r'(?<=[.!?]) +', original_text)
        valid_sentences = [s for s in sentences if len(s.split()) > 7] 
        
        # Grab the number of questions to grade
        try:
            num_questions = int(request.form.get('num_questions', 3))
        except ValueError:
            num_questions = 3
            
        score = 0
        results = []
        
        # 2. Loop through the dynamic number of questions and grade them
        for i in range(num_questions):
            if i < len(valid_sentences):
                # Re-find the target word
                sentence = valid_sentences[i]
                words = sentence.split()
                target_word = max(words, key=len).strip('.,!?()')
                
                # Grab the ACTUAL WORD the user clicked from the form
                user_choice = request.form.get(f'question_{i+1}')
                
                # Check if the word they clicked matches the target word
                is_correct = (user_choice == target_word)
                if is_correct:
                    score += 1
                    
                results.append({
                    "question_num": i + 1,
                    "user_choice": user_choice,
                    "correct_choice": target_word, # The correct choice is now the word itself
                    "is_correct": is_correct,
                    "answer_text": target_word
                })

        # 3. Render State 3 with the final grades!
        return render_template('tasks/quiz_generator.html', results=results, score=score, total=num_questions)