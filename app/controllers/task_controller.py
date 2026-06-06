import os
from datetime import datetime
from uuid import uuid4

from flask import flash, redirect, render_template, request, session, url_for
from werkzeug.utils import secure_filename

from app.models.task import Task, TaskSubmission


class TaskController:
    def __init__(self):
        self.session = session

    def _save_upload(self):
        uploaded_file = request.files.get('submission_file')
        if not uploaded_file or not uploaded_file.filename:
            return None

        upload_folder = os.path.join(os.getcwd(), 'app', 'static', 'uploads')
        os.makedirs(upload_folder, exist_ok=True)

        filename = secure_filename(uploaded_file.filename)
        unique_filename = f"{uuid4().hex}_{filename}"
        uploaded_file.save(os.path.join(upload_folder, unique_filename))
        return f"uploads/{unique_filename}"

    def _format_datetime(self, value):
        if not value:
            return '—'
        if isinstance(value, str):
            return value
        if hasattr(value, 'strftime'):
            return value.strftime('%b %d, %Y')
        return str(value)

    def teacher_dashboard(self):
        teacher_id = self.session.get('user_id')

        if request.method == 'POST':
            action = request.form.get('action')

            if action == 'create_task':
                title = request.form.get('title', '').strip()
                deadline = request.form.get('deadline', '').strip()

                if not title or not deadline:
                    flash('Task title and deadline are required.', 'error')
                    return redirect(url_for('auth.teacher'))

                Task.create_task(
                    teacher_id,
                    title,
                    request.form.get('description', '').strip(),
                    request.form.get('subject', '').strip(),
                    deadline,
                )
                flash('Task created successfully and published to students.', 'success')
                return redirect(url_for('auth.teacher'))

            if action == 'save_feedback':
                submission_id = request.form.get('submission_id')
                feedback = request.form.get('teacher_feedback', '').strip()

                if not submission_id or not feedback:
                    flash('Please add feedback before saving.', 'error')
                    return redirect(url_for('auth.teacher'))

                TaskSubmission.save_feedback(submission_id, feedback)
                flash('Feedback saved successfully.', 'success')
                return redirect(url_for('auth.teacher'))

        teacher_tasks = Task.get_teacher_tasks(teacher_id)
        task_lookup = {task['id']: task for task in teacher_tasks}
        task_submissions = []

        for task in teacher_tasks:
            submissions = TaskSubmission.get_submissions_for_task(task['id']) or []
            for submission in submissions:
                submission['task_title'] = task['title']
            task_submissions.extend(submissions)

        total_submissions = sum(int(task.get('submitted_count') or 0) for task in teacher_tasks)
        total_pending = sum(int(task.get('pending_count') or 0) for task in teacher_tasks)
        completion_rate = round((total_submissions / (total_submissions + total_pending)) * 100) if (total_submissions + total_pending) else 0

        class_summary = {
            'submitted': total_submissions,
            'pending': total_pending,
            'average_completion': f"{completion_rate}%",
        }

        tasks = []
        for task in teacher_tasks:
            tasks.append({
                'subject': task['subject'],
                'title': task['title'],
                'status': 'Live',
                'due': task['deadline'],
                'posted': self._format_datetime(task.get('created_at')),
                'submissions': int(task.get('submitted_count') or 0),
            })

        feedback_queue = []
        for submission in task_submissions:
            feedback_queue.append({
                'student': submission['student_name'],
                'task': submission['task_title'],
                'status': 'Reviewed' if submission.get('teacher_feedback') else 'Needs review',
                'note': submission.get('teacher_feedback') or (submission.get('submission_text') or 'No feedback yet.'),
            })

        submissions = []
        for submission in task_submissions:
            submissions.append({
                'name': submission['student_name'],
                'roll': submission.get('email') or submission['student_id'],
                'submission_text': submission.get('submission_text') or '',
                'submission_file_path': submission.get('submission_file_path'),
                'status': 'Submitted' if submission['status'] == 'submitted' else 'Pending',
                'time': self._format_datetime(submission.get('submitted_at')),
            })

        return render_template(
            'tasks/teacher_task.html',
            class_summary=class_summary,
            tasks=tasks,
            feedback_queue=feedback_queue,
            submissions=submissions,
            teacher_tasks=teacher_tasks,
            task_submissions=task_submissions,
            total_submissions=total_submissions,
            username=self.session.get('username'),
        )

    def student_dashboard(self):
        student_id = self.session.get('user_id')

        if request.method == 'POST':
            task_id = request.form.get('task_id')
            task = Task.get_task(task_id)

            if not task:
                flash('Task not found.', 'error')
                return redirect(url_for('auth.student'))

            if task['deadline'] < datetime.now().date():
                flash('The deadline has passed, so submission is no longer allowed.', 'error')
                return redirect(url_for('auth.student'))

            submission_text = request.form.get('submission_text', '').strip()
            submission_link = request.form.get('submission_link', '').strip()
            if submission_link:
                link_text = f"Submission link: {submission_link}"
                if submission_text:
                    submission_text = f"{submission_text}\n\n{link_text}"
                else:
                    submission_text = link_text

            submission_file_path = self._save_upload()

            if not submission_text and not submission_file_path:
                flash('Please upload a file, paste a link, or type a response before submitting.', 'error')
                return redirect(url_for('auth.student'))

            existing_submission = TaskSubmission.get_submission_for_task(task_id, student_id)
            if existing_submission:
                preserve_file_path = submission_file_path or existing_submission['submission_file_path']
                TaskSubmission.update_submission(existing_submission['id'], submission_text, preserve_file_path)
                flash('Your submission has been updated successfully.', 'success')
            else:
                TaskSubmission.create_submission(task_id, student_id, submission_text, submission_file_path)
                flash('Submission successful. Your work has been recorded.', 'success')

            return redirect(url_for('auth.student'))

        today_tasks = Task.get_today_tasks(student_id)

        # normalize and annotate tasks: compute overdue status
        normalized_today_tasks = []
        for task in (today_tasks or []):
            # task['deadline'] may be a date or string; try to compare safely
            is_overdue = False
            try:
                deadline_val = task.get('deadline')
                if hasattr(deadline_val, 'strftime'):
                    deadline_date = deadline_val
                else:
                    # try parsing YYYY-MM-DD
                    from datetime import datetime as _dt

                    try:
                        deadline_date = _dt.strptime(str(deadline_val), '%Y-%m-%d').date()
                    except Exception:
                        deadline_date = None

                if deadline_date and task.get('submission_status') != 'submitted':
                    from datetime import date as _date

                    if deadline_date < _date.today():
                        is_overdue = True
            except Exception:
                is_overdue = False

            task['is_overdue'] = is_overdue
            normalized_today_tasks.append(task)

        today_tasks = normalized_today_tasks

        completed_count = sum(1 for task in today_tasks if task.get('submission_status') == 'submitted')
        pending_count = len(today_tasks) - completed_count
        due_soon_count = sum(1 for task in today_tasks if task.get('submission_status') != 'submitted')

        overview = {
            'completed': completed_count,
            'pending': pending_count,
            'average_score': '—',
            'due_soon': due_soon_count,
        }

        tasks = []
        for task in today_tasks:
            tasks.append({
                'id': task['id'],
                'subject': task['subject'],
                'title': task['title'],
                'description': task['description'] or 'No description added yet.',
                'status': 'Submitted' if task.get('submission_status') == 'submitted' else 'Pending',
                'due': task['deadline'],
                'priority': 'High' if task.get('submission_status') != 'submitted' else 'Medium',
                'progress': 100 if task.get('submission_status') == 'submitted' else 40,
                'score': 'Reviewed' if task.get('teacher_feedback') else 'Pending',
            })

        feedback = []
        for task in today_tasks:
            if task.get('teacher_feedback'):
                feedback.append({
                    'title': task['title'],
                    'time': self._format_datetime(task.get('submitted_at')),
                    'message': task['teacher_feedback'],
                })

        return render_template(
            'tasks/student_task.html',
            overview=overview,
            tasks=tasks,
            feedback=feedback,
            today_tasks=today_tasks,
            username=self.session.get('username'),
        )

    def view_task(self, task_id):
        """Render a simple task detail page. No JavaScript required."""
        user_id = self.session.get('user_id')
        task = Task.get_task(task_id)
        if not task:
            from flask import abort

            return render_template('errors/404.html'), 404

        submission = None
        try:
            submission = TaskSubmission.get_submission_for_task(task_id, user_id)
        except Exception:
            submission = None

        return render_template(
            'tasks/task_detail.html',
            task=task,
            submission=submission,
            username=self.session.get('username'),
        )
