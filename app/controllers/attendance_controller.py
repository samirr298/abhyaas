from flask import Flask, render_template, request, url_for, flash, redirect
from app.controllers.base_controller import BaseController
from app.models.attendance import Attendance  # Imported your model class
from app.auth import login_required, role_required
from datetime import date,timedelta
import calendar
import math
class AttendanceController(BaseController):
    
    def mark_attendance(self):
        userid = self.session.get('user_id')
        today = date.today()
        
        # --- 1. HANDLE POST (Mark Present Submission) ---
        if request.method == 'POST':
            existing = Attendance.get_today_record(userid, today)
            if existing:
                flash("Attendance already updated for today.", 'warning')
                return redirect(url_for('attend.mark_attendance'))
            else:
                result = Attendance.mark_present(userid, today)
                if result:
                    flash("Attendance marked successfully!", 'success')
                else:
                    flash("Failed to mark attendance. Please try again.", 'error')
                return redirect(url_for('attend.mark_attendance'))
        

         #lazy insertion

        latest_previous_date = Attendance.get_latest_date(userid)
        if latest_previous_date:
            check_date = latest_previous_date + timedelta(days = 1)
        else:
            check_date = today
        while check_date < today:
            if check_date.weekday() not in [5,6]:
                Attendance.mark_absent(userid, check_date)
            check_date +=timedelta(days=1)


        
        # --- 2. HANDLE GET (Page Load Data Fetching) ---
        # Determine status text for your blue layout badge
        today_record = Attendance.get_today_record(userid, today)
        status_text = today_record['status'].replace('_', ' ').title() if today_record else "Not Marked"

        page = max(request.args.get('page', default=1, type=int), 1)
        selected_month = request.args.get('month', default=today.month, type=int)
        selected_year = request.args.get('year', default=today.year, type=int)
        search_query = (request.args.get('q') or '').strip().lower()

        if selected_month < 1 or selected_month > 12:
            selected_month = today.month

        if selected_year < 2000:
            selected_year = today.year

        selected_month_start = date(selected_year, selected_month, 1)
        if selected_month == 12:
            next_month_start = date(selected_year + 1, 1, 1)
        else:
            next_month_start = date(selected_year, selected_month + 1, 1)

        per_page = 10
        total_rows = Attendance.get_total_history_count(
            userid,
            selected_month_start,
            next_month_start
        )
        if search_query:
            history_records = Attendance.get_paginated_history(
                userid,
                1,
                max(total_rows, 1),
                selected_month_start,
                next_month_start
            )
        else:
            history_records = Attendance.get_paginated_history(
                userid,
                page,
                per_page,
                selected_month_start,
                next_month_start
            )
        total_pages = math.ceil(total_rows / per_page) if total_rows > 0 else 1

        present_count = Attendance.get_status_count(userid, 'present', selected_month_start, next_month_start)
        absent_count = Attendance.get_status_count(userid, 'absent', selected_month_start, next_month_start)
        total_days = present_count + absent_count
        current_rate = round((present_count / total_days) * 100, 1) if total_days else 0
        threshold_label = 'Above threshold (90%)' if current_rate >= 90 else 'Below threshold (90%)'

        if search_query:
            filtered_history = []
            for row in history_records:
                row_date = row.get('attendance_date')
                row_text = ' '.join([
                    str(row_date or ''),
                    (row.get('status') or ''),
                    row_date.strftime('%A') if row_date else '',
                    row.get('marked_at').strftime('%I:%M %p') if row.get('marked_at') else '',
                    str(row.get('marked_at') or ''),
                ]).lower()
                if search_query in row_text:
                    filtered_history.append(row)
            history_records = filtered_history
            total_pages = 1
            page = 1

        month_options = [
            {
                'value': month,
                'label': calendar.month_name[month],
                'selected': month == selected_month
            }
            for month in range(1, 13)
        ]
        current_year = today.year
        year_options = [
            {
                'value': year,
                'label': year,
                'selected': year == selected_year
            }
            for year in range(current_year - 5, current_year + 1)
        ]

        # --- 3. RENDER HTML TEMPLATE ---
        return self.render('attendance/attendance.html',
            username=self.session.get('username'),
            email=self.session.get('email'),
            role=self.session.get('role'),
            attendance_status=status_text,
            date=today,
            present_count=present_count,
            absent_count=absent_count,
            total_days=total_days,
            history=history_records,
            current_page=page,
            total_pages=total_pages,
            selected_month=selected_month,
            selected_year=selected_year,
            selected_month_name=calendar.month_name[selected_month],
            month_options=month_options,
            year_options=year_options,
            selected_month_label=f"{calendar.month_name[selected_month]} {selected_year}",
            current_rate=current_rate,
            threshold_label=threshold_label,
            search_query=search_query,
        )

    @login_required
    @role_required('teacher')
    def manage_attendance(self):
        today = date.today()
        search_query = (request.args.get('q') or '').strip().lower()

        if request.method == 'POST':
            student_id = request.form.get('student_id')
            status = request.form.get('status')
            if student_id and status in ['present', 'absent']:
                Attendance.set_attendance_status(student_id, today, status)
                flash('Attendance updated successfully.', 'success')
            else:
                flash('Invalid attendance update.', 'error')
            return redirect(url_for('attend.manage_attendance'))

        student_list = Attendance.get_students_attendance_for_date(today)
        if search_query:
            student_list = [
                student for student in student_list
                if search_query in (student.get('name') or '').lower()
                or search_query in (student.get('username') or '').lower()
                or search_query in (student.get('email') or '').lower()
                or search_query in (student.get('status') or '').lower()
            ]

        present_count = sum(1 for student in student_list if student.get('status') == 'present')
        absent_count = sum(1 for student in student_list if student.get('status') == 'absent')
        not_marked_count = sum(1 for student in student_list if student.get('status') == 'not_marked')
        total_students = len(student_list)
        current_rate = round((present_count / total_students) * 100, 1) if total_students else 0

        return self.render('attendance/manage_attendance.html',
            username=self.session.get('username'),
            email=self.session.get('email'),
            role=self.session.get('role'),
            date=today,
            students=student_list,
            present_count=present_count,
            absent_count=absent_count,
            not_marked_count=not_marked_count,
            total_students=total_students,
            current_rate=current_rate,
            threshold_label='Above threshold (90%)' if current_rate >= 90 else 'Below threshold (90%)',
            search_query=search_query,
        )
