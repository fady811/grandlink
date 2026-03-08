from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from authentication.models import User
from profiles.models import StudentProfile, EmployerProfile
from .models import Job, Application, Skill
from django.core.files.uploadedfile import SimpleUploadedFile
import uuid

class JobsPermissionsTests(APITestCase):
    def setUp(self):
        self.student_user = User.objects.create_user(email='student@example.com', password='Password123!', role='student', is_active=True)
        self.employer_user = User.objects.create_user(email='employer@example.com', password='Password123!', role='employer', is_active=True)
        
        # Ensure profiles exist
        self.student_profile = StudentProfile.objects.get(user=self.student_user)
        self.employer_profile = EmployerProfile.objects.get(user=self.employer_user)
        self.employer_profile.is_verified = True
        self.employer_profile.save()

        self.skill = Skill.objects.create(name='Python')
        
        self.job_list_create_url = reverse('job-list-create')

    def test_student_cannot_post_job(self):
        self.client.force_authenticate(user=self.student_user)
        job_data = {
            'title': 'Hack Entry',
            'description': 'Description',
            'work_type': 'full_time',
            'experience_level': 'entry',
        }
        response = self.client.post(self.job_list_create_url, job_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_employer_cannot_apply_to_job(self):
        job = Job.objects.create(employer=self.employer_profile, title='Dev Job', description='Desc', status='active')
        self.client.force_authenticate(user=self.employer_user)
        # Apply through direct ID lookup to skip missing kwarg issues
        apply_url = reverse('apply-to-job', kwargs={'job_id': job.id})
        response = self.client.post(apply_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_application_lifecycle(self):
        # 1. Employer creates job
        job = Job.objects.create(employer=self.employer_profile, title='Dev Job', description='Desc', status='active')
        
        # 2. Student applies
        self.client.force_authenticate(user=self.student_user)
        apply_url = reverse('apply-to-job', kwargs={'job_id': job.id})
        resume = SimpleUploadedFile("resume.pdf", b"pdf content", content_type="application/pdf")
        response = self.client.post(apply_url, {'resume': resume}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        application_id = response.data['id']

        # 3. Withdraw (while pending)
        withdraw_url = reverse('withdraw-application', kwargs={'pk': application_id})
        response = self.client.delete(withdraw_url)
        # Verify status 200 and data update
        self.assertEqual(response.status_code, status.HTTP_200_OK, f"Expected 200, got {response.status_code}: {response.data}")
        application = Application.objects.get(id=application_id)
        self.assertEqual(application.status, 'withdrawn')

        # 4. Reset to 'pending' manually to test employer status update
        application.status = 'pending'
        application.save()
        self.client.force_authenticate(user=self.employer_user)
        update_url = reverse('application-status-update', kwargs={'pk': application_id})
        response = self.client.patch(update_url, {'status': 'interview'})
        self.assertEqual(response.status_code, status.HTTP_200_OK, f"Expected 200, got {response.status_code}: {response.data}")
        application.refresh_from_db()
        self.assertEqual(application.status, 'interview')
