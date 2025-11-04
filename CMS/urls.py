# urls.py
from django.urls import path
from . import views

app_name = 'cms'

urlpatterns = [
    # Dashboard
    path('dashboard', views.dashboard, name='dashboard'),
    
    # Customer URLs
    path('customers/', views.customer_list_view, name='customer_list'),
    path('customers/create/', views.customer_create_view, name='customer_create'),
    path('customers/<int:pk>/', views.customer_detail_view, name='customer_detail'),
    path('customers/<int:pk>/update/', views.customer_update_view, name='customer_update'),
    path('customers/<int:pk>/toggle-status/', views.customer_toggle_status, name='customer_toggle_status'),
    
    # Customer Address URLs
    path('customers/<int:customer_pk>/add-address/', views.add_customer_address, name='add_customer_address'),
    path('addresses/<int:pk>/update/', views.update_customer_address, name='update_customer_address'),
    path('addresses/<int:pk>/delete/', views.delete_customer_address, name='delete_customer_address'),
    
    # Customer Bank URLs
    path('customers/<int:customer_pk>/add-bank/', views.add_customer_bank_detail, name='add_customer_bank'),
    path('bank-details/<int:pk>/update/', views.update_customer_bank_detail, name='update_customer_bank_detail'),
    path('bank-details/<int:pk>/delete/', views.delete_customer_bank_detail, name='delete_customer_bank_detail'),
    
    # Concern Person URLs
    path('concern-persons/', views.concern_person_list, name='concern_person_list'),
    path('concern-persons/create/', views.customer_concern_person_create, name='concern_person_create'),
    path('concern-persons/create/<int:customer_pk>/', views.customer_concern_person_create, name='concern_person_create_for_customer'),
    path('concern-persons/<int:pk>/update/', views.customer_concern_person_update, name='concern_person_update'),
    path('concern-persons/<int:pk>/toggle-status/', views.toggle_concern_person_status, name='toggle_concern_person_status'),
    path('concern-persons/<int:pk>/delete/', views.delete_concern_person, name='delete_concern_person'),
    path('customers/<int:customer_pk>/add-quick-concern/', views.add_quick_concern_person, name='add_quick_concern'),
    
    # Document URLs
    path('customers/<int:customer_pk>/add-document/', views.add_customer_document, name='add_customer_document'),
    path('documents/<int:pk>/verify/', views.verify_customer_document, name='verify_customer_document'),
    path('documents/<int:pk>/delete/', views.delete_customer_document, name='delete_customer_document'),
    
    # Note URLs
    path('customers/<int:customer_pk>/add-note/', views.add_customer_note, name='add_customer_note'),
    path('notes/<int:pk>/resolve/', views.resolve_customer_note, name='resolve_customer_note'),
    path('notes/<int:pk>/delete/', views.delete_customer_note, name='delete_customer_note'),
    
    # AJAX URLs
    path('check-name/', views.check_customer_name, name='check_customer_name'),
    path('ajax/get-customer-addresses/<int:customer_pk>/', views.get_customer_addresses, name='get_customer_addresses'),
    
    # Export and Report URLs
    path('export/customers/csv/', views.export_customers_csv, name='export_customers_csv'),
    path('reports/', views.customer_reports, name='customer_reports'),
]