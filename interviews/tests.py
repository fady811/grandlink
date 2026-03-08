from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from authentication.models import User
from profiles.models import StudentProfile, EmployerProfile
from jobs.models import Job, Application
from .models import Interview, InterviewFeedback
from django.utils import timezone
from datetime import timedelta


class InterviewManagementTests(APITestCase):
    """Full test suite for the interview management app."""

    def setUp(self):
        # ── Users ────────────────────────────────────────────────
        self.employer_user = User.objects.create_user(
            email='employer@test.com', password='Pass1234!', role='employer', is_active=True,
        )
        self.student_user = User.objects.create_user(
            email='student@test.com', password='Pass1234!', role='student', is_active=True,
        )
        self.other_employer = User.objects.create_user(
            email='other_employer@test.com', password='Pass1234!', role='employer', is_active=True,
        )

        # ── Profiles ────────────────────────────────────────────
        self.employer_profile = EmployerProfile.objects.get(user=self.employer_user)
        self.employer_profile.company_name = 'Acme Corp'
        self.employer_profile.is_verified = True
        self.employer_profile.save()

        self.student_profile = StudentProfile.objects.get(user=self.student_user)

        # ── Job + Application ───────────────────────────────────
        self.job = Job.objects.create(
            employer=self.employer_profile,
            title='Backend Developer',
            description='Build APIs',
            status='active',
        )
        self.application = Application.objects.create(
            job=self.job,
            student=self.student_profile,
            status='interview',
        )

        # ── URLs ────────────────────────────────────────────────
        self.list_url = reverse('interview-list-create')
        self.upcoming_url = reverse('interview-upcoming')
        self.stats_url = reverse('interview-stats')

        # ── Shared interview data ───────────────────────────────
        self.interview_data = {
            'application_id': str(self.application.id),
            'title': 'Technical Round 1',
            'description': 'Data structures & algorithms',
            'interview_type': 'video',
            'scheduled_at': (timezone.now() + timedelta(days=3)).isoformat(),
            'duration_minutes': 60,
            'meeting_link': 'https://meet.google.com/abc-def-ghi',
        }

    # ═══════════════════════════════════════════════════════════
    #  SCHEDULING
    # ═══════════════════════════════════════════════════════════

    def test_employer_can_schedule_interview(self):
        self.client.force_authenticate(user=self.employer_user)
        response = self.client.post(self.list_url, self.interview_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Interview.objects.count(), 1)
        interview = Interview.objects.first()
        self.assertEqual(interview.title, 'Technical Round 1')
        self.assertEqual(interview.status, 'scheduled')

    def test_student_cannot_schedule_interview(self):
        self.client.force_authenticate(user=self.student_user)
        response = self.client.post(self.list_url, self.interview_data)
        # Student is blocked — either 403 (permission) or 400 (serializer validation)
        self.assertIn(response.status_code, (status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN))

    def test_other_employer_cannot_schedule_for_others_job(self):
        self.client.force_authenticate(user=self.other_employer)
        response = self.client.post(self.list_url, self.interview_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_video_interview_requires_meeting_link(self):
        self.client.force_authenticate(user=self.employer_user)
        data = self.interview_data.copy()
        data['meeting_link'] = ''
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_past_date_rejected(self):
        self.client.force_authenticate(user=self.employer_user)
        data = self.interview_data.copy()
        data['scheduled_at'] = (timezone.now() - timedelta(days=1)).isoformat()
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ═══════════════════════════════════════════════════════════
    #  LISTING & DETAIL
    # ═══════════════════════════════════════════════════════════

    def _create_interview(self):
        return Interview.objects.create(
            application=self.application,
            scheduled_by=self.employer_user,
            title='Round 1',
            interview_type='video',
            scheduled_at=timezone.now() + timedelta(days=2),
            duration_minutes=45,
            meeting_link='https://zoom.us/j/123',
        )

    def test_employer_sees_own_interviews(self):
        self._create_interview()
        self.client.force_authenticate(user=self.employer_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_student_sees_own_interviews(self):
        self._create_interview()
        self.client.force_authenticate(user=self.student_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_other_employer_cannot_see_interviews(self):
        self._create_interview()
        self.client.force_authenticate(user=self.other_employer)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)

    def test_detail_view(self):
        interview = self._create_interview()
        self.client.force_authenticate(user=self.employer_user)
        url = reverse('interview-detail', kwargs={'pk': interview.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Round 1')

    # ═══════════════════════════════════════════════════════════
    #  UPDATE & CANCEL
    # ═══════════════════════════════════════════════════════════

    def test_employer_can_reschedule(self):
        interview = self._create_interview()
        self.client.force_authenticate(user=self.employer_user)
        url = reverse('interview-detail', kwargs={'pk': interview.id})
        new_time = (timezone.now() + timedelta(days=5)).isoformat()
        response = self.client.patch(url, {'scheduled_at': new_time})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_student_cannot_update_interview(self):
        interview = self._create_interview()
        self.client.force_authenticate(user=self.student_user)
        url = reverse('interview-detail', kwargs={'pk': interview.id})
        response = self.client.patch(url, {'title': 'Hacked'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cancel_interview(self):
        interview = self._create_interview()
        self.client.force_authenticate(user=self.employer_user)
        url = reverse('interview-detail', kwargs={'pk': interview.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        interview.refresh_from_db()
        self.assertEqual(interview.status, 'cancelled')

    # ═══════════════════════════════════════════════════════════
    #  STUDENT CONFIRMATION
    # ═══════════════════════════════════════════════════════════

    def test_student_can_confirm(self):
        interview = self._create_interview()
        self.client.force_authenticate(user=self.student_user)
        url = reverse('interview-confirm', kwargs={'pk': interview.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        interview.refresh_from_db()
        self.assertEqual(interview.status, 'confirmed')

    def test_employer_cannot_confirm(self):
        interview = self._create_interview()
        self.client.force_authenticate(user=self.employer_user)
        url = reverse('interview-confirm', kwargs={'pk': interview.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ═══════════════════════════════════════════════════════════
    #  FEEDBACK
    # ═══════════════════════════════════════════════════════════

    def test_employer_can_submit_feedback(self):
        interview = self._create_interview()
        interview.status = 'completed'
        interview.save()

        self.client.force_authenticate(user=self.employer_user)
        url = reverse('interview-feedback-create', kwargs={'pk': interview.id})
        feedback_data = {
            'rating': 4,
            'technical_rating': 5,
            'communication_rating': 3,
            'strengths': 'Strong algorithmics',
            'weaknesses': 'Could improve system design',
            'recommendation': 'yes',
        }
        response = self.client.post(url, feedback_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(InterviewFeedback.objects.count(), 1)

    def test_feedback_requires_completed_status(self):
        interview = self._create_interview()  # Status = scheduled
        self.client.force_authenticate(user=self.employer_user)
        url = reverse('interview-feedback-create', kwargs={'pk': interview.id})
        response = self.client.post(url, {
            'rating': 3, 'recommendation': 'maybe',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_feedback_rejected(self):
        interview = self._create_interview()
        interview.status = 'completed'
        interview.save()
        InterviewFeedback.objects.create(
            interview=interview, submitted_by=self.employer_user,
            rating=4, recommendation='yes',
        )

        self.client.force_authenticate(user=self.employer_user)
        url = reverse('interview-feedback-create', kwargs={'pk': interview.id})
        response = self.client.post(url, {
            'rating': 5, 'recommendation': 'strong_yes',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ═══════════════════════════════════════════════════════════
    #  DASHBOARD
    # ═══════════════════════════════════════════════════════════

    def test_upcoming_interviews(self):
        self._create_interview()
        self.client.force_authenticate(user=self.employer_user)
        response = self.client.get(self.upcoming_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_stats_endpoint(self):
        self._create_interview()
        self.client.force_authenticate(user=self.employer_user)
        response = self.client.get(self.stats_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_interviews'], 1)
        self.assertEqual(response.data['scheduled'], 1)
