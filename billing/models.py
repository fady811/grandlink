import uuid
from django.db import models
from django.utils import timezone
from profiles.models import EmployerProfile

class SubscriptionPlan(models.Model):
    """
    Available subscription tiers for employers.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    price_monthly = models.DecimalField(max_digits=10, decimal_places=2)
    price_yearly = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Limits and Features
    max_active_jobs = models.PositiveIntegerField(
        help_text="Maximum number of active job postings allowed at once."
    )
    can_feature_jobs = models.BooleanField(
        default=False,
        help_text="Whether this plan allows featuring jobs."
    )
    has_ats_access = models.BooleanField(
        default=False,
        help_text="Whether this plan gives access to ATS tools."
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} (${self.price_monthly}/mo)"


class EmployerSubscription(models.Model):
    """
    Current subscription status for an employer.
    """
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        CANCELLED = 'cancelled', 'Cancelled'
        EXPIRED = 'expired', 'Expired'
        TRIAL = 'trial', 'Trial'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employer = models.OneToOneField(
        EmployerProfile,
        on_delete=models.CASCADE,
        related_name='subscription'
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subscriptions',
        help_text="Null plan represents the Free Tier."
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.TRIAL
    )
    
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)
    auto_renew = models.BooleanField(default=True)
    
    # Stripe hooks
    stripe_subscription_id = models.CharField(max_length=255, null=True, blank=True)
    
    def __str__(self):
        plan_name = self.plan.name if self.plan else "Free"
        return f"{self.employer.company_name} - {plan_name} ({self.get_status_display()})"

    @property
    def is_valid(self):
        """Checks if subscription is active/trial and not expired."""
        if self.status not in [self.Status.ACTIVE, self.Status.TRIAL]:
            return False
        if self.end_date and self.end_date < timezone.now():
            return False
        return True

    @property
    def days_remaining(self):
        """Computed field for admin visibility."""
        if not self.end_date:
            return None
        delta = self.end_date - timezone.now()
        return max(0, delta.days)


class Invoice(models.Model):
    """
    Record of payment or billing event.
    """
    class Status(models.TextChoices):
        PAID = 'paid', 'Paid'
        PENDING = 'pending', 'Pending'
        FAILED = 'failed', 'Failed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employer = models.ForeignKey(
        EmployerProfile,
        on_delete=models.CASCADE,
        related_name='invoices'
    )
    subscription = models.ForeignKey(
        EmployerSubscription,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices'
    )
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    
    description = models.TextField(help_text="Description for the invoice PDF/receipt")
    issued_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    # Stripe hooks
    stripe_invoice_id = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"Invoice {self.id} - {self.employer.company_name} (${self.amount})"

    class Meta:
        ordering = ['-issued_at']
