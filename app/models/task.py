# Placeholder task models. Implement DB logic as needed.
class Task:
    @classmethod
    def create_task(cls, *args, **kwargs):
        raise NotImplementedError()

    @classmethod
    def get_teacher_tasks(cls, teacher_id):
        raise NotImplementedError()

    @classmethod
    def get_today_tasks(cls, student_id):
        # Return tasks that are either due today or still pending (not submitted) for this student
        sql = """
            SELECT t.*, 
                   ts.id AS submission_id,
                   ts.status AS submission_status,
                   ts.submitted_at,
                   ts.submission_text,
                   ts.teacher_feedback,
                   ts.submission_file_path
            FROM tasks t
            LEFT JOIN task_submissions ts
                ON ts.task_id = t.id AND ts.student_id = %s
            WHERE t.is_active = 1
              AND (
                    DATE(t.deadline) = CURDATE()
                    OR ts.status IS NULL
                    OR ts.status != 'submitted'
                  )
            ORDER BY t.deadline ASC, t.created_at ASC
        """
        return cls.fetch_all(sql, [student_id])

    @classmethod
    def get_task(cls, task_id):
        raise NotImplementedError()


class TaskSubmission:
    @classmethod
    def create_submission(cls, *args, **kwargs):
        raise NotImplementedError()

    @classmethod
    def get_submission_for_task(cls, task_id, student_id):
        raise NotImplementedError()

    @classmethod
    def update_submission(cls, submission_id, submission_text, submission_file_path=None):
        raise NotImplementedError()

    @classmethod
    def get_submissions_for_task(cls, task_id):
        raise NotImplementedError()

    @classmethod
    def save_feedback(cls, submission_id, teacher_feedback):
        raise NotImplementedError()
