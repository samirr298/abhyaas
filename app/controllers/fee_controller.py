from flask import render_template, request, redirect, url_for, flash
from app.controllers.base_controller import BaseController
from app.models.user import Users
from app.auth import login_required, role_required


class FeeController(BaseController):
    
    @login_required
    @role_required('admin')
    def fees_management(self):
        """Display all students with their fee status, with optional filtering."""
        fee_filter = request.args.get('filter', default=None)
        
        # Validate filter
        if fee_filter and fee_filter not in ['paid', 'unpaid']:
            fee_filter = None
        
        # Fetch students based on filter
        students = Users.get_all_students(fee_filter=fee_filter)
        
        return self.render(
            'users/fees_management.html',
            username=self.session.get('username'),
            email=self.session.get('email'),
            role=self.session.get('role'),
            students=students,
            current_filter=fee_filter
        )
    
    @login_required
    @role_required('admin')
    def update_fee_status(self):
        """Update a student's fee status."""
        if request.method == 'POST':
            student_id = request.form.get('student_id')
            fee_status = request.form.get('fee_status')
            
            # Validate inputs
            if not student_id or not fee_status:
                flash('Invalid request. Missing student ID or fee status.', 'error')
                return redirect(url_for('fee.fees_management'))
            
            if fee_status not in ['paid', 'unpaid']:
                flash('Invalid fee status. Please use "paid" or "unpaid".', 'error')
                return redirect(url_for('fee.fees_management'))
            
            # Verify student exists
            student = Users.get_student_by_id(student_id)
            if not student:
                flash('Student not found.', 'error')
                return redirect(url_for('fee.fees_management'))
            
            # Update fee status
            if Users.update_fee_status(student_id, fee_status):
                flash(f"Fee status updated to '{fee_status}' for {student['name']}", 'success')
            else:
                flash('Failed to update fee status. Please try again.', 'error')
            
            return redirect(url_for('fee.fees_management'))
        
        flash('Invalid request method.', 'error')
        return redirect(url_for('fee.fees_management'))
    

    @login_required
    def student_fees(self):
        """Display the fee status and notices for the currently logged-in student."""
        # 1. Double check that an admin didn't accidentally navigate here
        if self.session.get('role') != 'student':
            flash('Only students can view personal fee status.', 'error')
            return redirect(url_for('auth.profile'))
            
        # 2. Get the current student's ID from the session
        student_id = self.session.get('user_id')
        
        # 3. Fetch their exact details from the database
        student_data = Users.get_student_by_id(student_id)
        
        # Handle edge case if the database fails to find them
        if not student_data:
            flash('Could not retrieve fee data. Please contact admin.', 'error')
            return redirect(url_for('auth.profile'))
            
        # 4. Extract the fee status
        current_status = student_data.get('fee_status', 'unpaid').upper()
        
        # NEW: Grab the exact time the admin updated the status
        # Change 'fee_updated_at' to whatever your actual database column is named!
        last_updated_time = student_data.get('fee_updated_at', 'Time not available')
        
        # 5. Create a dynamic notice based on their status
        if current_status == 'UNPAID':
            notice_msg = "Your fees for the current semester are pending. Please clear your dues as soon as possible to avoid late penalties."
        else:
            notice_msg = "Thank you! Your fees for the current semester are fully paid. You have no pending dues."

        # 6. Send all of this to the HTML page
        return self.render(
            'users/student_fees.html',
            username=self.session.get('username'),
            email=self.session.get('email'),
            role=self.session.get('role'),
            fee_status=current_status,
            notice=notice_msg,
            last_updated=last_updated_time  # NEW: Passing the time to Jinja
        )
