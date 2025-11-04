# admin.py
from django.contrib import admin
from django.contrib.auth.models import Group
from .models import *

@admin.register(TypeOfOrganization)
class TypeOfOrganizationAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name']
    list_editable = ['is_active']

@admin.register(BranchCategory)
class BranchCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']

@admin.register(StateUTMaster)
class StateUTMasterAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_union_territory', 'is_active']
    list_filter = ['is_union_territory', 'is_active']
    search_fields = ['name', 'code']

@admin.register(CountryMaster)
class CountryMasterAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'currency', 'phone_code', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code']

@admin.register(DivisionMaster)
class DivisionMasterAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name']

@admin.register(ConcernCategory)
class ConcernCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name']

class CustomerAddressInline(admin.TabularInline):
    model = CustomerAddress
    extra = 1
    classes = ['collapse']

class CustomerBankDetailsInline(admin.TabularInline):
    model = CustomerBankDetails
    extra = 1
    classes = ['collapse']

class CustomerConcernPersonInline(admin.TabularInline):
    model = CustomerConcernPerson
    extra = 1
    classes = ['collapse']
    filter_horizontal = ['concern_for']

class CustomerDivisionInline(admin.TabularInline):
    model = CustomerDivision
    extra = 1
    classes = ['collapse']

@admin.register(CustomerMaster)
class CustomerMasterAdmin(admin.ModelAdmin):
    list_display = ['customer_id', 'name', 'organization_type', 'pan_number', 'is_active', 'created_at']
    list_filter = ['is_active', 'organization_type', 'status', 'created_at']
    search_fields = ['name', 'customer_id', 'pan_number', 'cin_number']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [CustomerAddressInline, CustomerBankDetailsInline, CustomerConcernPersonInline, CustomerDivisionInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('organization_type', 'name', 'is_active', 'status')
        }),
        ('Registration Details', {
            'fields': (
                'date_of_establishment',
                'pan_number',
                'msme_udyam_reg_no',
                'tan_number',
                'cin_number',
                'ie_code',
                'exemption_certificates'
            )
        }),
        ('Financial Information', {
            'fields': (
                'billing_currency',
                'payment_terms',
                'requires_advance',
                'credit_limit',
                'current_balance'
            )
        }),
        ('Contact Information', {
            'fields': (
                'website',
                'billing_contact_person',
                'billing_contact_email',
                'billing_contact_phone'
            )
        }),
        ('System Information', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(CustomerConcernPerson)
class CustomerConcernPersonAdmin(admin.ModelAdmin):
    list_display = ['concern_person', 'customer', 'designation', 'mobile_1', 'is_active']
    list_filter = ['is_active', 'customer', 'branch_category']
    search_fields = ['concern_person', 'customer__name', 'designation']
    filter_horizontal = ['concern_for']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('customer', 'branch_category', 'address', 'concern_person', 'designation')
        }),
        ('Contact Information', {
            'fields': (
                ('country_1', 'mobile_1'),
                ('country_2', 'mobile_2'),
                ('office_phone_1', 'office_extension_1'),
                'office_phone_2',
                ('email_company', 'email_personal')
            )
        }),
        ('Additional Information', {
            'fields': ('concern_for', 'remarks', 'is_active', 'is_primary_contact')
        }),
        ('System Information', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

# Unregister default Group if not needed
# admin.site.unregister(Group)