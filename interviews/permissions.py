from rest_framework import permissions


class IsInterviewParticipant(permissions.BasePermission):
    """
    Both the employer who owns the job AND the student
    being interviewed can view the interview.
    """
    message = 'You do not have permission to access this interview.'

    def has_object_permission(self, request, view, obj):
        user = request.user
        # Employer who owns the job
        if user.role == 'employer' and obj.application.job.employer.user == user:
            return True
        # Student who applied
        if user.role == 'student' and obj.application.student.user == user:
            return True
        # Admin
        if user.is_staff:
            return True
        return False


class IsInterviewEmployer(permissions.BasePermission):
    """
    Only the employer who owns the job can schedule, update,
    cancel, or submit feedback for interviews.
    """
    message = 'Only the employer who posted this job can manage interviews.'

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_staff:
            return True
        return (
            user.role == 'employer'
            and obj.application.job.employer.user == user
        )


class IsInterviewStudent(permissions.BasePermission):
    """
    Only the student being interviewed can confirm attendance.
    """
    message = 'Only the interviewed student can perform this action.'

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_staff:
            return True
        return (
            user.role == 'student'
            and obj.application.student.user == user
        )
