from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from authentication.models import User
from .models import StudentProfile, EmployerProfile

class ProfilePrivacyTests(APITestCase):
    def setUp(self):
        # 1. Create a student with private fields
        self.student_user = User.objects.create_user(
            email='student_private@example.com', password='Password123!', role='student', is_active=True
        )
        self.student_profile = StudentProfile.objects.get(user=self.student_user)
        self.student_profile.university = 'MIT'
        self.student_profile.major = 'CS'
        self.student_profile.gpa = 3.8
        self.student_profile.phone = '1234567890'
        # Private fields
        self.student_profile.hide_gpa = True
        self.student_profile.hide_phone = True
        self.student_profile.is_profile_public = True # but hidden fields should be hidden
        self.student_profile.save()

        # 2. Create another student as a viewer
        self.viewer_user = User.objects.create_user(
            email='viewer@example.com', password='Password123!', role='student', is_active=True
        )

        # URL for viewing the profile by user ID
        self.profile_lookup_url = reverse('student-profile-by-user', kwargs={'user_id': self.student_user.id})

    def test_owner_sees_all_fields(self):
        self.client.force_authenticate(user=self.student_user)
        # Use the ID lookup even for own profile
        response = self.client.get(self.profile_lookup_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(float(response.data['gpa']), 3.8)
        self.assertEqual(response.data['phone'], '1234567890')

    def test_other_user_cannot_see_hidden_fields(self):
        self.client.force_authenticate(user=self.viewer_user)
        response = self.client.get(self.profile_lookup_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Hidden fields should be None
        self.assertIsNone(response.data.get('gpa'))
        self.assertIsNone(response.data.get('phone'))
        # But public fields are fine
        self.assertEqual(response.data['university'], 'MIT')

    def test_private_profile_visibility(self):
        self.student_profile.is_profile_public = False
        self.student_profile.save()

        self.client.force_authenticate(user=self.viewer_user)
        response = self.client.get(self.profile_lookup_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Only allowed fields should be in the response
        # See StudentProfileSerializer.to_representation allowed list:
        # allowed = ['university', 'major', 'graduation_year', 'bio', 'skills']
        self.assertNotIn('phone', response.data)
        self.assertNotIn('gpa', response.data)
        self.assertEqual(response.data['university'], 'MIT')
