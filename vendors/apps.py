from django.apps import AppConfig

class VendorsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'vendors'
    verbose_name = 'Vendor Management'
    
    def ready(self):
        # Import and connect signals
        import vendors.signals
        
        # Add dynamic properties to models
        from .models import VendorQualitySystem
        from django.utils import timezone
        from datetime import timedelta
        
        # Add properties dynamically
        def is_expired(self):
            return self.valid_upto < timezone.now().date()
        
        def is_expiring_soon(self):
            thirty_days_from_now = timezone.now().date() + timedelta(days=30)
            return self.valid_upto <= thirty_days_from_now and self.valid_upto >= timezone.now().date()
        
        VendorQualitySystem.is_expired = property(is_expired)
        VendorQualitySystem.is_expiring_soon = property(is_expiring_soon)