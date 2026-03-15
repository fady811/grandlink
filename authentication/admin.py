from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.utils import timezone
from .models import User, OTPVerification


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Full-featured User admin with proper fieldsets,
    inheriting from Django's UserAdmin for password handling.
    """
    # ── List View ────────────────────────────────────────────────
    list_display = (
        'email', 'role_badge', 'is_active_badge',
        'date_joined', 'last_login', 'deletion_status',
    )
    list_filter = ('role', 'is_active', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    list_per_page = 25
    date_hierarchy = 'date_joined'

    # ── Detail View ──────────────────────────────────────────────
    fieldsets = (
        ('Account Information', {
            'fields': ('email', 'password'),
        }),
        ('Personal Info', {
            'fields': ('first_name', 'last_name'),
        }),
        ('Role & Permissions', {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined', 'deletion_date'),
            'classes': ('collapse',),
        }),
    )

    add_fieldsets = (
        ('Create New User', {
            'classes': ('wide',),
            'fields': ('email', 'role', 'password1', 'password2', 'is_active', 'is_staff'),
        }),
    )

    readonly_fields = ('date_joined', 'last_login')
    filter_horizontal = ('groups', 'user_permissions')

    # ── Custom Columns ───────────────────────────────────────────
    @admin.display(description='Role', ordering='role')
    def role_badge(self, obj):
        colors = {
            'student': ('#059669', '#ecfdf5'),
            'employer': ('#2563eb', '#eff6ff'),
            'admin': ('#dc2626', '#fef2f2'),
        }
        text_color, bg_color = colors.get(obj.role, ('#6b7280', '#f3f4f6'))
        return format_html(
            '<span style="background:{}; color:{}; padding:3px 10px; '
            'border-radius:12px; font-size:0.72rem; font-weight:600; '
            'text-transform:uppercase; letter-spacing:0.5px;">{}</span>',
            bg_color, text_color, obj.get_role_display(),
        )

    @admin.display(description='Status', boolean=True, ordering='is_active')
    def is_active_badge(self, obj):
        return obj.is_active

    @admin.display(description='Deletion')
    def deletion_status(self, obj):
        if obj.deletion_date:
            days_left = 30 - (timezone.now() - obj.deletion_date).days
            if days_left > 0:
                return format_html(
                    '<span style="color:#d97706; font-size:0.78rem;">{}</span>',
                    '⏳ {} days left'.format(days_left),
                )
            return format_html(
                '<span style="color:#dc2626; font-size:0.78rem;">{}</span>',
                '🗑️ Ready to purge',
            )
        return '—'

    # ── Actions ──────────────────────────────────────────────────
    actions = ['activate_users', 'deactivate_users', 'send_announcement']

    @admin.action(description='✅ Activate selected users')
    def activate_users(self, request, queryset):
        count = queryset.update(is_active=True, deletion_date=None)
        self.message_user(request, f'{count} user(s) activated successfully.')

    @admin.action(description='🚫 Deactivate selected users')
    def deactivate_users(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} user(s) deactivated.')


    @admin.action(description='📢 Send announcement to selected users')
    def send_announcement(self, request, queryset):
        """
        Intermediate page for sending announcements.
        """
        from django.template.response import TemplateResponse
        from notifications.tasks import send_bulk_announcement

        if 'apply' in request.POST:
            subject = request.POST.get('subject', '').strip()
            message = request.POST.get('message', '').strip()
            
            if not subject or not message:
                self.message_user(request, "Subject and message are required.", level='error')
                return None

            user_ids = list(queryset.values_list('pk', flat=True))
            send_bulk_announcement.delay(user_ids, subject, message)
            
            self.message_user(request, f"Announcement started for {len(queryset)} users.")
            return None

        return TemplateResponse(
            request,
            'admin/notifications/send_announcement.html',
            context={
                'queryset': queryset,
                'action_checkbox_name': admin.helpers.ACTION_CHECKBOX_NAME,
                **self.admin_site.each_context(request),
            }
        )


@admin.register(OTPVerification)
class OTPVerificationAdmin(admin.ModelAdmin):
    """OTP management with validity status."""

    list_display = ('user', 'code', 'validity_status', 'attempt_count', 'created_at', 'expires_at')
    list_filter = ('is_used',)
    search_fields = ('user__email', 'code')
    readonly_fields = ('id', 'created_at')
    ordering = ('-created_at',)
    list_per_page = 30

    @admin.display(description='Status')
    def validity_status(self, obj):
        if obj.is_used:
            return format_html(
                '<span style="color:#6b7280; font-size:0.78rem;">{}</span>',
                '✓ Used',
            )
        if obj.expires_at < timezone.now():
            return format_html(
                '<span style="color:#dc2626; font-size:0.78rem;">{}</span>',
                '✗ Expired',
            )
        return format_html(
            '<span style="color:#059669; font-size:0.78rem;">{}</span>',
            '● Active',
        )

    actions = ['clear_expired_otps']

    @admin.action(description='🧹 Clear all expired / used OTPs')
    def clear_expired_otps(self, request, queryset):
        from django.db.models import Q
        count, _ = OTPVerification.objects.filter(
            Q(is_used=True) | Q(expires_at__lt=timezone.now())
        ).delete()
        self.message_user(request, f'{count} expired/used OTP(s) cleaned up.')