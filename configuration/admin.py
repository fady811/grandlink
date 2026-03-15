from django.contrib import admin
from .models import PlatformSetting


@admin.register(PlatformSetting)
class PlatformSettingAdmin(admin.ModelAdmin):
    """
    Admin for platform settings.
    Restricts creation and deletion to maintain singleton behavior.
    """
    list_display = (
        '__str__', 'otp_expire_minutes', 'otp_max_attempts', 
        'maintenance_mode', 'updated_at'
    )
    
    fieldsets = (
        ('Authentication (OTP)', {
            'fields': ('otp_expire_minutes', 'otp_max_attempts'),
            'description': 'Configure global One-Time Password behavior.'
        }),
        ('File Limits', {
            'fields': ('max_cv_size_mb', 'max_logo_size_mb'),
            'description': 'Set maximum file sizes for various uploads across the platform.'
        }),
        ('System Flags', {
            'fields': ('maintenance_mode',),
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    readonly_fields = ('created_at', 'updated_at')

    def has_add_permission(self, request):
        # Only allow one instance
        return not PlatformSetting.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Recommended: don't allow delete for the singleton via UI
        return False
