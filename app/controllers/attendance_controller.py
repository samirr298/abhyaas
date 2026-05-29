from flask import Flask, render_template, request, url_for, flash, redirect
from app.controllers.base_controller import BaseController
from app.models.attendance import Attendance  # Imported your model class
from datetime import date,timedelta
import math
class AttendanceController(BaseController):
    
    def mark_attendance(self):
        userid = self.session.get('user_id')
        today = date.today()
        
        # --- 1. HANDLE POST (Mark Present Submission) ---
        if request.method == 'POST':
            existing = Attendance.get_today_record(userid, today)
            if existing:
                flash("You are already Present !")
                return redirect(url_for('attend.mark_attendance'))
            else:
                Attendance.mark_present(userid, today)
                flash("Attendance Done !")
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
        # Fetch counts safely via model helper methods
        present_count = Attendance.get_status_count(userid, 'present')
        absent_count = Attendance.get_status_count(userid, 'absent')
        total_days = present_count + absent_count
        
        # Determine status text for your blue layout badge
        today_record = Attendance.get_today_record(userid, today)
        status_text = "Present" if today_record else "Not Marked"

        #attendance_history and pagination
        # Grabs ?page=X from the URL bar; defaults to page 1
        page = request.args.get('page', default=1, type=int)
        per_page = 10
        offset = (page - 1) * per_page

        history_records = Attendance.get_paginated_history(userid, per_page, offset)
        total_rows = Attendance.get_total_history_count(userid)
        total_pages = math.ceil(total_rows / per_page) if total_rows > 0 else 1
        print(total_pages) 

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
            history=history_records,      # <--- Passed to HTML table loop
            current_page=page,            # <--- Passed for active page color
            total_pages=total_pages,
            show = "all"
        )