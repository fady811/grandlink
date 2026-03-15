from django.contrib import admin
from django.utils.html import format_html
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        'user_email', 'type_badge', 'message_preview',
        'read_badge', 'created_at',
    )
    list_filter = ('type', 'is_read', 'created_at')
    search_fields = ('user__email', 'message')
    readonly_fields = ('id', 'created_at')
    ordering = ('-created_at',)
    list_per_page = 30
    list_select_related = ('user',)

    fieldsets = (
        ('Notification', {
            'fields': ('id', 'user', 'type', 'message'),
        }),
        ('Reference', {
            'fields': ('related_object_id',),
            'classes': ('collapse',),
        }),
        ('State', {
            'fields': ('is_read', 'created_at'),
        }),
    )

    @admin.display(description='User', ordering='user__email')
    def user_email(self, obj):
        return obj.user.email

    @admin.display(description='Message')
    def message_preview(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message

    @admin.display(description='Type')
    def type_badge(self, obj):
        colors = {
            'application_received': ('#2563eb', '#eff6ff'),
            'application_status_changed': ('#7c3aed', '#f5f3ff'),
            'interview_scheduled': ('#0891b2', '#ecfeff'),
            'interview_confirmed': ('#059669', '#ecfdf5'),
            'interview_cancelled': ('#dc2626', '#fef2f2'),
            'job_approved': ('#10b981', '#ecfdf5'),
            'job_rejected': ('#ef4444', '#fef2f2'),
            'announcement': ('#f59e0b', '#fffbeb'),
        }
        fg, bg = colors.get(obj.type, ('#6b7280', '#f3f4f6'))
        return format_html(
            '<span style="background:{}; color:{}; padding:3px 10px; '
            'border-radius:12px; font-size:0.72rem; font-weight:600;">{}</span>',
            bg, fg, obj.get_type_display(),
        )

    @admin.display(description='Read', boolean=True)
    def read_badge(self, obj):
        return obj.is_read

    # ── Actions ──────────────────────────────────────────────────
    actions = ['mark_as_read', 'mark_as_unread']

    @admin.action(description='✅ Mark as Read')
    def mark_as_read(self, request, queryset):
        count = queryset.update(is_read=True)
        self.message_user(request, f'{count} notification(s) marked as read.')

    @admin.action(description='📩 Mark as Unread')
    def mark_as_unread(self, request, queryset):
        count = queryset.update(is_read=False)
        self.message_user(request, f'{count} notification(s) marked as unread.')
