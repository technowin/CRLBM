from django.urls import path
from . import views

app_name = 'crm'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),  
    
    # Enquiry URLs
    path('enquiries/', views.EnquiryListView.as_view(), name='enquiry_list'),
    path('enquiries/create/', views.EnquiryCreateView.as_view(), name='enquiry_create'),
    path('enquiries/<int:pk>/', views.EnquiryDetailView.as_view(), name='enquiry_detail'),
    path('enquiries/<int:pk>/update/', views.EnquiryUpdateView.as_view(), name='enquiry_update'),
    path('enquiries/<int:pk>/delete/', views.EnquiryDeleteView.as_view(), name='enquiry_delete'),
    
    # Quotation URLs
    path('quotations/', views.QuotationListView.as_view(), name='quotation_list'),
    path('quotations/create/', views.QuotationCreateView.as_view(), name='quotation_create'),
    path('quotations/<int:pk>/', views.QuotationDetailView.as_view(), name='quotation_detail'),
    path('quotations/<int:pk>/update/', views.QuotationUpdateView.as_view(), name='quotation_update'),
    path('quotations/<int:pk>/delete/', views.QuotationDeleteView.as_view(), name='quotation_delete'),
    path('quotations/<int:pk>/update-status/', views.update_quotation_status, name='quotation_update_status'),
    
    # Sales Order URLs
    path('sales-orders/', views.SalesOrderListView.as_view(), name='sales_order_list'),
    path('sales-orders/create/', views.SalesOrderCreateView.as_view(), name='sales_order_create'),
    path('sales-orders/<int:pk>/', views.SalesOrderDetailView.as_view(), name='sales_order_detail'),
    path('sales-orders/<int:pk>/update/', views.SalesOrderUpdateView.as_view(), name='sales_order_update'),
    path('sales-orders/<int:pk>/delete/', views.SalesOrderDeleteView.as_view(), name='sales_order_delete'),
    path('sales-orders/<int:pk>/update-status/', views.update_order_status, name='sales_order_update_status'),
    
    # AJAX URLs
    path('ajax/get-contact-persons/', views.get_contact_persons, name='get_contact_persons'),
    path('ajax/get-enquiry-items/', views.get_enquiry_items, name='get_enquiry_items'),
]