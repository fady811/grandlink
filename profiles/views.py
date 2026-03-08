from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from .models import StudentProfile, EmployerProfile
from .serializers import StudentProfileSerializer, EmployerProfileSerializer
from authentication.models import User

class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Allow viewing for any authenticated user, but restrict editing to owner/staff
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_staff or obj.user == request.user

class StudentProfileDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = StudentProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    queryset = StudentProfile.objects.all()

    def get_object(self):
        # Allow retrieval by user_id or current user
        user_id = self.kwargs.get('user_id')
        if user_id:
            user = get_object_or_404(User, id=user_id)
            profile = get_object_or_404(StudentProfile, user=user)
        else:
            profile = get_object_or_404(StudentProfile, user=self.request.user)
        self.check_object_permissions(self.request, profile)
        return profile

    def perform_update(self, serializer):
        serializer.save()


class EmployerProfileDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = EmployerProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    queryset = EmployerProfile.objects.all()

    def get_object(self):
        user_id = self.kwargs.get('user_id')
        if user_id:
            user = get_object_or_404(User, id=user_id)
            profile = get_object_or_404(EmployerProfile, user=user)
        else:
            profile = get_object_or_404(EmployerProfile, user=self.request.user)
        self.check_object_permissions(self.request, profile)
        return profile

    def perform_update(self, serializer):
        serializer.save()


class PrivacySettingsView(generics.GenericAPIView):
    """Endpoint to update privacy flags for the authenticated user's profile"""
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request):
        user = request.user
        if user.role == 'student':
            profile = get_object_or_404(StudentProfile, user=user)
            serializer = StudentProfileSerializer(profile, data=request.data, partial=True, context={'request': request})
        elif user.role == 'employer':
            profile = get_object_or_404(EmployerProfile, user=user)
            serializer = EmployerProfileSerializer(profile, data=request.data, partial=True, context={'request': request})
        else:
            return Response({"error": "Invalid role."}, status=status.HTTP_400_BAD_REQUEST)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)