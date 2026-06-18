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
            end_date_str = request.form.get('end_date')
            leave_type = (request.form.get('leave_type') or '').strip()
            reason = (request.form.get('leave_reason') or '').strip()

            if not leave_date_str or not end_date_str or not leave_type or not reason:
                flash('Please complete all fields before submitting a leave request.', 'error')
                return redirect(url_for('leave.apply_leave'))

            try:
                leave_date = date.fromisoformat(leave_date_str)
                end_date = date.fromisoformat(end_date_str)
            except ValueError:
                flash('Please select valid leave dates.', 'error')
                return redirect(url_for('leave.apply_leave'))

            if leave_date < date.today() or end_date < date.today():
                flash('Leave dates cannot be in the past.', 'error')
                return redirect(url_for('leave.apply_leave'))

            if end_date < leave_date:
                flash('End date cannot be earlier than start date.', 'error')
                return redirect(url_for('leave.apply_leave'))

            if len(reason) < 10:
                flash('Please provide a reason with at least 10 characters.', 'error')
                return redirect(url_for('leave.apply_leave'))

            if LeaveRequest.create(current_user_id, leave_date, end_date, leave_type, reason):
                flash('Leave request submitted successfully. Status is now Pending.', 'success')
            else:
                flash('Unable to submit leave request. Please try again later.', 'error')

            return redirect(url_for('leave.apply_leave'))

        status_filter = (request.args.get('status_filter') or '').strip().lower()
        leave_requests = LeaveRequest.get_by_user(current_user_id, status_filter)
        notifications = LeaveRequest.get_unread_notifications_by_user(current_user_id)

        approved_days = 0
        pending_count = 0
        for req in leave_requests:
            if str(req.get('status', '')).lower() == 'pending':
                pending_count += 1

            start_date = req.get('leave_date')
            end_date = req.get('end_date') or start_date
            if isinstance(start_date, str):
                start_date = date.fromisoformat(start_date)
            if isinstance(end_date, str):
                end_date = date.fromisoformat(end_date)

            duration_days = max(1, (end_date - start_date).days + 1)
            req['start_date'] = start_date
            req['end_date'] = end_date
            req['date_range'] = f"{start_date.isoformat()} - {end_date.isoformat()}" if start_date != end_date else start_date.isoformat()
            req['duration_days'] = duration_days

            if str(req.get('status', '')).lower() == 'approved':
                approved_days += duration_days

        total_allowed_days = 21
        remaining_days = max(total_allowed_days - approved_days, 0)

        if notifications:
            LeaveRequest.mark_notifications_read(current_user_id)

        return self.render(
            'users/apply_leave.html',
            leave_requests=leave_requests,
            status_filter=status_filter,
            today_date=date.today().isoformat(),
            notifications=notifications,
            total_taken=approved_days,
            pending_count=pending_count,
            remaining_days=remaining_days,
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
            if str(leave_request.get('status', '')).lower() != 'pending':
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
