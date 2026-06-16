from flask import render_template, request, redirect, url_for, flash

class QuizController:
    def quiz_generator_page(self):
        return render_template('tasks/quiz_generator.html', quiz_data=None)

    def generate_quiz(self):
        pass

    def submit_quiz(self):
        pass