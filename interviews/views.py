from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.db.models import Avg, Count, Q
from datetime import timedelta

from .models import Interview, InterviewFeedback
from .serializers import (
    InterviewCreateSerializer,
    InterviewListSerializer,
    InterviewDetailSerializer,
    InterviewUpdateSerializer,
    InterviewFeedbackSerializer,
    InterviewStatsSerializer,
)
from .permissions import IsInterviewParticipant, IsInterviewEmployer, IsInterviewStudent
from jobs.permissions import IsEmployer, IsStudent


# ═══════════════════════════════════════════════════════════════
#  INTERVIEW CRUD
# ═══════════════════════════════════════════════════════════════

class InterviewListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/interviews/       — List interviews (employer sees own jobs', student sees own)
    POST /api/interviews/       — Schedule a new interview (employer only)
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return InterviewCreateSerializer
        return InterviewListSerializer

    def get_queryset(self):
        user = self.request.user
        qs = Interview.objects.select_related(
            'application__job__employer__user',
            'application__student__user',
        )

        if user.role == 'employer':
            qs = qs.filter(application__job__employer__user=user)
        elif user.role == 'student':
            qs = qs.filter(application__student__user=user)
        else:
            # Admin sees all
            pass

        # ── Filters ──────────────────────────────────────────────
        interview_status = self.request.query_params.get('status')
        if interview_status:
            qs = qs.filter(status=interview_status)

        job_id = self.request.query_params.get('job_id')
        if job_id:
            qs = qs.filter(application__job__id=job_id)

        application_id = self.request.query_params.get('application_id')
        if application_id:
            qs = qs.filter(application__id=application_id)

        return qs

    def perform_create(self, serializer):
        # Only employers can create
        if self.request.user.role != 'employer':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only employers can schedule interviews.")
        serializer.save()


class InterviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/interviews/<id>/  — View interview detail
    PATCH  /api/interviews/<id>/  — Update / reschedule (employer only)
    DELETE /api/interviews/<id>/  — Cancel interview (employer only)
    """
    permission_classes = [permissions.IsAuthenticated, IsInterviewParticipant]
    queryset = Interview.objects.select_related(
        'application__job__employer__user',
        'application__student__user',
    )

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return InterviewUpdateSerializer
        return InterviewDetailSerializer

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        # Write operations require employer ownership
        if request.method not in permissions.SAFE_METHODS:
            if not (request.user.is_staff or obj.application.job.employer.user == request.user):
                self.permission_denied(
                    request,
                    message='Only the employer who posted this job can modify interviews.',
                )

    def perform_destroy(self, instance):
        """Cancelling = setting status to cancelled, not hard deleting."""
        instance.status = Interview.Status.CANCELLED
        if not instance.cancellation_reason:
            instance.cancellation_reason = 'Cancelled by employer.'
        instance.save()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.status in (Interview.Status.COMPLETED, Interview.Status.CANCELLED):
            return Response(
                {"error": f"Cannot cancel an interview that is already {instance.get_status_display()}."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        self.perform_destroy(instance)
        return Response(
            {"message": "Interview cancelled.", "status": instance.status},
            status=status.HTTP_200_OK,
        )


# ═══════════════════════════════════════════════════════════════
#  STUDENT CONFIRMATION
# ═══════════════════════════════════════════════════════════════

class InterviewConfirmView(generics.GenericAPIView):
    """
    POST /api/interviews/<id>/confirm/ — Student confirms attendance.
    """
    permission_classes = [permissions.IsAuthenticated, IsInterviewStudent]
    queryset = Interview.objects.select_related(
        'application__student__user',
        'application__job__employer__user',
    )

    def post(self, request, pk):
        interview = self.get_object()

        if interview.status != Interview.Status.SCHEDULED:
            return Response(
                {"error": f"Cannot confirm an interview with status '{interview.get_status_display()}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        interview.status = Interview.Status.CONFIRMED
        interview.save(update_fields=['status', 'updated_at'])

        return Response(
            {
                "message": "Interview confirmed.",
                "interview_id": str(interview.id),
                "status": interview.status,
            },
            status=status.HTTP_200_OK,
        )


# ═══════════════════════════════════════════════════════════════
#  FEEDBACK
# ═══════════════════════════════════════════════════════════════

class InterviewFeedbackCreateView(generics.CreateAPIView):
    """
    POST /api/interviews/<id>/feedback/ — Employer submits post-interview feedback.
    """
    serializer_class = InterviewFeedbackSerializer
    permission_classes = [permissions.IsAuthenticated, IsEmployer]

    def perform_create(self, serializer):
        interview = Interview.objects.select_related(
            'application__job__employer__user'
        ).get(pk=self.kwargs['pk'])

        # Verify employer ownership
        if interview.application.job.employer.user != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only submit feedback for your own interviews.")

        if interview.status != Interview.Status.COMPLETED:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Feedback can only be submitted for completed interviews.")

        if hasattr(interview, 'feedback'):
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Feedback has already been submitted for this interview.")

        serializer.save(
            interview=interview,
            submitted_by=self.request.user,
        )


class InterviewFeedbackDetailView(generics.RetrieveAPIView):
    """
    GET /api/interviews/<id>/feedback/ — View feedback for an interview.
    """
    serializer_class = InterviewFeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        interview = Interview.objects.select_related(
            'application__job__employer__user',
            'application__student__user',
        ).get(pk=self.kwargs['pk'])

        user = self.request.user
        # Only employer who owns the job can see feedback
        # (Students should NOT see raw interview feedback)
        if not (
            user.is_staff
            or interview.application.job.employer.user == user
        ):
            self.permission_denied(
                self.request,
                message='Only the employer can view interview feedback.',
            )

        try:
            return interview.feedback
        except InterviewFeedback.DoesNotExist:
            from django.http import Http404
            raise Http404("No feedback submitted yet.")


# ═══════════════════════════════════════════════════════════════
#  DASHBOARD VIEWS
# ═══════════════════════════════════════════════════════════════

class UpcomingInterviewsView(generics.ListAPIView):
    """
    GET /api/interviews/upcoming/ — Next 7 days of interviews.
    """
    serializer_class = InterviewListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        now = timezone.now()
        week_ahead = now + timedelta(days=7)

        qs = Interview.objects.select_related(
            'application__job__employer__user',
            'application__student__user',
        ).filter(
            scheduled_at__gte=now,
            scheduled_at__lte=week_ahead,
            status__in=[Interview.Status.SCHEDULED, Interview.Status.CONFIRMED],
        )

        if user.role == 'employer':
            qs = qs.filter(application__job__employer__user=user)
        elif user.role == 'student':
            qs = qs.filter(application__student__user=user)

        return qs


class InterviewStatsView(APIView):
    """
    GET /api/interviews/stats/ — Employer interview pipeline statistics.
    """
    permission_classes = [permissions.IsAuthenticated, IsEmployer]

    def get(self, request):
        user = request.user
        interviews = Interview.objects.filter(
            application__job__employer__user=user,
        )

        total = interviews.count()
        status_counts = interviews.values('status').annotate(count=Count('id'))
        status_map = {s['status']: s['count'] for s in status_counts}

        # Average rating from completed interviews with feedback
        avg_rating = InterviewFeedback.objects.filter(
            interview__application__job__employer__user=user,
        ).aggregate(avg=Avg('rating'))['avg']

        # Recommendation breakdown
        rec_counts = InterviewFeedback.objects.filter(
            interview__application__job__employer__user=user,
        ).values('recommendation').annotate(count=Count('id'))
        rec_map = {r['recommendation']: r['count'] for r in rec_counts}

        data = {
            'total_interviews': total,
            'scheduled': status_map.get('scheduled', 0),
            'confirmed': status_map.get('confirmed', 0),
            'completed': status_map.get('completed', 0),
            'cancelled': status_map.get('cancelled', 0),
            'no_show': status_map.get('no_show', 0),
            'avg_rating': round(avg_rating, 2) if avg_rating else None,
            'recommendation_breakdown': rec_map,
        }

        serializer = InterviewStatsSerializer(data)
        return Response(serializer.data)
