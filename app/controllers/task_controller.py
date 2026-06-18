import os
import time
from datetime import datetime
from flask import request, redirect, url_for, jsonify, flash
from app.controllers.base_controller import BaseController
from app.models.base_model import BaseModel
from app.models.task import Task, TaskBookmark
from app.models.notification import Notification
from app.auth import login_required, role_required
import math
class TaskController(BaseController):

    def task_delete(self, task_id):
        task = BaseModel.fetch_one("SELECT attached_filename FROM tasks WHERE id = %s LIMIT 1", [task_id])

        if not task:
            return jsonify({"success": False, "message": "Task not found"}), 404

        BaseModel.execute_write("DELETE FROM feedback WHERE task_id = %s", [task_id])
        BaseModel.execute_write("DELETE FROM submissions WHERE task_id = %s", [task_id])
        BaseModel.execute_write("DELETE FROM tasks WHERE id = %s", [task_id])

        attached_filename = task.get('attached_filename')
        if attached_filename:
            file_path = os.path.join('app', 'static', 'uploads', attached_filename)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                        # Failed to remove file during cleanup; debug print removed
                        pass

        return redirect(url_for('tasks.teacher_task'))

    def teacher_task(self):
        # ========================================================
        # handle form submissions (post)
        # ========================================================
        if request.method == 'POST':
            method = request.form.get('action')
            current_teacher_id = self.session.get('user_id')
            
            # --- ACTION A: CREATE A NEW TASK ---
            if method == 'create_task':
                task_title = request.form.get('title')
                subject = request.form.get('subject')
                due_date = request.form.get('deadline')
                description = request.form.get('description')
                
                attached_file = request.files.get('file')
                filename = None 

                if attached_file and attached_file.filename != '':
                    file_extension = os.path.splitext(attached_file.filename)[1].lower()
                    upload_folder = os.path.join('app', 'static', 'uploads')
                    
                    if not os.path.exists(upload_folder):
                        os.makedirs(upload_folder)
                    
                    filename = f"task_{current_teacher_id}_{int(time.time())}{file_extension}"
                    destination_path = os.path.join(upload_folder, filename)
                    
                    try:
                        attached_file.save(destination_path)
                    except Exception as e:
                        # File save error logged earlier during development; removed debug print
                        pass

                # Insert the fresh assignment details into the main ledger
                task_id = Task.create_task(
                    task_title,
                    description,
                    current_teacher_id,
                    due_date,
                    filename,
                    subject,
                )
                if task_id:
                    Notification.create_task_notifications(task_id, task_title, subject)
                    return redirect(url_for('tasks.teacher_task'))

            # --- ACTION B: SAVE STUDENT FEEDBACK SECURELY (ONCE PER TASK) ---
            elif method == "save_feedback":
                combined_student_data = request.form.get("student_data")  # Format: "task_id:student_id"
                feedback_text = (request.form.get("feedback") or "").strip()
                
                if combined_student_data and feedback_text:
                    # split the string identifiers
                    task_id, student_id = combined_student_data.split(":")

                    # security check: verify task belongs to logged-in teacher
                    security_check_sql = """
                        SELECT 1 
                        FROM submissions s
                        JOIN tasks t ON s.task_id = t.id
                        WHERE s.student_id = %s 
                          AND s.task_id = %s 
                          AND t.created_by = %s
                        LIMIT 1
                    """
                    is_valid_submission = BaseModel.fetch_one(security_check_sql, [int(student_id), int(task_id), current_teacher_id])
            
                    if is_valid_submission:
                        # duplicate guard: ensure feedback doesn't already exist
                        dup_sql = "SELECT id FROM feedback WHERE student_id = %s AND task_id = %s LIMIT 1"
                        exists = BaseModel.fetch_one(dup_sql, [int(student_id), int(task_id)])
                        
                        if not exists:
                            # Step A: Log feedback securely
                            insert_feedback_sql = """
                                INSERT INTO feedback (student_id, teacher_id, task_id, feedback_text) 
                                VALUES (%s, %s, %s, %s)
                            """
                            BaseModel.execute_write(insert_feedback_sql, [int(student_id), current_teacher_id, int(task_id), feedback_text])
                    
                            # Step B: Advance the specific submission row status to 'Reviewed'
                            update_status_sql = """
                                UPDATE submissions 
                                SET status = 'Reviewed' 
                                WHERE task_id = %s AND student_id = %s
                            """
                            BaseModel.execute_write(update_status_sql, [int(task_id), int(student_id)])
                        else:
                            # Duplicate feedback attempt; no action needed beyond guard
                            pass
                    else:
                        # Unauthorized attempt blocked; debug print removed
                        pass

                return redirect(url_for('tasks.teacher_task'))
                
        # ========================================================
        # render task interface feed (get)
        # ========================================================
        teacher_id = self.session.get('user_id')
        
        # Pull all active assignments created by this teacher account
        all_tasks = Task.get_teacher_tasks(teacher_id)
        
        # Pull all student submissions (both reviewed and pending, sorted cleanly)
        fetch_submissions_sql = """
            SELECT 
                s.task_id,
                s.student_id,
                s.status,
                t.title AS task_title, 
                s.submitted_filename,
                u.name AS student_name 
            FROM submissions s 
            JOIN tasks t ON s.task_id = t.id 
            JOIN users u ON s.student_id = u.id 
            WHERE t.created_by = %s
            ORDER BY s.status ASC, t.created_at DESC
        """
        all_submissions = BaseModel.fetch_all(fetch_submissions_sql, [teacher_id]) or []
        
        return self.render(
            'tasks/teacher_task.html', 
            tasks=all_tasks, 
            totalsubmissions=all_submissions,
            now=datetime.now()
        )
        

    def student_task(self):
        
        if request.method == 'POST':
            method = request.form.get('action')
            
            if method == 'submit_assignment':
                task_id = request.form.get('task_id')
                student_id = str(self.session.get('user_id'))
                student_file = request.files.get('student_file')
                
                
                if student_file and student_file.filename != '':
                    file_extension = os.path.splitext(student_file.filename)[1].lower()
                    upload_folder = os.path.join('app', 'static', 'student_uploads')
                    
                    if not os.path.exists(upload_folder):
                        os.makedirs(upload_folder)
                    
                    filename = f"sub_{task_id}_{student_id}_{int(time.time())}{file_extension}"
                    destination_path = os.path.join(upload_folder, filename)
                    
                    try:
                        # 1. Check if an old submission already exists in the database
                        check_existing_sql = "SELECT submitted_filename FROM submissions WHERE task_id = %s AND student_id = %s"
                        existing_submission = BaseModel.fetch_one(check_existing_sql, [task_id, int(student_id)])

                        # 2. If it exists, delete the physical old file from the server folder
                        if existing_submission and existing_submission.get('submitted_filename'):
                            old_file_path = os.path.join(upload_folder, existing_submission['submitted_filename'])
                            if os.path.exists(old_file_path):
                                os.remove(old_file_path)

                        # 3. Save the newly uploaded file to the folder
                        student_file.save(destination_path)
                        
                        # Sync tracking string array inside main tasks reference ledger
                        fetch_task_sql = "SELECT completed_by_students FROM tasks WHERE id = %s"
                        task_data = BaseModel.fetch_one(fetch_task_sql, [task_id])
                        
                        current_list = task_data['completed_by_students'] or ''
                        existing_ids = current_list.split(',') if current_list else []
                        
                        if student_id not in existing_ids:
                            existing_ids.append(student_id)
                            new_list_string = ",".join(existing_ids)
                            
                            update_task_sql = "UPDATE tasks SET completed_by_students = %s WHERE id = %s"
                            BaseModel.execute_write(update_task_sql, [new_list_string, task_id])
                        
                        # 4. DATABASE SYNC (INSERT vs UPDATE)
                        if existing_submission:
                            # If it's a reupload, UPDATE the file name and reset status to 'Pending'
                            update_sub_sql = """
                                UPDATE submissions 
                                SET submitted_filename = %s, status = 'Pending' 
                                WHERE task_id = %s AND student_id = %s
                            """
                            BaseModel.execute_write(update_sub_sql, [filename, task_id, int(student_id)])
                        else:
                            # If it's the first time, INSERT a fresh row
                            insert_sub_sql = """
                                INSERT INTO submissions (task_id, student_id, submitted_filename, status) 
                                VALUES (%s, %s, %s, 'Pending')
                            """
                            BaseModel.execute_write(insert_sub_sql, [task_id, int(student_id), filename])
                            
                    except Exception as e:
                        # Error handling for file operations; debug print removed
                        pass
                        
                return redirect(url_for('tasks.student_task'))

        # ========================================================
        # render task feed (get)
        # ========================================================
        current_student_id = self.session.get('user_id')
        bookmarked_task_ids = TaskBookmark.get_bookmarked_task_ids(current_student_id)
        
        # Pull all global classroom assignments
        fetch_all_tasks_sql = "SELECT * FROM tasks ORDER BY due_date ASC"
        all_tasks = BaseModel.fetch_all(fetch_all_tasks_sql) or []
        
        # Pull this student's submission logs with granular statuses
        fetch_status_sql = "SELECT task_id, status FROM submissions WHERE student_id = %s"
        student_submissions = BaseModel.fetch_all(fetch_status_sql, [current_student_id]) or []

        # Map: task_id -> status for quick lookup
        submission_map = {int(sub['task_id']): sub['status'] for sub in student_submissions}

        # Compute summary counts
        total_tasks_count = len(all_tasks)
        completion_count = sum(1 for status in submission_map.values() if status == 'Reviewed')

        today = datetime.now()
        over_due = 0
        for task in all_tasks:
            tid = int(task['id'])
            # count as overdue only if due_date passed and not reviewed
            if task['due_date'] < today and submission_map.get(tid) != 'Reviewed':
                over_due += 1

        remaining = total_tasks_count - completion_count - over_due
        if remaining < 0:
            remaining = 0

        # Incomplete = all tasks minus completed
        incomplete_count = total_tasks_count - completion_count
        if incomplete_count < 0:
            incomplete_count = 0
        
        try:
            score = completion_count/total_tasks_count
            score = score * 100
        except:
            score = 0
        # Convert to float first if it's currently a string
        score = float(score) 

