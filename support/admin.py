from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import SupportTicket, TicketReply

class TicketReplyInline(admin.TabularInline):
    model = TicketReply
    extra = 1
    readonly_fields = ('created_at',)
    fields = ('author', 'message', 'is_staff_reply', 'created_at')

@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = (
        'ticket_id', 'user_email', 'category_badge', 
        'priority_badge', 'status_badge', 'assigned_to', 'created_at'
    )
    list_filter = ('status', 'category', 'priority', 'assigned_to', 'created_at')
    search_fields = ('id', 'user__email', 'subject', 'message')
    readonly_fields = ('id', 'created_at', 'updated_at', 'resolved_at')
    inlines = [TicketReplyInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'user', 'subject', 'message')
        }),
        ('Classification', {
            'fields': ('category', 'priority', 'status')
        }),
        ('Assignment & Resolution', {
            'fields': ('assigned_to', 'created_at', 'updated_at', 'resolved_at')
        }),
    )

    @admin.display(description='Ticket ID')
    def ticket_id(self, obj):
        return str(obj.id)[:8] + '...'

    @admin.display(description='User')
    def user_email(self, obj):
        return obj.user.email

    @admin.display(description='Status')
    def status_badge(self, obj):
        colors = {
            'open': ('#dc2626', '#fef2f2'),
            'in_progress': ('#2563eb', '#eff6ff'),
            'resolved': ('#059669', '#ecfdf5'),
            'closed': ('#6b7280', '#f3f4f6'),
        }
        fg, bg = colors.get(obj.status, ('#6b7280', '#f3f4f6'))
        return format_html(
            '<span style="background:{}; color:{}; padding:3px 10px; '
            'border-radius:12px; font-size:0.75rem; font-weight:600;">{}</span>',
            bg, fg, obj.get_status_display()
        )

    @admin.display(description='Priority')
    def priority_badge(self, obj):
        colors = {
            'high': ('#dc2626', '#fef2f2'),
            'medium': ('#d97706', '#fffbeb'),
            'low': ('#059669', '#ecfdf5'),
        }
        fg, bg = colors.get(obj.priority, ('#6b7280', '#f3f4f6'))
        return format_html(
            '<span style="background:{}; color:{}; padding:3px 10px; '
            'border-radius:12px; font-size:0.75rem; font-weight:600;">{}</span>',
            bg, fg, obj.get_priority_display()
        )

    @admin.display(description='Category')
    def category_badge(self, obj):
        return format_html(
            '<span style="color:#4b5563; font-size:0.8rem; font-weight:500;">{}</span>',
            obj.get_category_display()
        )

    # ── Actions ──────────────────────────────────────────────────
    actions = ['assign_to_me', 'mark_resolved', 'mark_closed']

    @admin.action(description='🙋 Assign selected tickets to me')
    def assign_to_me(self, request, queryset):
        updated = queryset.update(assigned_to=request.user, status=SupportTicket.Status.IN_PROGRESS)
        self.message_user(request, f'{updated} ticket(s) assigned to you.')

    @admin.action(description='✅ Mark selected tickets as Resolved')
    def mark_resolved(self, request, queryset):
        # We use a loop here because .update() doesn't trigger .save() logic (resolved_at)
        for ticket in queryset:
            ticket.status = SupportTicket.Status.RESOLVED
            ticket.save()
        self.message_user(request, f'{queryset.count()} ticket(s) marked as resolved.')

    @admin.action(description='🔒 Mark selected tickets as Closed')
    def mark_closed(self, request, queryset):
        for ticket in queryset:
            ticket.status = SupportTicket.Status.CLOSED
            ticket.save()
        self.message_user(request, f'{queryset.count()} ticket(s) marked as closed.')
