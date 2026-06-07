import os
import time
from datetime import datetime
from flask import request, redirect, url_for, jsonify
from app.controllers.base_controller import BaseController
from app.models.base_model import BaseModel
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
                    print(f"Failed to remove task file {attached_filename}: {e}")

        return redirect(url_for('tasks.teacher_task'))

    def teacher_task(self):
        # ========================================================
        # 1️⃣ HANDLE FORM SUBMISSIONS (POST)
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
                        print(f"File save error: {e}")

                # Insert the fresh assignment details into the main ledger
                sql = """
                    INSERT INTO tasks (title, description, created_by, due_date, completed_by_students, attached_filename, subject) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                status = BaseModel.execute_write(sql, [task_title, description, current_teacher_id, due_date, '', filename, subject])
                
                if status:
                    return redirect(url_for('tasks.teacher_task'))

            # --- ACTION B: SAVE STUDENT FEEDBACK SECURELY (ONCE PER TASK) ---
            elif method == "save_feedback":
                combined_student_data = request.form.get("student_data")  # Format: "task_id:student_id"
                feedback_text = (request.form.get("feedback") or "").strip()
                
                if combined_student_data and feedback_text:
                    # ✂️ Split the string identifiers FIRST 
                    task_id, student_id = combined_student_data.split(":")
                    
                    # 🛡️ Security Check: Verify this task belongs to the logged-in teacher
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
                        # 🛑 Duplicate Guard Check: Ensure feedback doesn't already exist
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
                            print(f"🚀 Feedback saved securely for Student {student_id}!")
                        else:
                            print("🛑 Double submission blocked. Feedback already exists.")
                    else:
                        print("⚠️ Security Alert: Unauthorized attempt blocked.")

                return redirect(url_for('tasks.teacher_task'))
                
        # ========================================================
        # 2️⃣ RENDER task INTERFACE FEED (GET)
        # ========================================================
        teacher_id = self.session.get('user_id')
        
        # Pull all active assignments created by this teacher account
        fetch_tasks_sql = "SELECT * FROM tasks WHERE created_by = %s ORDER BY created_at DESC"
        all_tasks = BaseModel.fetch_all(fetch_tasks_sql, [teacher_id]) or []
        
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
                            print("Submission successfully updated (Reuploaded).")
                        else:
                            # If it's the first time, INSERT a fresh row
                            insert_sub_sql = """
                                INSERT INTO submissions (task_id, student_id, submitted_filename, status) 
                                VALUES (%s, %s, %s, 'Pending')
                            """
                            BaseModel.execute_write(insert_sub_sql, [task_id, int(student_id), filename])
                            print("Fresh submission recorded.")
                            
                    except Exception as e:
                        print(f"Failed handling student submission file: {e}")
                        
                return redirect(url_for('tasks.student_task'))

        # ========================================================
        # 2️⃣ RENDER task FEED (GET)
        # ========================================================
        current_student_id = self.session.get('user_id')
        
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
            submission_map=submission_map,
            total_tasks_count=total_tasks_count,
            completion_count=completion_count,
            incomplete_count=incomplete_count,
            non_completion_count=remaining,
            over_due=over_due,
            now=datetime.now(),
            score =score
            
        )

    def task_detail(self, task_id):
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
                        print(f"Failed handling student submission file on detail page: {e}")

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
            now=datetime.now()
        )
