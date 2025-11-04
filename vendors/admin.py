from django.contrib import admin
from django.contrib.auth.models import Group
from .models import *

class VendorContactInline(admin.TabularInline):
    model = VendorContact
    extra = 1
    fields = ['contact_type', 'address', 'state', 'gst_number', 'is_primary']

class VendorBankDetailInline(admin.TabularInline):
    model = VendorBankDetail
    extra = 1
    fields = ['bank_name', 'account_number', 'ifsc_code', 'is_primary', 'is_active']

class VendorConcernPersonInline(admin.TabularInline):
    model = VendorConcernPerson
    extra = 1
    fields = ['name', 'designation', 'mobile_1', 'concern_for', 'is_primary']

class VendorFinancialInfoInline(admin.TabularInline):
    model = VendorFinancialInfo
    extra = 1
    fields = ['year', 'share_capital_reserves', 'sales_turnover', 'cash_profit']

class VendorQualitySystemInline(admin.TabularInline):
    model = VendorQualitySystem
    extra = 1
    fields = ['system_name', 'certificate_number', 'valid_upto']

class VendorCustomerReferenceInline(admin.TabularInline):
    model = VendorCustomerReference
    extra = 1
    fields = ['customer_name', 'percentage']

class VendorDocumentInline(admin.TabularInline):
    model = VendorDocument
    extra = 1
    fields = ['document_type', 'file', 'description', 'is_verified']

@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = [
        'vendor_code', 'company_name', 'company_type', 'pan_number', 
        'status', 'is_active', 'is_blacklisted', 'created_at'
    ]
    list_filter = [
        'status', 'is_active', 'is_blacklisted', 'company_type', 
        'is_msme', 'country', 'created_at'
    ]
    search_fields = [
        'company_name', 'vendor_code', 'pan_number', 'display_name'
    ]
    readonly_fields = ['vendor_code', 'created_at', 'updated_at', 'submitted_date']
    fieldsets = [
        ('Basic Information', {
            'fields': [
                'vendor_code', 'country', 'company_type', 'company_name', 
                'display_name', 'create_ledger', 'vendor_types', 'work_description'
            ]
        }),
        ('Registration Details', {
            'fields': [
                'pan_number', 'pan_copy', 'is_msme', 'msme_type', 
                'msme_number', 'msme_certificate', 'msme_validity'
            ]
        }),
        ('Company Dates', {
            'fields': [
                'establishment_date', 'commencement_date'
            ]
        }),
        ('Preferences', {
            'fields': [
                'payment_preference', 'vendor_group', 'registered_with_bluechip',
                'responsibility_return_replace'
            ]
        }),
        ('Status & Workflow', {
            'fields': [
                'status', 'is_active', 'is_blacklisted', 'blacklist_reason',
                'blacklist_date', 'submitted_date', 'reviewed_by', 'reviewed_date',
                'approval_notes'
            ]
        }),
        ('Metadata', {
            'fields': [
                'created_by', 'created_at', 'updated_at'
            ]
        }),
    ]
    inlines = [
        VendorContactInline,
        VendorBankDetailInline,
        VendorConcernPersonInline,
        VendorFinancialInfoInline,
        VendorQualitySystemInline,
        VendorCustomerReferenceInline,
        VendorDocumentInline,
    ]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'country', 'created_by', 'reviewed_by'
        )
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(VendorCategory)
class VendorCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']

@admin.register(VendorApprovalLog)
class VendorApprovalLogAdmin(admin.ModelAdmin):
    list_display = ['vendor', 'action', 'performed_by', 'performed_at']
    list_filter = ['action', 'performed_at']
    search_fields = ['vendor__company_name', 'performed_by__username']
    readonly_fields = ['performed_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('vendor', 'performed_by')

# Unregister default Group if not needed
# admin.site.unregister(Group)

# Customize admin site
admin.site.site_header = "Vendor Management System Administration"
admin.site.site_title = "VMS Admin"
admin.site.index_title = "Vendor Management System"