# Format to 2 decimal places
        score = f"{score:.2f}"  # If score was 85, it cleanly becomes "85.00"
        return self.render(
            'tasks/student_task.html', 
            tasks=all_tasks, 
            student_id=str(current_student_id),
            bookmarked_task_ids=bookmarked_task_ids,
            submission_map=submission_map,
            total_tasks_count=total_tasks_count,
            completion_count=completion_count,
            incomplete_count=incomplete_count,
            non_completion_count=remaining,
            over_due=over_due,
            now=datetime.now(),
            score =score
            
        )

    def view_task(self, task_id):
        """Student-facing single task view. Allows viewing full details and submitting a file."""
        current_student_id = self.session.get('user_id')

        # Handle submission POST from this page
        if request.method == 'POST':
            method = request.form.get('action')
            if method == 'submit_assignment':
                student_id = str(current_student_id)
                student_file = request.files.get('student_file')

                if student_file and student_file.filename != '':
                    file_extension = os.path.splitext(student_file.filename)[1].lower()
                    upload_folder = os.path.join('app', 'static', 'student_uploads')
                    if not os.path.exists(upload_folder):
                        os.makedirs(upload_folder)

                    filename = f"sub_{task_id}_{student_id}_{int(time.time())}{file_extension}"
                    destination_path = os.path.join(upload_folder, filename)

                    try:
                        student_file.save(destination_path)

                        # Update tasks.completed_by_students tracking
                        fetch_task_sql = "SELECT completed_by_students FROM tasks WHERE id = %s"
                        task_data = BaseModel.fetch_one(fetch_task_sql, [task_id])

                        current_list = task_data['completed_by_students'] or ''
                        existing_ids = current_list.split(',') if current_list else []

                        if student_id not in existing_ids:
                            existing_ids.append(student_id)
                            new_list_string = ",".join(existing_ids)
                            update_task_sql = "UPDATE tasks SET completed_by_students = %s WHERE id = %s"
                            BaseModel.execute_write(update_task_sql, [new_list_string, task_id])

                        insert_sub_sql = """
                            INSERT INTO submissions (task_id, student_id, submitted_filename, status) 
                            VALUES (%s, %s, %s, 'Pending')
                        """
                        BaseModel.execute_write(insert_sub_sql, [task_id, int(student_id), filename])

                    except Exception as e:
                        # Debug print removed
                        pass

        # mark notification read when student arrives from a notification link
        notification_id = request.args.get('notification_id')
        if notification_id:
            Notification.mark_as_read(notification_id, current_student_id)

        # GET: render task details
        fetch_task_sql = "SELECT * FROM tasks WHERE id = %s LIMIT 1"
        task = BaseModel.fetch_one(fetch_task_sql, [task_id])

        # student's submission for this task (if any)
        fetch_sub_sql = "SELECT * FROM submissions WHERE task_id = %s AND student_id = %s LIMIT 1"
        student_sub = BaseModel.fetch_one(fetch_sub_sql, [task_id, current_student_id]) or None

        # any feedback for this student and task
        fetch_feedback_sql = "SELECT * FROM feedback WHERE task_id = %s AND student_id = %s ORDER BY created_at DESC"
        feedback_items = BaseModel.fetch_all(fetch_feedback_sql, [task_id, current_student_id]) or []

        return self.render(
            'tasks/task_detail.html',
            task=task,
            submission=student_sub,
            feedback=feedback_items,
            is_bookmarked=TaskBookmark.is_bookmarked(current_student_id, task_id),
            now=datetime.now()
        )

    @login_required
    @role_required('student')
    def toggle_bookmark(self, task_id):
        task = BaseModel.fetch_one("SELECT id FROM tasks WHERE id = %s LIMIT 1", [task_id])
        if not task:
            return jsonify({"success": False, "message": "Task not found"}), 404

        current_student_id = self.session.get('user_id')
        is_bookmarked = TaskBookmark.toggle(current_student_id, task_id)

        message = 'Task bookmarked.' if is_bookmarked else 'Bookmark removed.'
        flash(message, 'success')

        referrer = request.referrer or url_for('tasks.student_task')
        return redirect(referrer)

    @login_required
    @role_required('student')
    def bookmarks(self):
        current_student_id = self.session.get('user_id')
        bookmarks = TaskBookmark.get_bookmarks_for_user(current_student_id)
        bookmarked_task_ids = {int(item['id']) for item in bookmarks if item.get('id') is not None}

        return self.render(
            'tasks/bookmarks.html',
            bookmarks=bookmarks,
            bookmarked_task_ids=bookmarked_task_ids,
            now=datetime.now(),
        )

    def notifications(self):
        user_id = self.session.get('user_id')
        notifications = Notification.get_for_user(user_id)
        return self.render('users/notifications.html', notifications=notifications)

    def mark_all_notifications(self):
        user_id = self.session.get('user_id')
        Notification.mark_all_read(user_id)
        return redirect(url_for('tasks.notifications'))
