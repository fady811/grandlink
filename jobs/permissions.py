from rest_framework import permissions


class IsEmployer(permissions.BasePermission):
    """
    Only users with role='employer' can access.
    Used for: creating jobs, viewing applications for own jobs.
    """
    message = 'Only employers can perform this action.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'employer'
        )


class IsStudent(permissions.BasePermission):
    """
    Only users with role='student' can access.
    Used for: applying to jobs, saving jobs.
    """
    message = 'Only students can perform this action.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'student'
        )


class IsJobOwner(permissions.BasePermission):
    """
    Only the employer who posted the job can modify it.
    Used for: updating/deleting own jobs.
    """
    message = 'You can only modify your own job postings.'

    def has_object_permission(self, request, view, obj):
        # obj is a Job instance
        return obj.employer.user == request.user


class IsApplicationOwnerOrJobOwner(permissions.BasePermission):
    """
    - Student who submitted the application can view/withdraw it.
    - Employer who owns the job can view/update application status.
    """
    message = 'You do not have permission to access this application.'

    def has_object_permission(self, request, view, obj):
        user = request.user
        # Student who applied
        if user.role == 'student' and obj.student.user == user:
            return True
        # Employer who owns the job
        if user.role == 'employer' and obj.job.employer.user == user:
            return True
        # Admin
        if user.is_staff:
            return True
        return False
