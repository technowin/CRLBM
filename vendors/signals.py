from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Vendor, VendorApprovalLog

@receiver(post_save, sender=Vendor)
def handle_vendor_status_change(sender, instance, created, **kwargs):
    """
    Automatically handle vendor status changes and send notifications
    """
    if created:
        # New vendor created
        VendorApprovalLog.objects.create(
            vendor=instance,
            action='created',
            performed_by=instance.created_by,
            notes='Vendor registration created'
        )
        
        # Send notification email (in production)
        if not settings.DEBUG:
            send_mail(
                f'New Vendor Registration: {instance.company_name}',
                f'A new vendor {instance.company_name} has been registered in the system.',
                settings.DEFAULT_FROM_EMAIL,
                ['admin@company.com'],  # Replace with actual admin email
                fail_silently=True,
            )

@receiver(post_save, sender=Vendor)
def handle_vendor_blacklist(sender, instance, **kwargs):
    """
    Handle vendor blacklisting
    """
    if instance.is_blacklisted and instance.blacklist_reason:
        # Log the blacklisting (already handled in view, but added for completeness)
        pass