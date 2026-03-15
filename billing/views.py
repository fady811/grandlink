from rest_framework import generics, permissions, response, status
from .models import SubscriptionPlan, EmployerSubscription
from .serializers import SubscriptionPlanSerializer, EmployerSubscriptionSerializer

class SubscriptionPlanListView(generics.ListAPIView):
    """
    GET /api/billing/plans/ — public endpoint listing active plans
    """
    queryset = SubscriptionPlan.objects.filter(is_active=True)
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [permissions.AllowAny]


class MySubscriptionView(generics.RetrieveAPIView):
    """
    GET /api/billing/my-subscription/ — employer's current subscription
    """
    serializer_class = EmployerSubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # We need to ensure the user has an employer profile
        try:
            employer = self.request.user.employer_profile
            subscription, created = EmployerSubscription.objects.get_or_create(
                employer=employer
            )
            return subscription
        except Exception:
            # Fallback for students or users without profiles
            return None

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance is None:
            return response.Response(
                {"detail": "Only employers can have subscriptions."},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = self.get_serializer(instance)
        return response.Response(serializer.data)
