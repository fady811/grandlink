from rest_framework import generics, permissions, status, filters
from rest_framework.response import Response
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django.db.models import Q, F
from django.db import IntegrityError
from django.utils import timezone

from core.pagination import StandardPagination
from profiles.models import StudentProfile
from .models import Job, Application, SavedJob, Skill, JobReport, JobCategory
from .serializers import (
    SkillSerializer,
    JobCategorySerializer,
    JobListSerializer,
    JobDetailSerializer,
    ApplicationCreateSerializer,
    ApplicationListSerializer,
    ApplicationDetailSerializer,
    ApplicationStatusUpdateSerializer,
    SavedJobSerializer,
    JobReportSerializer
)
from .permissions import IsEmployer, IsStudent, IsJobOwner, IsApplicationOwnerOrJobOwner, IsNotJobOwner
from .services import process_job_report


# ═══════════════════════════════════════════════════════════════
#  SKILL VIEWS
# ═══════════════════════════════════════════════════════════════

class SkillListView(generics.ListAPIView):
    """
    GET /api/jobs/skills/ — List all skills (for autocomplete/dropdowns).
    Public for authenticated users.
    """
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None  # Return all skills without pagination for dropdown usage
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


# ═══════════════════════════════════════════════════════════════
#  CATEGORY VIEWS
# ═══════════════════════════════════════════════════════════════

class JobCategoryListView(generics.ListAPIView):
    """
    GET /api/jobs/categories/ — List all active job categories.
    Public for authenticated users.
    """
    queryset = JobCategory.objects.filter(is_active=True)
    serializer_class = JobCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']


# ═══════════════════════════════════════════════════════════════
#  JOB VIEWS
# ═══════════════════════════════════════════════════════════════

class JobListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/jobs/          — List active jobs (all authenticated users).
    POST /api/jobs/          — Create a new job (employers only).
    """
    pagination_class = StandardPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'location', 'employer__company_name']
    ordering_fields = ['created_at', 'deadline', 'salary_min', 'salary_max', 'views_count']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return JobDetailSerializer
        return JobListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated(), IsEmployer()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        """
        - All users see ACTIVE jobs.
        - Supports filtering via query params.
        """
        qs = Job.objects.select_related('employer', 'employer__user', 'category').prefetch_related('skills')

        # By default, only show active and unflagged jobs in the public list
        qs = qs.filter(status=Job.Status.ACTIVE, is_flagged=False)

        # ── Query param filters ──────────────────────────────────
        params = self.request.query_params

        work_type = params.get('work_type')
        if work_type:
            qs = qs.filter(work_type=work_type)

        experience_level = params.get('experience_level')
        if experience_level:
            qs = qs.filter(experience_level=experience_level)

        is_remote = params.get('is_remote')
        if is_remote is not None:
            qs = qs.filter(is_remote=is_remote.lower() in ('true', '1'))

        location = params.get('location')
        if location:
            qs = qs.filter(location__icontains=location)

        category = params.get('category')
        if category:
            # Filter by category slug (standard for URLs) or ID
            if category.isdigit():
                qs = qs.filter(category_id=category)
            else:
                qs = qs.filter(category__slug=category)

        skill_ids = params.get('skills')
        if skill_ids:
            ids = [s.strip() for s in skill_ids.split(',') if s.strip()]
            qs = qs.filter(skills__id__in=ids).distinct()

        salary_min = params.get('salary_min')
        if salary_min:
            try:
                qs = qs.filter(salary_max__gte=float(salary_min))
            except ValueError:
                pass

        salary_max = params.get('salary_max')
        if salary_max:
            try:
                qs = qs.filter(salary_min__lte=float(salary_max))
            except ValueError:
                pass

        return qs

    def perform_create(self, serializer):
        """Automatically attach the employer profile to the job."""
        employer_profile = get_object_or_404(
            # Use the authenticated user's employer profile
            self.request.user.employer_profile.__class__,
            user=self.request.user,
        )
        serializer.save(employer=employer_profile)


class JobDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/jobs/<uuid>/  — View job details (any authenticated user).
    PUT    /api/jobs/<uuid>/  — Full update (job owner only; blocked if pending_review).
    PATCH  /api/jobs/<uuid>/  — Partial update (job owner only; blocked if pending_review).
    DELETE /api/jobs/<uuid>/  — Delete job (job owner only; withdraws from review if pending).
    """
    serializer_class = JobDetailSerializer
    queryset = Job.objects.select_related('employer', 'employer__user').prefetch_related('skills')

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH', 'DELETE'):
            return [permissions.IsAuthenticated(), IsEmployer(), IsJobOwner()]
        return [permissions.IsAuthenticated()]

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        # Block employer writes on pending_review jobs (read-only enforced)
        if (
            request.method in ('PUT', 'PATCH')
            and obj.status == Job.Status.PENDING_REVIEW
            and not request.user.is_staff
        ):
            self.permission_denied(
                request,
                message='This job is currently under review and cannot be modified.',
            )

    def retrieve(self, request, *args, **kwargs):
        """Increment view count on each retrieval."""
        instance = self.get_object()
        # Use F() to avoid race conditions
        Job.objects.filter(pk=instance.pk).update(views_count=F('views_count') + 1)
        instance.refresh_from_db()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """If pending_review, treat DELETE as 'withdraw from review' → draft."""
        instance = self.get_object()
        if instance.status == Job.Status.PENDING_REVIEW:
            instance.status = Job.Status.DRAFT
            instance.submitted_at = None
            instance.save(update_fields=['status', 'submitted_at', 'updated_at'])
            return Response(
                {'message': 'Job withdrawn from review and returned to draft.'},
                status=status.HTTP_200_OK,
            )
        return super().destroy(request, *args, **kwargs)


