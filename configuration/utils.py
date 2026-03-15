from django.core.cache import cache
from django.conf import settings
from .models import PlatformSetting


def get_setting(key, default=None):
    """
    Fetch a global platform setting from the singleton model.
    Uses Redis/LocMem caching with automatic expiration.
    Returns typed values (int, bool, float, str) based on the model field.
    """
    cache_key = 'platform_settings_dict'
    settings_dict = cache.get(cache_key)

    if settings_dict is None:
        try:
            # Try to fetch the singleton instance
            instance = PlatformSetting.objects.get(pk=1)
            # Convert instance to dict for caching
            settings_dict = {
                field.name: getattr(instance, field.name)
                for field in instance._meta.fields
            }
            # Cache for 24 hours (86400 seconds)
            cache.set(cache_key, settings_dict, timeout=86400)
        except PlatformSetting.DoesNotExist:
            # Fallback to hardcoded settings.py values or provided default
            return getattr(settings, key.upper(), default)
        except Exception:
            # Database or Redis might be down, fallback to settings.py
            return getattr(settings, key.upper(), default)

    # Return the specific key from local dict
    return settings_dict.get(key, getattr(settings, key.upper(), default))
