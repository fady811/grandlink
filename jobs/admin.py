from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.db.models import Count, Q
from django.template.response import TemplateResponse
from django.http import HttpResponseRedirect
from .models import Skill, Job, Application, SavedJob, JobReport, JobCategory
from .services import approve_job, reject_job, resolve_job_report


# ═══════════════════════════════════════════════════════════════
#  INLINES
# ═══════════════════════════════════════════════════════════════

class ApplicationInline(admin.TabularInline):
    """Show applications directly within the Job detail page."""
    model = Application
    fields = ('student', 'status', 'applied_at')
    readonly_fields = ('student', 'applied_at')
    extra = 0
    show_change_link = True
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class JobReportInline(admin.TabularInline):
    """Show pending reports on the Job detail page."""
    model = JobReport
    fields = ('reporter', 'reason', 'status', 'created_at')
    readonly_fields = ('reporter', 'reason', 'status', 'created_at')
    extra = 0
    show_change_link = True
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


# ═══════════════════════════════════════════════════════════════
#  SKILL ADMIN
# ═══════════════════════════════════════════════════════════════

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'category_badge', 'jobs_count', 'created_at')
    list_filter = ('category',)
    search_fields = ('name',)
    ordering = ('name',)
    list_per_page = 50

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(num_jobs=Count('jobs'))

    @admin.display(description='Category')
    def category_badge(self, obj):
        colors = {
            'technical': ('#4f46e5', '#eef2ff'),
            'soft': ('#059669', '#ecfdf5'),
            'language': ('#d97706', '#fffbeb'),
            'tool': ('#7c3aed', '#f5f3ff'),
        }
        if not obj.category:
            return '—'
        text_color, bg_color = colors.get(obj.category, ('#6b7280', '#f3f4f6'))
        return format_html(
            '<span style="background:{}; color:{}; padding:3px 10px; '
            'border-radius:12px; font-size:0.72rem; font-weight:600;">{}</span>',
            bg_color, text_color, obj.get_category_display(),
        )

    @admin.display(description='Jobs Using', ordering='num_jobs')
    def jobs_count(self, obj):
        count = obj.num_jobs
        if count == 0:
            return '0'
        return format_html(
            '<span style="font-weight:600; color:#4f46e5;">{}</span>', count,
        )

@admin.register(JobCategory)
class JobCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'jobs_count', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)

    def jobs_count(self, obj):
        return obj.jobs.count()
    jobs_count.short_description = 'Job Posts'

