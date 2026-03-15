from django.db import models
from django.core.cache import cache


class PlatformSetting(models.Model):
    """
    Singleton model for global platform configurations.
    Only one instance exists (PK=1).
    """
    # ── OTP Settings ─────────────────────────────────────────────
    otp_expire_minutes = models.PositiveIntegerField(
        default=10, 
        help_text="How long the OTP is valid for (in minutes)."
    )
    otp_max_attempts = models.PositiveIntegerField(
        default=5, 
        help_text="Maximum failed attempts before OTP is invalidated."
    )

    # ── File Upload Settings ─────────────────────────────────────
    max_cv_size_mb = models.PositiveIntegerField(
        default=5,
        help_text="Maximum allowed size for CV uploads (in MB)."
    )
    max_logo_size_mb = models.PositiveIntegerField(
        default=2,
        help_text="Maximum allowed size for company logo uploads (in MB)."
    )

    # ── Platform Flags ───────────────────────────────────────────
    maintenance_mode = models.BooleanField(
        default=False,
        help_text="Enable to put the platform in maintenance mode."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.pk = 1  # Ensure only one record exists
        super().save(*args, **kwargs)
        # Invalidate the cache whenever settings change
        cache.delete('platform_settings_dict')

    def __str__(self):
        return "Global Platform Settings"

    class Meta:
        verbose_name = "Platform Setting"
        verbose_name_plural = "Platform Settings"
