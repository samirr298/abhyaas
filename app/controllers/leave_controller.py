from datetime import date
from flask import render_template, request, redirect, url_for, flash
from app.auth import login_required, role_required
from app.controllers.base_controller import BaseController
from app.models.leave_request import LeaveRequest


class LeaveController(BaseController):
    @login_required
    @role_required('student')
    def apply_leave(self):
        current_user_id = self.session.get('user_id')

        if request.method == 'POST':
            action = request.form.get('action')

            if action == 'cancel':
                request_id = request.form.get('request_id')
                if request_id and LeaveRequest.delete_pending(current_user_id, request_id):
                    flash('Pending leave request cancelled successfully.', 'success')
                else:
                    flash('Unable to cancel leave request.', 'error')
                return redirect(url_for('leave.apply_leave'))

            leave_date_str = request.form.get('leave_date')
            reason = (request.form.get('leave_reason') or '').strip()

            if not leave_date_str or not reason:
                flash('Please provide both a date and a reason for leave.', 'error')
                return redirect(url_for('leave.apply_leave'))

            try:
                leave_date = date.fromisoformat(leave_date_str)
            except ValueError:
                flash('Please select a valid leave date.', 'error')
                return redirect(url_for('leave.apply_leave'))

            if leave_date < date.today():
                flash('You cannot apply for a leave date that has already passed.', 'error')
                return redirect(url_for('leave.apply_leave'))

            if len(reason) < 10:
                flash('Please provide a reason with at least 10 characters.', 'error')
                return redirect(url_for('leave.apply_leave'))

            if LeaveRequest.create(current_user_id, leave_date, reason):
                flash('Leave request submitted successfully. Status is now Pending.', 'success')
            else:
                flash('Unable to submit leave request. Please try again later.', 'error')

            return redirect(url_for('leave.apply_leave'))

        status_filter = (request.args.get('status_filter') or '').strip().lower()
        leave_requests = LeaveRequest.get_by_user(current_user_id, status_filter)
        notifications = LeaveRequest.get_unread_notifications_by_user(current_user_id)

        if notifications:
            LeaveRequest.mark_notifications_read(current_user_id)

        return self.render(
            'users/apply_leave.html',
            leave_requests=leave_requests,
            status_filter=status_filter,
            today_date=date.today().isoformat(),
            notifications=notifications,
        )

    @login_required
    @role_required('teacher')
    def teacher_leave_requests(self):
        if request.method == 'POST':
            action = request.form.get('action')
            request_id = request.form.get('request_id')
            leave_request = LeaveRequest.get_by_id(request_id) if request_id else None

            if not leave_request:
                flash('Leave request not found.', 'error')
                return redirect(url_for('leave.teacher_leave_requests'))

            if leave_request.get('status') != 'Pending':
                flash('Only pending leave requests can be updated.', 'error')
                return redirect(url_for('leave.teacher_leave_requests'))

            if action == 'approve':
                LeaveRequest.update_status(request_id, 'Approved')
                flash('Leave request approved.', 'success')
            elif action == 'reject':
                LeaveRequest.update_status(request_id, 'Rejected')
                flash('Leave request rejected.', 'success')
            else:
                flash('Invalid action. Please try again.', 'error')

            return redirect(url_for('leave.teacher_leave_requests'))

        status_filter = (request.args.get('status_filter') or '').strip().lower()
        leave_requests = LeaveRequest.get_all_requests(status_filter)

        return self.render(
            'users/teacher_leave_requests.html',
            leave_requests=leave_requests,
            status_filter=status_filter,
        )