# ═══════════════════════════════════════════════════════════════
#  JOB ADMIN
# ═══════════════════════════════════════════════════════════════

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    """Rich Job management with approval workflow, status badges & inline applications."""

    # ── List View ────────────────────────────────────────────────
    list_display = (
        'title', 'employer', 'category', 'is_flagged', 'flag_count_badge', 'work_type_badge', 
        'experience_badge', 'status_badge', 'deadline_display',
        'apps_count', 'views_count', 'created_at',
    )
    list_filter = ('is_flagged', 'status', 'work_type', 'experience_level', 'is_remote', 'hide_salary')
    search_fields = ('title', 'description', 'employer__company_name', 'location')
    readonly_fields = (
        'id', 'is_flagged', 'views_count', 'created_at', 'updated_at', 'apps_count_detail',
        'reviewed_by', 'reviewed_at', 'submitted_at',
    )
    filter_horizontal = ('skills',)
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    list_per_page = 25
    list_select_related = ('employer',)
    inlines = [ApplicationInline, JobReportInline]

    # ── Detail View ──────────────────────────────────────────────
    fieldsets = (
        ('Job Information', {
            'fields': ('id', 'employer', 'title', 'description', 'requirements', 'responsibilities'),
        }),
        ('Classification', {
            'fields': ('category', 'work_type', 'experience_level', 'skills'),
        }),
        ('Location', {
            'fields': ('location', 'is_remote'),
        }),
        ('Compensation', {
            'fields': ('salary_min', 'salary_max', 'hide_salary'),
        }),
        ('Status & Deadline', {
            'fields': ('status', 'is_flagged', 'deadline'),
        }),
        ('Review', {
            'fields': ('reviewed_by', 'reviewed_at', 'submitted_at', 'rejection_reason'),
            'classes': ('collapse',),
        }),
        ('Analytics', {
            'fields': ('views_count', 'apps_count_detail', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('employer').annotate(
            num_apps=Count('applications', distinct=True),
            pending_reports=Count('reports', filter=Q(reports__status=JobReport.Status.PENDING), distinct=True)
        )

    # ── Custom Columns ───────────────────────────────────────────
    @admin.display(description='Reports', ordering='pending_reports')
    def flag_count_badge(self, obj):
        count = obj.pending_reports
        if count == 0:
            return '—'
        color = '#dc2626' if count >= 5 else '#b45309'
        return format_html(
            '<span style="color:{}; font-weight:bold;">{}</span>',
            color, count
        )
    @admin.display(description='Type')
    def work_type_badge(self, obj):
        colors = {
            'full_time': ('#059669', '#ecfdf5'),
            'part_time': ('#2563eb', '#eff6ff'),
            'internship': ('#7c3aed', '#f5f3ff'),
            'contract': ('#d97706', '#fffbeb'),
            'remote': ('#0891b2', '#ecfeff'),
        }
        text_color, bg_color = colors.get(obj.work_type, ('#6b7280', '#f3f4f6'))
        return format_html(
            '<span style="background:{}; color:{}; padding:3px 9px; '
            'border-radius:12px; font-size:0.7rem; font-weight:600;">{}</span>',
            bg_color, text_color, obj.get_work_type_display(),
        )

    @admin.display(description='Level')
    def experience_badge(self, obj):
        return format_html(
            '<span style="color:#6b7280; font-size:0.78rem;">{}</span>',
            obj.get_experience_level_display(),
        )

    @admin.display(description='Status')
    def status_badge(self, obj):
        colors = {
            'draft': ('#6b7280', '#f3f4f6', '📝'),
            'pending_review': ('#b45309', '#fef3c7', '🔍'),
            'active': ('#059669', '#ecfdf5', '🟢'),
            'paused': ('#d97706', '#fffbeb', '⏸️'),
            'closed': ('#dc2626', '#fef2f2', '🔴'),
            'expired': ('#9ca3af', '#f9fafb', '⏰'),
        }
        text_color, bg_color, icon = colors.get(obj.status, ('#6b7280', '#f3f4f6', ''))
        label = '{} {}'.format(icon, obj.get_status_display())
        return format_html(
            '<span style="background:{}; color:{}; padding:3px 10px; '
            'border-radius:12px; font-size:0.72rem; font-weight:600;">{}</span>',
            bg_color, text_color, label,
        )

    @admin.display(description='Deadline')
    def deadline_display(self, obj):
        if not obj.deadline:
            return 'No deadline'
        is_past = obj.deadline < timezone.now()
        color = '#dc2626' if is_past else '#059669'
        icon = '⚠️' if is_past else '📅'
        label = '{} {}'.format(icon, obj.deadline.strftime('%b %d, %Y'))
        return format_html(
            '<span style="color:{}; font-size:0.78rem;">{}</span>',
            color, label,
        )

    @admin.display(description='Applications', ordering='num_apps')
    def apps_count(self, obj):
        count = obj.num_apps
        if count == 0:
            return '0'
        return format_html(
            '<a href="/admin/jobs/application/?job__id__exact={}" '
            'style="background:#eef2ff; color:#4f46e5; padding:3px 10px; '
            'border-radius:12px; font-size:0.75rem; font-weight:600; '
            'text-decoration:none;">{}</a>',
            obj.pk, '{} 📩'.format(count),
        )

    @admin.display(description='Total Applications')
    def apps_count_detail(self, obj):
        return obj.applications.count()

    # ── Actions ──────────────────────────────────────────────────
    actions = ['approve_jobs', 'reject_jobs', 'make_paused', 'make_closed']

    @admin.action(description='✅ Approve selected jobs (pending → active)')
    def approve_jobs(self, request, queryset):
        pending = queryset.filter(status=Job.Status.PENDING_REVIEW)
        skipped = queryset.exclude(status=Job.Status.PENDING_REVIEW).count()
        approved_count = 0

        for job in pending.select_related('employer__user'):
            approve_job(job, request.user)
            approved_count += 1

        msg = f'{approved_count} job(s) approved.'
        if skipped:
            msg += f' {skipped} job(s) skipped (not pending review).'
        self.message_user(request, msg)

    @admin.action(description='❌ Reject selected jobs (pending → draft)')
    def reject_jobs(self, request, queryset):
        pending = queryset.filter(status=Job.Status.PENDING_REVIEW)

        if not pending.exists():
            self.message_user(request, 'No pending review jobs selected.', level='warning')
            return

        # If the form was submitted with a rejection reason
        if 'apply' in request.POST:
            reason = request.POST.get('rejection_reason', '').strip()
            if not reason:
                self.message_user(request, 'Rejection reason is required.', level='error')
                return

            rejected_count = 0
            for job in pending.select_related('employer__user'):
                reject_job(job, request.user, reason)
                rejected_count += 1

            self.message_user(request, f'{rejected_count} job(s) rejected.')
            return HttpResponseRedirect(request.get_full_path())

        # Show intermediate confirmation page
        return TemplateResponse(
            request,
            'admin/jobs/reject_intermediate.html',
            context={
                **self.admin_site.each_context(request),
                'title': 'Reject Jobs',
                'jobs': pending.select_related('employer'),
                'action_checkbox_name': admin.helpers.ACTION_CHECKBOX_NAME,
                'opts': self.model._meta,
            },
        )

    @admin.action(description='⏸️ Set status to Paused')
    def make_paused(self, request, queryset):
        count = queryset.filter(
            status__in=[Job.Status.ACTIVE, Job.Status.PENDING_REVIEW]
        ).update(status=Job.Status.PAUSED)
        self.message_user(request, f'{count} job(s) paused.')

    @admin.action(description='🔴 Set status to Closed')
    def make_closed(self, request, queryset):
        count = queryset.exclude(
            status__in=[Job.Status.CLOSED, Job.Status.EXPIRED]
        ).update(status=Job.Status.CLOSED)
        self.message_user(request, f'{count} job(s) closed.')


# ═══════════════════════════════════════════════════════════════
#  APPLICATION ADMIN
# ═══════════════════════════════════════════════════════════════

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    """Application management with status workflow."""

    # ── List View ────────────────────────────────────────────────
    list_display = (
        'get_student_email', 'get_job_title', 'get_company',
        'status_badge', 'has_resume', 'applied_at',
    )
    list_filter = ('status', 'applied_at')
    search_fields = ('student__user__email', 'job__title', 'job__employer__company_name')
    readonly_fields = ('id', 'applied_at', 'updated_at')
    date_hierarchy = 'applied_at'
    ordering = ('-applied_at',)
    list_per_page = 25
    list_select_related = ('student', 'student__user', 'job', 'job__employer')
    raw_id_fields = ('job', 'student')

    # ── Detail View ──────────────────────────────────────────────
    fieldsets = (
        ('Application', {
            'fields': ('id', 'job', 'student'),
        }),
        ('Content', {
            'fields': ('cover_letter', 'resume'),
        }),
        ('Review', {
            'fields': ('status', 'employer_notes'),
        }),
        ('Dates', {
            'fields': ('applied_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    # ── Custom Columns ───────────────────────────────────────────
    @admin.display(description='Student', ordering='student__user__email')
    def get_student_email(self, obj):
        return obj.student.user.email

    @admin.display(description='Job', ordering='job__title')
    def get_job_title(self, obj):
        return obj.job.title

    @admin.display(description='Company', ordering='job__employer__company_name')
    def get_company(self, obj):
        return obj.job.employer.company_name

    @admin.display(description='Status')
    def status_badge(self, obj):
        colors = {
            'pending': ('#d97706', '#fffbeb'),
            'reviewing': ('#2563eb', '#eff6ff'),
            'shortlisted': ('#7c3aed', '#f5f3ff'),
            'interview': ('#0891b2', '#ecfeff'),
            'accepted': ('#059669', '#ecfdf5'),
            'rejected': ('#dc2626', '#fef2f2'),
            'withdrawn': ('#6b7280', '#f3f4f6'),
        }
        text_color, bg_color = colors.get(obj.status, ('#6b7280', '#f3f4f6'))
        return format_html(
            '<span style="background:{}; color:{}; padding:3px 10px; '
            'border-radius:12px; font-size:0.72rem; font-weight:600;">{}</span>',
            bg_color, text_color, obj.get_status_display(),
        )

    @admin.display(description='CV', boolean=True)
    def has_resume(self, obj):
        return bool(obj.resume)

    # ── Actions ──────────────────────────────────────────────────
    actions = ['mark_reviewing', 'mark_shortlisted', 'mark_rejected']

    @admin.action(description='📋 Mark as Under Review')
    def mark_reviewing(self, request, queryset):
        count = queryset.update(status=Application.Status.REVIEWING)
        self.message_user(request, f'{count} application(s) marked as Under Review.')

    @admin.action(description='⭐ Mark as Shortlisted')
    def mark_shortlisted(self, request, queryset):
        count = queryset.update(status=Application.Status.SHORTLISTED)
        self.message_user(request, f'{count} application(s) shortlisted.')

    @admin.action(description='❌ Mark as Rejected')
    def mark_rejected(self, request, queryset):
        count = queryset.update(status=Application.Status.REJECTED)
        self.message_user(request, f'{count} application(s) rejected.')


# ═══════════════════════════════════════════════════════════════
#  SAVED JOB ADMIN
# ═══════════════════════════════════════════════════════════════

@admin.register(SavedJob)
class SavedJobAdmin(admin.ModelAdmin):
    list_display = ('get_student_email', 'get_job_title', 'saved_at')
    search_fields = ('student__user__email', 'job__title')
    readonly_fields = ('id', 'saved_at')
    ordering = ('-saved_at',)
    list_per_page = 30
    list_select_related = ('student', 'student__user', 'job')

    @admin.display(description='Student', ordering='student__user__email')
    def get_student_email(self, obj):
        return obj.student.user.email

    @admin.display(description='Job', ordering='job__title')
    def get_job_title(self, obj):
        return obj.job.title


# ═══════════════════════════════════════════════════════════════
#  JOB REPORT ADMIN
# ═══════════════════════════════════════════════════════════════

@admin.register(JobReport)
class JobReportAdmin(admin.ModelAdmin):
    list_display = ('job', 'get_employer', 'reason', 'status_badge', 'created_at')
    list_filter = ('status', 'reason', 'created_at')
    search_fields = ('job__title', 'job__employer__company_name', 'details')
    readonly_fields = ('job', 'reporter', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    list_per_page = 30
    list_select_related = ('job', 'job__employer', 'reporter')

    fieldsets = (
        ('Report Details', {
            'fields': ('job', 'reporter', 'reason', 'details')
        }),
        ('Administration', {
            'fields': ('status', 'created_at', 'updated_at')
        })
    )

    @admin.display(description='Employer', ordering='job__employer__company_name')
    def get_employer(self, obj):
        return obj.job.employer.company_name

    @admin.display(description='Status')
    def status_badge(self, obj):
        colors = {
            'pending': ('#dc2626', '#fef2f2'),
            'reviewed': ('#059669', '#ecfdf5'),
            'dismissed': ('#6b7280', '#f3f4f6'),
        }
        text_color, bg_color = colors.get(obj.status, ('#6b7280', '#f3f4f6'))
        return format_html(
            '<span style="background:{}; color:{}; padding:3px 10px; '
            'border-radius:12px; font-size:0.72rem; font-weight:600;">{}</span>',
            bg_color, text_color, obj.get_status_display()
        )

    actions = ['mark_dismissed', 'mark_reviewed']

    @admin.action(description='✅ Dismiss Selected Reports (False Alarm)')
    def mark_dismissed(self, request, queryset):
        # We need to resolve the underlying jobs, so we iterate
        jobs_to_resolve = set()
        for report in queryset:
            report.status = JobReport.Status.DISMISSED
            report.save(update_fields=['status', 'updated_at'])
            jobs_to_resolve.add(report.job)
        
        # Check if we should unflag the jobs
        for job in jobs_to_resolve:
            resolve_job_report(job)
            
        self.message_user(request, f'{queryset.count()} report(s) dismissed.')

    @admin.action(description='⚠️ Mark as Reviewed (Action Taken)')
    def mark_reviewed(self, request, queryset):
        jobs_to_resolve = set()
        for report in queryset:
            report.status = JobReport.Status.REVIEWED
            report.save(update_fields=['status', 'updated_at'])
            jobs_to_resolve.add(report.job)

        for job in jobs_to_resolve:
            resolve_job_report(job)

        self.message_user(request, f'{queryset.count()} report(s) marked as reviewed.')
