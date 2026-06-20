from flask import render_template, request, redirect, url_for, flash
from app.controllers.base_controller import BaseController
from app.models.user import Users
from app.auth import login_required, role_required


class FeeController(BaseController):
    
    @login_required
    @role_required('admin')
    def fees_management(self):
        """Display all students with their fee status, calculating the filter dynamically."""
        fee_filter = request.args.get('filter', default=None)
        if fee_filter and fee_filter not in ['paid', 'unpaid']:
            fee_filter = None
        
        # Pull all student accounts to evaluate individual active invoices
        all_students = Users.get_all_students(fee_filter=None)
        filtered_students = []
        
        for student in all_students:
            individual_fees = Users.get_fees_by_student_id(student['id'])
            student['individual_fees'] = individual_fees
            
            if individual_fees:
                # Accumulate live ledger values
                student['fee_amount'] = sum(float(f['amount'] or 0) for f in individual_fees)
                student['fee_paid_amount'] = sum(float(f['paid_amount'] or 0) for f in individual_fees)
                
                # If any single ledger line is unpaid, the whole account standing is unpaid
                has_unpaid = any(f['status'] != 'paid' for f in individual_fees)
                calculated_status = 'unpaid' if has_unpaid else 'paid'
                student['fee_status'] = calculated_status
                
                # Fetch closest processing timeline due date
                unpaid_deadlines = [f['due_date'] for f in individual_fees if f['status'] != 'paid' and f['due_date']]
                if unpaid_deadlines:
                    student['fee_due_date'] = min(unpaid_deadlines)
                else:
                    all_deadlines = [f['due_date'] for f in individual_fees if f['due_date']]
                    student['fee_due_date'] = max(all_deadlines) if all_deadlines else None
            else:
                # Safe fallbacks if no dues are currently registered
                student['fee_amount'] = 0.0
                student['fee_paid_amount'] = 0.0
                student['fee_status'] = 'paid'
                student['fee_due_date'] = None
                calculated_status = 'paid'
            
            # Append only if it satisfies your sidebar pipeline selection parameters
            if not fee_filter or calculated_status == fee_filter:
                filtered_students.append(student)
            
        return self.render(
            'users/fees_management.html',
            username=self.session.get('username'),
            email=self.session.get('email'),
            role=self.session.get('role'),
            students=filtered_students,
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

        # -------------------------------------------------------------
        # 1. Handle Bulk Actions First (These don't need a single student_id)
        # -------------------------------------------------------------
        if action == 'bulk_set_fee':
            target_group = request.form.get('target_group', 'all')
            title = request.form.get('fee_title', '').strip() or "General Semester Dues"
            try:
                fee_amount = float(request.form.get('fee_amount', 0))
            except ValueError:
                flash('Invalid fee amount numerical syntax.', 'error')
                return redirect(url_for('auth.fees_management'))

            fee_due_date = request.form.get('fee_due_date', '').strip() or None

            # Fetch everyone and dynamically calculate who fits the target group
            all_students = Users.get_all_students(fee_filter=None)
            target_ids = []

            for student in all_students:
                individual_fees = Users.get_fees_by_student_id(student['id'])
                has_unpaid = any(f['status'] != 'paid' for f in individual_fees) if individual_fees else False
                calc_status = 'unpaid' if has_unpaid else 'paid'

                if target_group == 'all' or target_group == calc_status:
                    target_ids.append(student['id'])

            if not target_ids:
                flash('No students currently match the selected pipeline group.', 'error')
                return redirect(url_for('auth.fees_management'))

            # Issue the bills
            success_count = 0
            for sid in target_ids:
                if Users.add_student_due(sid, title, fee_amount, fee_due_date):
                    success_count += 1

            flash(f"Successfully allocated '{title}' to {success_count} student accounts.", 'success')
            return redirect(url_for('auth.fees_management'))
        
        if action == 'bulk_delete_fee':
            target_group = request.form.get('target_group', 'all')
            title = request.form.get('fee_title', '').strip()

            if not title:
                flash('Please provide the exact invoice title to delete.', 'error')
                return redirect(url_for('auth.fees_management'))

            # Fetch all students and find who fits the target group
            all_students = Users.get_all_students(fee_filter=None)
            target_ids = []

            for student in all_students:
                individual_fees = Users.get_fees_by_student_id(student['id'])
                has_unpaid = any(f['status'] != 'paid' for f in individual_fees) if individual_fees else False
                calc_status = 'unpaid' if has_unpaid else 'paid'

                if target_group == 'all' or target_group == calc_status:
                    target_ids.append(student['id'])

            if not target_ids:
                flash('No students matched the selected group for deletion.', 'error')
                return redirect(url_for('auth.fees_management'))

            # Hunt down the specific fee by title for each targeted student and delete it
            delete_count = 0
            for sid in target_ids:
                individual_fees = Users.get_fees_by_student_id(sid)
                for fee in individual_fees:
                    if fee['title'].strip().lower() == title.lower():
                        if Users.delete_fee(fee['id']):
                            delete_count += 1

            if delete_count > 0:
                flash(f"Successfully retracted/deleted invoice '{title}' from {delete_count} student accounts.", 'success')
            else:
                flash(f"No invoices found matching the title '{title}' in the selected group.", 'error')
                
            return redirect(url_for('auth.fees_management'))

        # 2. Handle Individual Student Actions (Require student_id)
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
            target_group = request.form.get('target_group', 'all')
            title = request.form.get('fee_title', '').strip() or "General Semester Dues"
            try:
                fee_amount = float(request.form.get('fee_amount', 0))
            except ValueError:
                flash('Invalid fee amount numerical syntax.', 'error')
                return redirect(url_for('auth.fees_management'))

            fee_due_date = request.form.get('fee_due_date', '').strip() or None

            # Fetch everyone and dynamically calculate who fits the target group
            all_students = Users.get_all_students(fee_filter=None)
            target_ids = []

            for student in all_students:
                individual_fees = Users.get_fees_by_student_id(student['id'])
                has_unpaid = any(f['status'] != 'paid' for f in individual_fees) if individual_fees else False
                calc_status = 'unpaid' if has_unpaid else 'paid'

                if target_group == 'all' or target_group == calc_status:
                    target_ids.append(student['id'])

            if not target_ids:
                flash('No students currently match the selected pipeline group.', 'error')
                return redirect(url_for('auth.fees_management'))

            # Issue the bills
            success_count = 0
            for sid in target_ids:
                if Users.add_student_due(sid, title, fee_amount, fee_due_date):
                    success_count += 1

            flash(f"Successfully allocated '{title}' to {success_count} student accounts.", 'success')
            return redirect(url_for('auth.fees_management'))
        
        if action == 'bulk_delete_fee':
            target_group = request.form.get('target_group', 'all')
            title = request.form.get('fee_title', '').strip()

            if not title:
                flash('Please provide the exact invoice title to delete.', 'error')
                return redirect(url_for('auth.fees_management'))

            # Fetch all students and find who fits the target group
            all_students = Users.get_all_students(fee_filter=None)
            target_ids = []

            for student in all_students:
                individual_fees = Users.get_fees_by_student_id(student['id'])
                has_unpaid = any(f['status'] != 'paid' for f in individual_fees) if individual_fees else False
                calc_status = 'unpaid' if has_unpaid else 'paid'

                if target_group == 'all' or target_group == calc_status:
                    target_ids.append(student['id'])

            if not target_ids:
                flash('No students matched the selected group for deletion.', 'error')
                return redirect(url_for('auth.fees_management'))

            # Hunt down the specific fee by title for each targeted student and delete it
            delete_count = 0
            for sid in target_ids:
                individual_fees = Users.get_fees_by_student_id(sid)
                for fee in individual_fees:
                    # Case-insensitive match to prevent typos leaving orphaned bills
                    if fee['title'].strip().lower() == title.lower():
                        if Users.delete_fee(fee['id']):
                            delete_count += 1

            if delete_count > 0:
                flash(f"Successfully retracted/deleted invoice '{title}' from {delete_count} student accounts.", 'success')
            else:
                flash(f"No invoices found matching the title '{title}' in the selected group.", 'error')
                
            return redirect(url_for('auth.fees_management'))
        

        if action == 'set_fee_amount':
            title = request.form.get('fee_title', '').strip() or "General Semester Dues"
            try:
                fee_amount = float(request.form.get('fee_amount', 0))
            except ValueError:
                flash('Invalid fee amount numerical syntax.', 'error')
                return redirect(url_for('auth.fees_management'))

            fee_due_date = request.form.get('fee_due_date', '').strip() or None

            if Users.add_student_due(student_id, title, fee_amount, fee_due_date):
                flash(f"New charge profile '{title}' successfully assigned to {student['name']}.", 'success')
            else:
                flash('Database record assignment dropped. Try again.', 'error')
            return redirect(url_for('auth.fees_management'))

        if action == 'record_payment':
            fee_id = request.form.get('fee_id')
            try:
                payment_amount = float(request.form.get('payment_amount', 0))
            except ValueError:
                flash('Invalid payment numeric data.', 'error')
                return redirect(url_for('auth.fees_management'))

            if not fee_id:
                flash('Please pick an active invoice item allocation target first.', 'error')
                return redirect(url_for('auth.fees_management'))

            if Users.record_payment_on_fee(fee_id, payment_amount):
                flash(f"Collection entry recorded successfully.", 'success')
            else:
                flash('Failed to post payment collection.', 'error')
            return redirect(url_for('auth.fees_management'))

        if action == 'reset_fee':
            fee_id = request.form.get('fee_id')
            if fee_id and Users.reset_single_fee(fee_id):
                flash('Target invoice balance parameters reset.', 'success')
            else:
                flash('Failed to clear balance row item.', 'error')
            return redirect(url_for('auth.fees_management'))
        
        if action == 'delete_fee':
            fee_id = request.form.get('fee_id')
            if fee_id and Users.delete_fee(fee_id):
                flash('Due invoice completely deleted from records.', 'success')
            else:
                flash('Failed to delete due invoice.', 'error')
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
        """Display consolidated ledger invoices for the active student account."""
        if self.session.get('role') != 'student':
            flash('Only students can view personal fee profiles.', 'error')
            return redirect(url_for('auth.profile'))
            
        student_id = self.session.get('user_id')
        fees_list = Users.get_fees_by_student_id(student_id)

        transactions = Users.get_transactions_by_student_id(student_id)
        for fee in fees_list:
            fee['transactions'] = [t for t in transactions if t['fee_id'] == fee['id']]
        
        # Calculate dynamic matrix aggregates on the fly
        total_billed = sum(float(f['amount'] or 0) for f in fees_list)
        total_paid = sum(float(f['paid_amount'] or 0) for f in fees_list)
        total_balance = max(0.0, total_billed - total_paid)
        
        global_status = "PAID" if (total_billed > 0 and total_paid >= total_billed) or (total_billed == 0) else "UNPAID"
        notice_msg = "All clear! Excellent status standing." if global_status == "PAID" else f"Pending payment collection required. Current net balance: NPR {total_balance:.2f}"

        return self.render(
            'users/student_fees.html',
            username=self.session.get('username'),
            email=self.session.get('email'),
            role=self.session.get('role'),
            fees=fees_list,
            fee_status=global_status,
            notice=notice_msg,
            fee_amount=total_billed,
            fee_paid_amount=total_paid,
            balance=total_balance
        )

