from flask import render_template, request, redirect, url_for, flash
import re

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
        # We split the text into sentences
        sentences = re.split(r'(?<=[.!?]) +', source_text)
        valid_sentences = [s for s in sentences if len(s.split()) > 7] 
        
        # If the text is weird and doesn't have 3 good sentences
        if len(valid_sentences) < 3:
            error_msg = "Please provide text with clearer, distinct sentences to generate a quiz."
            return render_template('tasks/quiz_generator.html', quiz_data=None, error_msg=error_msg)

        quiz_data = []
        
        # Create 3 questions by blanking out the longest word in a sentence
        for i in range(3):
            sentence = valid_sentences[i]
            words = sentence.split()
            
            # Find the longest word to use as the "answer"
            target_word = max(words, key=len).strip('.,!?()')
            question_text = sentence.replace(target_word, "________", 1)
            
            # You can upgrade this later to shuffle answers or use an AI library!
            quiz_data.append({
                "id": i + 1,
                "question_text": question_text,
                "option_a": target_word, 
                "option_b": "Concept",
                "option_c": "Theory",
                "option_d": "Application",
                "correct_answer": "A"
            })

        # 4. State 2: Render the page with the generated questions!
        return render_template('tasks/quiz_generator.html', quiz_data=quiz_data, original_text=source_text)

    def submit_quiz(self):
        # 1. Grab the hidden original text and re-parse it to get the correct answers
        original_text = request.form.get('original_text', '')
        sentences = re.split(r'(?<=[.!?]) +', original_text)
        valid_sentences = [s for s in sentences if len(s.split()) > 7] 
        
        score = 0
        results = []
        
        # 2. Loop through the 3 questions and grade them
        for i in range(3):
            if i < len(valid_sentences):
                # Re-find the target word
                sentence = valid_sentences[i]
                words = sentence.split()
                target_word = max(words, key=len).strip('.,!?()')
                
                # In our generator, Option A was always the correct one
                correct_choice = "A"
                
                # Grab what radio button the user clicked (e.g., 'question_1')
                user_choice = request.form.get(f'question_{i+1}')
                
                is_correct = (user_choice == correct_choice)
                if is_correct:
                    score += 1
                    
                results.append({
                    "question_num": i + 1,
                    "user_choice": user_choice,
                    "correct_choice": correct_choice,
                    "is_correct": is_correct,
                    "answer_text": target_word
                })

        # 3. Render State 3 with the final grades!
        return render_template('tasks/quiz_generator.html', results=results, score=score, total=3)