class MyJobsListView(generics.ListAPIView):
    """
    GET /api/jobs/my-jobs/ — Employer's own job postings (all statuses).
    """
    serializer_class = JobListSerializer
    permission_classes = [permissions.IsAuthenticated, IsEmployer]
    pagination_class = StandardPagination

    def get_queryset(self):
        return (
            Job.objects
            .filter(employer__user=self.request.user)
            .select_related('employer', 'employer__user')
            .prefetch_related('skills')
        )


class SubmitForReviewView(generics.GenericAPIView):
    """
    POST /api/jobs/<uuid>/submit-for-review/
    Employer submits a draft job for admin approval.
    """
    permission_classes = [permissions.IsAuthenticated, IsEmployer, IsJobOwner]
    queryset = Job.objects.select_related('employer', 'employer__user')

    def post(self, request, pk):
        job = self.get_object()

        # Only draft jobs can be submitted for review (allows resubmission after rejection)
        if job.status != Job.Status.DRAFT:
            return Response(
                {'error': f'Only draft jobs can be submitted for review. '
                          f'Current status: {job.get_status_display()}.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Basic required fields check
        if not job.title or not job.description:
            return Response(
                {'error': 'Job must have at least a title and description before submission.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        job.status = Job.Status.PENDING_REVIEW
        job.submitted_at = timezone.now()
        job.rejection_reason = ''  # Clear previous rejection reason
        job.save(update_fields=['status', 'submitted_at', 'rejection_reason', 'updated_at'])

        serializer = JobDetailSerializer(job, context={'request': request})
        return Response(
            {
                'message': 'Job submitted for admin review.',
                'job': serializer.data,
            },
            status=status.HTTP_200_OK,
        )


# ═══════════════════════════════════════════════════════════════
#  APPLICATION VIEWS
# ═══════════════════════════════════════════════════════════════

class ApplyToJobView(generics.CreateAPIView):
    """
    POST /api/jobs/<uuid>/apply/ — Student applies to a job.
    """
    serializer_class = ApplicationCreateSerializer
    permission_classes = [permissions.IsAuthenticated, IsStudent]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def create(self, request, *args, **kwargs):
        job_id = self.kwargs.get('job_id')
        job = get_object_or_404(Job, id=job_id)

        # Validate: job must be active
        if job.status != Job.Status.ACTIVE:
            return Response(
                {'error': 'This job is no longer accepting applications.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate: job must not be expired
        if job.is_expired:
            return Response(
                {'error': 'This job posting has expired.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        student_profile = get_object_or_404(StudentProfile, user=request.user)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            serializer.save(job=job, student=student_profile)
        except IntegrityError:
            return Response(
                {'error': 'You have already applied to this job.'},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MyApplicationsListView(generics.ListAPIView):
    """
    GET /api/jobs/my-applications/ — Student's own applications.
    """
    serializer_class = ApplicationListSerializer
    permission_classes = [permissions.IsAuthenticated, IsStudent]
    pagination_class = StandardPagination

    def get_queryset(self):
        return (
            Application.objects
            .filter(student__user=self.request.user)
            .select_related('job', 'job__employer', 'student', 'student__user')
        )


class JobApplicationsListView(generics.ListAPIView):
    """
    GET /api/jobs/<uuid>/applications/ — Employer views applications for their job.
    """
    serializer_class = ApplicationListSerializer
    permission_classes = [permissions.IsAuthenticated, IsEmployer]
    pagination_class = StandardPagination

    def get_queryset(self):
        job_id = self.kwargs.get('job_id')
        job = get_object_or_404(Job, id=job_id)

        # Ensure the employer owns this job
        if job.employer.user != self.request.user:
            return Application.objects.none()

        qs = (
            Application.objects
            .filter(job=job)
            .select_related('student', 'student__user', 'job', 'job__employer')
        )

        # Filter by application status
        app_status = self.request.query_params.get('status')
        if app_status:
            qs = qs.filter(status=app_status)

        return qs


class ApplicationDetailView(generics.RetrieveAPIView):
    """
    GET /api/jobs/applications/<uuid>/ — View single application detail.
    Accessible by: the student who applied OR the employer who owns the job.
    """
    serializer_class = ApplicationDetailSerializer
    permission_classes = [permissions.IsAuthenticated, IsApplicationOwnerOrJobOwner]
    queryset = Application.objects.select_related(
        'job', 'job__employer', 'job__employer__user',
        'student', 'student__user',
    )


class ApplicationStatusUpdateView(generics.UpdateAPIView):
    """
    PATCH /api/jobs/applications/<uuid>/status/ — Employer updates application status.
    """
    serializer_class = ApplicationStatusUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, IsEmployer]
    queryset = Application.objects.select_related('job', 'job__employer', 'job__employer__user')
    http_method_names = ['patch']  # Only PATCH allowed

    def get_object(self):
        obj = super().get_object()
        # Ensure employer owns the job this application belongs to
        if obj.job.employer.user != self.request.user:
            self.permission_denied(self.request, message='You can only manage applications for your own jobs.')
        return obj


class WithdrawApplicationView(generics.DestroyAPIView):
    """
    DELETE /api/jobs/applications/<uuid>/withdraw/ — Student withdraws their application.
    """
    permission_classes = [permissions.IsAuthenticated, IsStudent]

    def get_queryset(self):
        return Application.objects.filter(student__user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        application = self.get_object()

        # Can only withdraw pending or reviewing applications
        if application.status not in (Application.Status.PENDING, Application.Status.REVIEWING):
            return Response(
                {'error': f'Cannot withdraw an application with status "{application.get_status_display()}".'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        application.status = Application.Status.WITHDRAWN
        application.save()
        return Response(
            {'message': 'Application withdrawn successfully.'},
            status=status.HTTP_200_OK,
        )


# ═══════════════════════════════════════════════════════════════
#  SAVED JOBS VIEWS
# ═══════════════════════════════════════════════════════════════

class SavedJobsListView(generics.ListAPIView):
    """
    GET /api/jobs/saved/ — Student's saved/bookmarked jobs.
    """
    serializer_class = SavedJobSerializer
    permission_classes = [permissions.IsAuthenticated, IsStudent]
    pagination_class = StandardPagination

    def get_queryset(self):
        return (
            SavedJob.objects
            .filter(student__user=self.request.user)
            .select_related('job', 'job__employer', 'job__employer__user')
            .prefetch_related('job__skills')
        )


class SaveJobView(generics.CreateAPIView):
    """
    POST /api/jobs/<uuid>/save/ — Student saves a job.
    """
    permission_classes = [permissions.IsAuthenticated, IsStudent]

    def create(self, request, *args, **kwargs):
        job_id = self.kwargs.get('job_id')
        job = get_object_or_404(Job, id=job_id)
        student_profile = get_object_or_404(StudentProfile, user=request.user)

        try:
            SavedJob.objects.create(student=student_profile, job=job)
        except IntegrityError:
            return Response(
                {'error': 'Job already saved.'},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            {'message': 'Job saved successfully.'},
            status=status.HTTP_201_CREATED,
        )


class UnsaveJobView(generics.DestroyAPIView):
    """
    DELETE /api/jobs/<uuid>/unsave/ — Student removes a saved job.
    """
    permission_classes = [permissions.IsAuthenticated, IsStudent]

    def destroy(self, request, *args, **kwargs):
        job_id = self.kwargs.get('job_id')
        student_profile = get_object_or_404(StudentProfile, user=request.user)
        deleted, _ = SavedJob.objects.filter(student=student_profile, job_id=job_id).delete()

        if not deleted:
            return Response(
                {'error': 'Job was not saved.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {'message': 'Job unsaved successfully.'},
            status=status.HTTP_200_OK,
        )


# ═══════════════════════════════════════════════════════════════
#  REPORTING ENDPOINTS
# ═══════════════════════════════════════════════════════════════

class ReportJobView(generics.CreateAPIView):
    """
    POST /api/jobs/<uuid>/report/
    Reports a job for spam, misleading content, etc.
    """
    serializer_class = JobReportSerializer
    # Custom IsNotJobOwner to stop employers from reporting their own job (though mostly a logical edge case)
    permission_classes = [permissions.IsAuthenticated, IsNotJobOwner]

    def perform_create(self, serializer):
        job_id = self.kwargs['pk']
        job = get_object_or_404(Job, pk=job_id)
        
        # Check permissions explicitly as it's a create view acting on an object param
        self.check_object_permissions(self.request, job)

        # Check if already reported
        if JobReport.objects.filter(job=job, reporter=self.request.user).exists():
            from rest_framework.exceptions import APIException
            class Conflict(APIException):
                status_code = status.HTTP_409_CONFLICT
                default_detail = 'You have already reported this job.'

            raise Conflict()

        # Save and process auto-flag logic
        reason = serializer.validated_data.get('reason')
        details = serializer.validated_data.get('details', '')
        
        process_job_report(
            job=job,
            reporter=self.request.user,
            reason=reason,
            details=details
        )
        
        serializer.instance = JobReport.objects.get(job=job, reporter=self.request.user)
