from flask import Flask, render_template, request, url_for, flash, redirect
from app.controllers.base_controller import BaseController
from app.models.attendance import Attendance  # Imported your model class
from datetime import date

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
        
        # --- 2. HANDLE GET (Page Load Data Fetching) ---
        # Fetch counts safely via model helper methods
        present_count = Attendance.get_status_count(userid, 'present')
        absent_count = Attendance.get_status_count(userid, 'absent')
        total_days = present_count + absent_count
        
        # Determine status text for your blue layout badge
        today_record = Attendance.get_today_record(userid, today)
        status_text = "Present" if today_record else "Not Marked"
        
        # --- 3. RENDER HTML TEMPLATE ---
        return self.render('attendance/attendance.html',
            username=self.session.get('username'),
            email=self.session.get('email'),
            role=self.session.get('role'),
            attendance_status=status_text,
            date=today,
            present_count=present_count,
            absent_count=absent_count,
            total_days=total_days
        )