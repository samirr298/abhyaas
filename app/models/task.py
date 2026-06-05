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
        raise NotImplementedError()

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
