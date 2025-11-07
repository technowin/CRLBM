from django.contrib import admin
from .models import Enquiry, EnquiryItem, Quotation, QuotationItem, SalesOrder, SalesOrderItem

@admin.register(Enquiry)
class EnquiryAdmin(admin.ModelAdmin):
    list_display = ['enquiry_number', 'customer', 'enquiry_type', 'priority', 'status', 'enquiry_date', 'created_by']
    list_filter = ['enquiry_type', 'priority', 'status', 'enquiry_date']
    search_fields = ['enquiry_number', 'customer__name', 'subject']
    readonly_fields = ['enquiry_number', 'created_date', 'last_modified']
    date_hierarchy = 'enquiry_date'

@admin.register(EnquiryItem)
class EnquiryItemAdmin(admin.ModelAdmin):
    list_display = ['enquiry', 'service_category', 'service_description', 'quantity', 'unit']
    list_filter = ['service_category', 'unit']
    search_fields = ['enquiry__enquiry_number', 'service_description']

@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):
    list_display = ['quotation_number', 'customer', 'enquiry', 'status', 'quotation_date', 'expiry_date', 'total_amount']
    list_filter = ['status', 'quotation_date', 'currency']
    search_fields = ['quotation_number', 'customer__name', 'enquiry__enquiry_number']
    readonly_fields = ['quotation_number', 'expiry_date', 'created_date', 'last_modified']
    date_hierarchy = 'quotation_date'

@admin.register(QuotationItem)
class QuotationItemAdmin(admin.ModelAdmin):
    list_display = ['quotation', 'service_description', 'quantity', 'unit', 'unit_price', 'line_total']
    list_filter = ['service_category']
    search_fields = ['quotation__quotation_number', 'service_description']

@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'customer', 'quotation', 'status', 'order_date', 'expected_delivery_date', 'total_amount']
    list_filter = ['status', 'order_date', 'currency']
    search_fields = ['order_number', 'customer__name', 'customer_po_number']
    readonly_fields = ['order_number', 'created_date', 'last_modified']
    date_hierarchy = 'order_date'

@admin.register(SalesOrderItem)
class SalesOrderItemAdmin(admin.ModelAdmin):
    list_display = ['sales_order', 'service_description', 'quantity', 'unit', 'unit_price', 'line_total', 'status']
    list_filter = ['service_category', 'status']
    search_fields = ['sales_order__order_number', 'service_description']