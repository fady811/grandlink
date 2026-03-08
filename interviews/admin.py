from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Interview, InterviewFeedback


# ═══════════════════════════════════════════════════════════════
#  INLINES
# ═══════════════════════════════════════════════════════════════

class InterviewFeedbackInline(admin.StackedInline):
    model = InterviewFeedback
    extra = 0
    readonly_fields = ('submitted_by', 'created_at')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


# ═══════════════════════════════════════════════════════════════
#  INTERVIEW ADMIN
# ═══════════════════════════════════════════════════════════════

@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'student_email', 'job_title', 'type_badge',
        'status_badge', 'scheduled_at_display', 'duration_minutes',
    )
    list_filter = ('status', 'interview_type', 'scheduled_at')
    search_fields = (
        'title',
        'application__student__user__email',
        'application__job__title',
        'application__job__employer__company_name',
    )
    ordering = ('-scheduled_at',)
    list_per_page = 25
    date_hierarchy = 'scheduled_at'
    readonly_fields = ('id', 'created_at', 'updated_at')
    inlines = [InterviewFeedbackInline]

    fieldsets = (
        ('Interview Details', {
            'fields': ('id', 'application', 'scheduled_by', 'title', 'description'),
        }),
        ('Schedule', {
            'fields': ('interview_type', 'scheduled_at', 'duration_minutes'),
        }),
        ('Location / Link', {
            'fields': ('location', 'meeting_link'),
            'classes': ('collapse',),
        }),
        ('Status', {
            'fields': ('status', 'cancellation_reason'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Student')
    def student_email(self, obj):
        return obj.application.student.user.email

    @admin.display(description='Job')
    def job_title(self, obj):
        return obj.application.job.title

    @admin.display(description='Type')
    def type_badge(self, obj):
        colors = {
            'in_person': ('#0369a1', '#e0f2fe'),
            'video': ('#7c3aed', '#f5f3ff'),
            'phone': ('#059669', '#ecfdf5'),
        }
        fg, bg = colors.get(obj.interview_type, ('#374151', '#f3f4f6'))
        return format_html(
            '<span style="background:{}; color:{}; padding:3px 10px; '
            'border-radius:12px; font-size:11px; font-weight:600;">{}</span>',
            bg, fg, obj.get_interview_type_display(),
        )

    @admin.display(description='Status')
    def status_badge(self, obj):
        colors = {
            'scheduled': ('#ca8a04', '#fefce8'),
            'confirmed': ('#0369a1', '#e0f2fe'),
            'completed': ('#059669', '#ecfdf5'),
            'cancelled': ('#dc2626', '#fef2f2'),
            'no_show': ('#9333ea', '#faf5ff'),
        }
        fg, bg = colors.get(obj.status, ('#374151', '#f3f4f6'))
        return format_html(
            '<span style="background:{}; color:{}; padding:3px 10px; '
            'border-radius:12px; font-size:11px; font-weight:600;">{}</span>',
            bg, fg, obj.get_status_display(),
        )

    @admin.display(description='Scheduled At')
    def scheduled_at_display(self, obj):
        now = timezone.now()
        if obj.scheduled_at < now and obj.status in ('scheduled', 'confirmed'):
            return format_html(
                '<span style="color: #dc2626; font-weight: 600;">{} ⚠️ OVERDUE</span>',
                obj.scheduled_at.strftime('%b %d, %Y %H:%M'),
            )
        return obj.scheduled_at.strftime('%b %d, %Y %H:%M')

    # ── Admin Actions ────────────────────────────────────────────
    @admin.action(description='Mark selected as Completed')
    def mark_completed(self, request, queryset):
        updated = queryset.filter(
            status__in=['scheduled', 'confirmed']
        ).update(status='completed')
        self.message_user(request, f"{updated} interview(s) marked as completed.")

    @admin.action(description='Mark selected as Cancelled')
    def mark_cancelled(self, request, queryset):
        updated = queryset.exclude(
            status__in=['completed', 'cancelled']
        ).update(status='cancelled', cancellation_reason='Cancelled by admin.')
        self.message_user(request, f"{updated} interview(s) cancelled.")

    actions = [mark_completed, mark_cancelled]


# ═══════════════════════════════════════════════════════════════
#  FEEDBACK ADMIN
# ═══════════════════════════════════════════════════════════════

@admin.register(InterviewFeedback)
class InterviewFeedbackAdmin(admin.ModelAdmin):
    list_display = (
        'interview_title', 'student_email', 'rating_stars',
        'recommendation_badge', 'submitted_by_email', 'created_at',
    )
    list_filter = ('recommendation', 'rating')
    search_fields = (
        'interview__title',
        'interview__application__student__user__email',
    )
    ordering = ('-created_at',)
    list_per_page = 25
    readonly_fields = ('id', 'created_at')

    @admin.display(description='Interview')
    def interview_title(self, obj):
        return obj.interview.title

    @admin.display(description='Student')
    def student_email(self, obj):
        return obj.interview.application.student.user.email

    @admin.display(description='Submitted By')
    def submitted_by_email(self, obj):
        return obj.submitted_by.email

    @admin.display(description='Rating')
    def rating_stars(self, obj):
        stars = '★' * obj.rating + '☆' * (5 - obj.rating)
        return format_html(
            '<span style="color: #f59e0b; font-size: 14px;">{}</span>',
            stars,
        )

    @admin.display(description='Recommendation')
    def recommendation_badge(self, obj):
        colors = {
            'strong_yes': ('#059669', '#ecfdf5'),
            'yes': ('#0369a1', '#e0f2fe'),
            'maybe': ('#ca8a04', '#fefce8'),
            'no': ('#dc2626', '#fef2f2'),
            'strong_no': ('#991b1b', '#fef2f2'),
        }
        fg, bg = colors.get(obj.recommendation, ('#374151', '#f3f4f6'))
        return format_html(
            '<span style="background:{}; color:{}; padding:3px 10px; '
            'border-radius:12px; font-size:11px; font-weight:600;">{}</span>',
            bg, fg, obj.get_recommendation_display(),
        )
