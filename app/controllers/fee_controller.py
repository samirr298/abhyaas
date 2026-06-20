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
        """Admin endpoint to update fee payment details."""
        if request.method != 'POST':
            flash('Invalid request method.', 'error')
            return redirect(url_for('auth.fees_management'))

        action = (request.form.get('action') or 'set_status').strip()
        student_id = request.form.get('student_id')

        if not student_id:
            flash('Missing student ID.', 'error')
            return redirect(url_for('auth.fees_management'))

        # Verify student exists
        student = Users.get_student_by_id(student_id)
        if not student:
            flash('Student not found.', 'error')
            return redirect(url_for('auth.fees_management'))

        if action == 'set_fee_amount':
            # fee_amount and fee_due_date are required/optional respectively
            try:
                fee_amount = request.form.get('fee_amount')
                fee_amount = float(fee_amount)
            except Exception:
                flash('Invalid fee amount.', 'error')
                return redirect(url_for('auth.fees_management'))

            if fee_amount < 0:
                flash('Fee amount cannot be negative.', 'error')
                return redirect(url_for('auth.fees_management'))

            fee_due_date = request.form.get('fee_due_date')
            if fee_due_date is not None:
                fee_due_date = fee_due_date.strip()
                if fee_due_date == '':
                    fee_due_date = None

            if Users.set_fee_details(student_id, fee_amount=fee_amount, fee_due_date=fee_due_date):
                flash(f"Fee set for {student['name']}.", 'success')
            else:
                flash('Failed to set fee. Please try again.', 'error')

            return redirect(url_for('auth.fees_management'))

        if action == 'record_payment':
            # payment_amount is required
            try:
                payment_amount = request.form.get('payment_amount')
                payment_amount = float(payment_amount)
            except Exception:
                flash('Invalid payment amount.', 'error')
                return redirect(url_for('auth.fees_management'))

            if payment_amount < 0:
                flash('Payment amount cannot be negative.', 'error')
                return redirect(url_for('auth.fees_management'))

            if Users.record_fee_payment(student_id, payment_amount, payment_at=None):
                flash(f"Payment recorded for {student['name']}.", 'success')
            else:
                flash('Failed to record payment. Please try again.', 'error')

            return redirect(url_for('auth.fees_management'))

        if action == 'reset_fee':
            if Users.reset_fee(student_id):
                flash(f"Fee reset for {student['name']}.", 'success')
            else:
                flash('Failed to reset fee. Please try again.', 'error')
            return redirect(url_for('auth.fees_management'))

        # Backward-compatible: set_status (paid/unpaid)
        fee_status = request.form.get('fee_status')
        if fee_status not in ['paid', 'unpaid']:
            flash('Invalid fee status. Please use "paid" or "unpaid".', 'error')
            return redirect(url_for('auth.fees_management'))

        if Users.update_fee_status(student_id, fee_status):
            flash(f"Fee status updated to '{fee_status}' for {student['name']}", 'success')
        else:
            flash('Failed to update fee status. Please try again.', 'error')

        return redirect(url_for('auth.fees_management'))

    

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
            
        # 4. Extract the fee status & details
        current_status = student_data.get('fee_status', 'unpaid').upper()
        last_updated_time = student_data.get('fee_updated_at', 'Time not available')

        fee_amount = student_data.get('fee_amount')
        fee_due_date = student_data.get('fee_due_date')
        fee_paid_amount = student_data.get('fee_paid_amount')
        fee_last_payment_at = student_data.get('fee_last_payment_at')

        # Normalize numeric display
        try:
            fee_amount = float(fee_amount) if fee_amount is not None else 0.0
        except Exception:
            fee_amount = 0.0

        try:
            fee_paid_amount = float(fee_paid_amount) if fee_paid_amount is not None else 0.0
        except Exception:
            fee_paid_amount = 0.0

        remaining = max(0.0, fee_amount - fee_paid_amount)

        # 5. Create a dynamic notice based on their status
        if current_status == 'UNPAID':
            if remaining > 0 and fee_amount > 0:
                notice_msg = f"Your fees are pending. Remaining due: {remaining:.2f}. Please clear your dues." 
            else:
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
            last_updated=last_updated_time,
            fee_amount=fee_amount,
            fee_due_date=fee_due_date,
            fee_paid_amount=fee_paid_amount,
            fee_last_payment_at=fee_last_payment_at
        )

