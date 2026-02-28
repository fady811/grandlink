from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import StudentProfile, EmployerProfile


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    """Student profile management with rich display."""

    # ── List View ────────────────────────────────────────────────
    list_display = (
        'get_email', 'university', 'major',
        'graduation_year', 'gpa_display', 'skills_preview',
        'privacy_status', 'created_at',
    )
    list_filter = ('is_profile_public', 'hide_gpa', 'graduation_year')
    search_fields = ('user__email', 'university', 'major')
    readonly_fields = ('id', 'created_at', 'updated_at', 'get_email')
    ordering = ('-created_at',)
    list_per_page = 25

    # ── Detail View ──────────────────────────────────────────────
    fieldsets = (
        ('Student', {
            'fields': ('id', 'user', 'get_email'),
        }),
        ('Academic Information', {
            'fields': ('university', 'major', 'graduation_year', 'gpa'),
        }),
        ('Profile Details', {
            'fields': ('bio', 'skills', 'phone', 'cv_file'),
        }),
        ('Privacy Settings', {
            'fields': ('is_profile_public', 'hide_gpa', 'hide_phone'),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    # ── Custom Columns ───────────────────────────────────────────
    @admin.display(description='Email', ordering='user__email')
    def get_email(self, obj):
        return obj.user.email

    @admin.display(description='GPA')
    def gpa_display(self, obj):
        if obj.gpa is None:
            return '—'
        color = '#059669' if obj.gpa >= 3.0 else '#d97706' if obj.gpa >= 2.0 else '#dc2626'
        return format_html(
            '<span style="color:{}; font-weight:600;">{}</span>',
            color, obj.gpa,
        )

    @admin.display(description='Skills')
    def skills_preview(self, obj):
        if not obj.skills:
            return '—'
        skills = obj.skills[:3]  # Show first 3
        parts = []
        for s in skills:
            parts.append(
                '<span style="background:#eef2ff; color:#4f46e5; padding:2px 8px; '
                'border-radius:10px; font-size:0.7rem; font-weight:500; '
                'margin-right:3px;">{}</span>'.format(s)
            )
        extra = len(obj.skills) - 3
        if extra > 0:
            parts.append('<span style="color:#9ca3af; font-size:0.72rem;">+{}</span>'.format(extra))
        return format_html('{}', ' '.join(parts))

    @admin.display(description='Privacy')
    def privacy_status(self, obj):
        if obj.is_profile_public:
            return format_html(
                '<span style="color:#059669; font-size:0.78rem;">{}</span>',
                '🌐 Public',
            )
        return format_html(
            '<span style="color:#d97706; font-size:0.78rem;">{}</span>',
            '🔒 Private',
        )


@admin.register(EmployerProfile)
class EmployerProfileAdmin(admin.ModelAdmin):
    """Employer profile management with verification workflow."""

    # ── List View ────────────────────────────────────────────────
    list_display = (
        'company_name', 'get_email', 'industry',
        'company_size', 'verification_badge',
        'privacy_status', 'created_at',
    )
    list_filter = ('is_verified', 'is_profile_public', 'industry')
    search_fields = ('company_name', 'user__email', 'industry')
    readonly_fields = ('id', 'created_at', 'updated_at', 'get_email', 'verification_date')
    ordering = ('-created_at',)
    list_per_page = 25

    # ── Detail View ──────────────────────────────────────────────
    fieldsets = (
        ('Account', {
            'fields': ('id', 'user', 'get_email'),
        }),
        ('Company Information', {
            'fields': ('company_name', 'industry', 'company_size', 'website', 'phone'),
        }),
        ('Verification', {
            'fields': ('is_verified', 'verified_by', 'verification_date'),
        }),
        ('Privacy Settings', {
            'fields': ('is_profile_public', 'hide_phone'),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    # ── Custom Columns ───────────────────────────────────────────
    @admin.display(description='Email', ordering='user__email')
    def get_email(self, obj):
        return obj.user.email

    @admin.display(description='Verified', ordering='is_verified')
    def verification_badge(self, obj):
        if obj.is_verified:
            return format_html(
                '<span style="background:#ecfdf5; color:#059669; padding:3px 10px; '
                'border-radius:12px; font-size:0.72rem; font-weight:600;">{}</span>',
                '✓ Verified',
            )
        return format_html(
            '<span style="background:#fef2f2; color:#dc2626; padding:3px 10px; '
            'border-radius:12px; font-size:0.72rem; font-weight:600;">{}</span>',
            '✗ Unverified',
        )

    @admin.display(description='Privacy')
    def privacy_status(self, obj):
        if obj.is_profile_public:
            return format_html(
                '<span style="color:#059669; font-size:0.78rem;">{}</span>',
                '🌐 Public',
            )
        return format_html(
            '<span style="color:#d97706; font-size:0.78rem;">{}</span>',
            '🔒 Private',
        )

    # ── Actions ──────────────────────────────────────────────────
    actions = ['verify_employers', 'unverify_employers']

    @admin.action(description='✅ Verify selected employers')
    def verify_employers(self, request, queryset):
        count = queryset.update(
            is_verified=True,
            verified_by=request.user,
            verification_date=timezone.now(),
        )
        self.message_user(request, f'{count} employer(s) verified successfully.')

    @admin.action(description='🚫 Revoke verification for selected employers')
    def unverify_employers(self, request, queryset):
        count = queryset.update(
            is_verified=False,
            verified_by=None,
            verification_date=None,
        )
        self.message_user(request, f'{count} employer(s) verification revoked.')