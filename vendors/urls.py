# Complete vendors/urls.py

from django.shortcuts import render
from django.urls import path
from . import views
from .views import  VendorDetailView

app_name = 'vendors'

urlpatterns = [
    # Dashboard and Main Views
    path('', views.vendor_dashboard, name='vendor_dashboard'),
    path('list/', views.vendor_list, name='vendor_list'),
    path('export/', views.vendor_export, name='vendor_export'),
    
    # Vendor Wizard Registration
    path('new/', views.vendor_wizard_start, name='vendor_wizard_start'),
    path('new/step/<int:step>/', views.vendor_wizard, name='vendor_wizard_step'),
    path('new/step/<int:step>/<int:vendor_id>/', views.vendor_wizard, name='vendor_wizard_step'),
    
    # Vendor Management
    path('vendor/<int:pk>/', VendorDetailView.as_view(), name='vendor_detail'),
    path('vendor/<int:pk>/review/', views.vendor_review, name='vendor_review'),
    path('vendor/<int:pk>/approve/', views.vendor_approve, name='vendor_approve'),
    path('vendor/<int:pk>/reject/', views.vendor_reject, name='vendor_reject'),
    path('vendor/<int:pk>/blacklist/', views.vendor_blacklist, name='vendor_blacklist'),
    path('vendor/<int:pk>/remove-blacklist/', views.vendor_remove_blacklist, name='vendor_remove_blacklist'),
    
    # Sister Concerns
    path('vendor/<int:vendor_id>/add-sister-concern/', views.add_sister_concern, name='add_sister_concern'),
    path('sister-concern/<int:sister_concern_id>/delete/', views.delete_sister_concern, name='delete_sister_concern'),

    # Contact Management
    path('vendor/<int:vendor_id>/add-contact/', views.add_vendor_contact, name='add_vendor_contact'),
    path('contact/<int:contact_id>/delete/', views.delete_vendor_contact, name='delete_vendor_contact'),
    
    # Bank Management
    path('vendor/<int:vendor_id>/add-bank/', views.add_vendor_bank, name='add_vendor_bank'),
    path('bank/<int:bank_id>/delete/', views.delete_vendor_bank, name='delete_vendor_bank'),
    
    # Financial Information
    path('vendor/<int:vendor_id>/add-financial/', views.add_financial_info, name='add_financial_info'),
    path('financial/<int:financial_id>/delete/', views.delete_financial_info, name='delete_financial_info'),
    
    # Statutory Details
    path('vendor/<int:vendor_id>/save-statutory/', views.save_statutory_details, name='save_statutory_details'),
    
    # Quality Systems
    path('vendor/<int:vendor_id>/add-quality/', views.add_quality_system, name='add_quality_system'),
    path('quality/<int:quality_id>/delete/', views.delete_quality_system, name='delete_quality_system'),
    
    # Manpower and References
    path('vendor/<int:vendor_id>/save-manpower/', views.save_manpower, name='save_manpower'),
     # Customer References
    path('vendor/<int:vendor_id>/add-customer-reference/', views.add_customer_reference, name='add_customer_reference'),
    path('customer-reference/<int:reference_id>/delete/', views.delete_customer_reference, name='delete_customer_reference'),

    # Dealerships
    path('vendor/<int:vendor_id>/add-dealership/', views.add_dealership, name='add_dealership'),
    path('dealership/<int:dealership_id>/delete/', views.delete_dealership, name='delete_dealership'),

    # References
    path('vendor/<int:vendor_id>/save-reference/', views.save_reference, name='save_reference'),

    # Concern Persons
    path('vendor/<int:vendor_id>/add-concern-person/', views.add_concern_person, name='add_concern_person'),
    path('concern-person/<int:person_id>/delete/', views.delete_concern_person, name='delete_concern_person'),
    
    # Documents
    path('vendor/<int:vendor_id>/add-document/', views.add_document, name='add_document'),
    path('document/<int:document_id>/delete/', views.delete_document, name='delete_document'),
    
    # API Endpoints
    path('api/states/<int:country_id>/', views.get_states, name='api_states'),
    path('api/validate-pan/', views.validate_pan, name='api_validate_pan'),
    path('api/quick-stats/', views.vendor_quick_stats, name='api_quick_stats'),

    # Workflow
    path('workflow/', views.vendor_workflow_dashboard, name='vendor_workflow_dashboard'),
    path('vendor/<int:pk>/assign-review/', views.assign_vendor_review, name='assign_vendor_review'),
]

# Add error handlers
handler404 = 'vendors.views.handler404'
handler500 = 'vendors.views.handler500'

# Add error handling views
def handler404(request, exception):
    return render(request, 'vendors/404.html', status=404)

def handler500(request):
    return render(request, 'vendors/500.html', status=500)