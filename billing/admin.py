from django.contrib import admin
from django.utils import timezone
from .models import SubscriptionPlan, EmployerSubscription, Invoice

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price_monthly', 'max_active_jobs', 'can_feature_jobs', 'is_active')
    list_filter = ('is_active', 'can_feature_jobs', 'has_ats_access')
    search_fields = ('name', 'description')


@admin.register(EmployerSubscription)
class EmployerSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('employer', 'plan_name', 'status', 'start_date', 'end_date', 'days_left')
    list_filter = ('status', 'plan', 'auto_renew')
    search_fields = ('employer__company_name', 'stripe_subscription_id')
    readonly_fields = ('days_left',)

    @admin.display(description='Plan')
    def plan_name(self, obj):
        return obj.plan.name if obj.plan else "Free Tier"

    @admin.display(description='Days Remaining')
    def days_left(self, obj):
        days = obj.days_remaining
        if days is None: return "∞"
        return days


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'employer', 'amount', 'status', 'issued_at', 'paid_at')
    list_filter = ('status', 'currency', 'issued_at')
    search_fields = ('employer__company_name', 'stripe_invoice_id', 'description')
    readonly_fields = ('issued_at',)
    actions = ['mark_as_paid']

    @admin.action(description='✅ Mark selected invoices as Paid')
    def mark_as_paid(self, request, queryset):
        queryset.update(status=Invoice.Status.PAID, paid_at=timezone.now())
        self.message_user(request, f"{queryset.count()} invoice(s) marked as paid.")
