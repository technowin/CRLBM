from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy
from django.db.models import Q, Count, Sum
from django.http import JsonResponse
from django.forms import inlineformset_factory
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.db import transaction

from .models import Enquiry, EnquiryItem, Quotation, QuotationItem, SalesOrder, SalesOrderItem
from .forms import EnquiryForm, EnquiryItemForm, QuotationForm, QuotationItemForm, SalesOrderForm, SalesOrderItemForm
from CMS.models import CustomerMaster, CustomerConcernPerson
from Account.models import CustomUser

# Dashboard View
class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'crm/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Enquiry Statistics
        context['total_enquiries'] = Enquiry.objects.count()
        context['new_enquiries'] = Enquiry.objects.filter(status='new').count()
        context['high_priority'] = Enquiry.objects.filter(priority='high').count()
        context['urgent_enquiries'] = Enquiry.objects.filter(priority='urgent').count()
        
        # Quotation Statistics
        context['total_quotations'] = Quotation.objects.count()
        context['draft_quotations'] = Quotation.objects.filter(status='draft').count()
        context['sent_quotations'] = Quotation.objects.filter(status='sent').count()
        context['accepted_quotations'] = Quotation.objects.filter(status='accepted').count()
        
        # Sales Order Statistics
        context['total_orders'] = SalesOrder.objects.count()
        context['in_progress_orders'] = SalesOrder.objects.filter(status='in_progress').count()
        context['completed_orders'] = SalesOrder.objects.filter(status='completed').count()
        context['overdue_orders'] = SalesOrder.objects.filter(
            expected_delivery_date__lt=timezone.now().date(),
            status__in=['draft', 'confirmed', 'planning', 'in_progress']
        ).count()
        
        # Recent Activities
        context['recent_enquiries'] = Enquiry.objects.select_related('customer', 'contact_person').order_by('-created_date')[:5]
        context['recent_quotations'] = Quotation.objects.select_related('customer', 'enquiry').order_by('-created_date')[:5]
        
        return context

# Enquiry Views
class EnquiryListView(LoginRequiredMixin, ListView):
    model = Enquiry
    template_name = 'crm/enquiry_list.html'
    context_object_name = 'enquiries'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Enquiry.objects.select_related('customer', 'contact_person', 'created_by').prefetch_related('items')
        
        # Filtering
        status_filter = self.request.GET.get('status')
        priority_filter = self.request.GET.get('priority')
        type_filter = self.request.GET.get('type')
        search_query = self.request.GET.get('search')
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if priority_filter:
            queryset = queryset.filter(priority=priority_filter)
        if type_filter:
            queryset = queryset.filter(enquiry_type=type_filter)
        if search_query:
            queryset = queryset.filter(
                Q(enquiry_number__icontains=search_query) |
                Q(customer__name__icontains=search_query) |
                Q(subject__icontains=search_query) |
                Q(contact_person__concern_person__icontains=search_query)
            )
        
        return queryset.order_by('-enquiry_date', '-created_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Enquiry.ENQUIRY_STATUS
        context['priority_choices'] = Enquiry.PRIORITY_CHOICES
        context['type_choices'] = Enquiry.ENQUIRY_TYPE
        
        # Statistics for dashboard
        context['total_enquiries'] = Enquiry.objects.count()
        context['new_enquiries'] = Enquiry.objects.filter(status='new').count()
        context['high_priority'] = Enquiry.objects.filter(priority='high').count()
        context['urgent_enquiries'] = Enquiry.objects.filter(priority='urgent').count()
        
        return context

class EnquiryCreateView(LoginRequiredMixin, CreateView):
    model = Enquiry
    form_class = EnquiryForm
    template_name = 'crm/enquiry_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['item_formset'] = EnquiryItemFormSet(self.request.POST, self.request.FILES)
        else:
            context['item_formset'] = EnquiryItemFormSet()
        return context
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        context = self.get_context_data()
        item_formset = context['item_formset']
        
        if item_formset.is_valid():
            with transaction.atomic():
                self.object = form.save()
                item_formset.instance = self.object
                item_formset.save()
                
                # Update enquiry status based on items
                if self.object.items.exists():
                    if self.object.status == 'draft':
                        self.object.status = 'new'
                        self.object.save()
                
            messages.success(self.request, f'Enquiry {self.object.enquiry_number} created successfully!')
            return redirect('crm:enquiry_detail', pk=self.object.pk)
        else:
            return self.form_invalid(form)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

class EnquiryUpdateView(LoginRequiredMixin, UpdateView):
    model = Enquiry
    form_class = EnquiryForm
    template_name = 'crm/enquiry_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['item_formset'] = EnquiryItemFormSet(self.request.POST, self.request.FILES, instance=self.object)
        else:
            context['item_formset'] = EnquiryItemFormSet(instance=self.object)
        return context
    
    def form_valid(self, form):
        form.instance.modified_by = self.request.user
        context = self.get_context_data()
        item_formset = context['item_formset']
        
        if item_formset.is_valid():
            with transaction.atomic():
                self.object = form.save()
                item_formset.instance = self.object
                item_formset.save()
                
            messages.success(self.request, f'Enquiry {self.object.enquiry_number} updated successfully!')
            return redirect('crm:enquiry_detail', pk=self.object.pk)
        else:
            return self.form_invalid(form)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

class EnquiryDetailView(LoginRequiredMixin, DetailView):
    model = Enquiry
    template_name = 'crm/enquiry_detail.html'
    context_object_name = 'enquiry'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.items.all()
        context['quotations'] = self.object.quotations.all().select_related('customer')
        return context

class EnquiryDeleteView(LoginRequiredMixin, DeleteView):
    model = Enquiry
    template_name = 'crm/enquiry_confirm_delete.html'
    success_url = reverse_lazy('crm:enquiry_list')
    
    def delete(self, request, *args, **kwargs):
        enquiry = self.get_object()
        messages.success(request, f'Enquiry {enquiry.enquiry_number} deleted successfully!')
        return super().delete(request, *args, **kwargs)

# Quotation Views
class QuotationListView(LoginRequiredMixin, ListView):
    model = Quotation
    template_name = 'crm/quotation_list.html'
    context_object_name = 'quotations'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Quotation.objects.select_related('enquiry', 'customer', 'contact_person', 'created_by').prefetch_related('items')
        
        # Filtering
        status_filter = self.request.GET.get('status')
        customer_filter = self.request.GET.get('customer')
        search_query = self.request.GET.get('search')
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if customer_filter:
            queryset = queryset.filter(customer_id=customer_filter)
        if search_query:
            queryset = queryset.filter(
                Q(quotation_number__icontains=search_query) |
                Q(customer__name__icontains=search_query) |
                Q(enquiry__enquiry_number__icontains=search_query)
            )
        
        return queryset.order_by('-quotation_date', '-created_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Quotation.QUOTATION_STATUS
        context['customers'] = Quotation.objects.values('customer__id', 'customer__name').distinct()
        
        # Statistics
        context['total_quotations'] = Quotation.objects.count()
        context['draft_quotations'] = Quotation.objects.filter(status='draft').count()
        context['sent_quotations'] = Quotation.objects.filter(status='sent').count()
        context['accepted_quotations'] = Quotation.objects.filter(status='accepted').count()
        
        return context

class QuotationCreateView(LoginRequiredMixin, CreateView):
    model = Quotation
    form_class = QuotationForm
    template_name = 'crm/quotation_form.html'
    
    def get_initial(self):
        initial = super().get_initial()
        enquiry_id = self.request.GET.get('enquiry')
        if enquiry_id:
            try:
                enquiry = Enquiry.objects.get(pk=enquiry_id)
                initial['enquiry'] = enquiry
                initial['customer'] = enquiry.customer
                initial['contact_person'] = enquiry.contact_person
            except Enquiry.DoesNotExist:
                pass
        return initial
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['item_formset'] = QuotationItemFormSet(self.request.POST, self.request.FILES)
        else:
            context['item_formset'] = QuotationItemFormSet()
            
            # Pre-populate items from enquiry if available
            enquiry_id = self.request.GET.get('enquiry')
            if enquiry_id and not self.request.POST:
                try:
                    enquiry = Enquiry.objects.get(pk=enquiry_id)
                    initial_forms = []
                    for enquiry_item in enquiry.items.all():
                        initial_forms.append({
                            'enquiry_item': enquiry_item,
                            'service_category': enquiry_item.service_category,
                            'service_description': enquiry_item.service_description,
                            'specifications': enquiry_item.detailed_specifications,
                            'quantity': enquiry_item.quantity,
                            'unit': enquiry_item.unit,
                            'unit_price': enquiry_item.target_price or 0,
                        })
                    context['item_formset'] = QuotationItemFormSet(initial=initial_forms)
                except Enquiry.DoesNotExist:
                    pass
        
        return context
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        context = self.get_context_data()
        item_formset = context['item_formset']
        
        if item_formset.is_valid():
            with transaction.atomic():
                self.object = form.save()
                item_formset.instance = self.object
                item_formset.save()
                
                # Update quotation totals
                self.object.calculate_totals()
                
                # Update enquiry status
                if self.object.enquiry:
                    self.object.enquiry.status = 'quoted'
                    self.object.enquiry.save()
                
                # Handle status based on button clicked
                if 'send_quotation' in self.request.POST:
                    self.object.status = 'sent'
                    self.object.sent_date = timezone.now()
                    self.object.save()
                    messages.success(self.request, f'Quotation {self.object.quotation_number} sent successfully!')
                else:
                    messages.success(self.request, f'Quotation {self.object.quotation_number} saved as draft!')
                
            return redirect('crm:quotation_detail', pk=self.object.pk)
        else:
            return self.form_invalid(form)

class QuotationUpdateView(LoginRequiredMixin, UpdateView):
    model = Quotation
    form_class = QuotationForm
    template_name = 'crm/quotation_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['item_formset'] = QuotationItemFormSet(self.request.POST, self.request.FILES, instance=self.object)
        else:
            context['item_formset'] = QuotationItemFormSet(instance=self.object)
        return context
    
    def form_valid(self, form):
        form.instance.modified_by = self.request.user
        context = self.get_context_data()
        item_formset = context['item_formset']
        
        if item_formset.is_valid():
            with transaction.atomic():
                self.object = form.save()
                item_formset.instance = self.object
                item_formset.save()
                
                # Update quotation totals
                self.object.calculate_totals()
                
                # Handle status based on button clicked
                if 'send_quotation' in self.request.POST:
                    self.object.status = 'sent'
                    self.object.sent_date = timezone.now()
                    self.object.save()
                    messages.success(self.request, f'Quotation {self.object.quotation_number} sent successfully!')
                else:
                    messages.success(self.request, f'Quotation {self.object.quotation_number} updated successfully!')
                
            return redirect('crm:quotation_detail', pk=self.object.pk)
        else:
            return self.form_invalid(form)

class QuotationDetailView(LoginRequiredMixin, DetailView):
    model = Quotation
    template_name = 'crm/quotation_detail.html'
    context_object_name = 'quotation'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.items.all()
        context['sales_orders'] = self.object.sales_orders.all().select_related('customer')
        return context

class QuotationDeleteView(LoginRequiredMixin, DeleteView):
    model = Quotation
    template_name = 'crm/quotation_confirm_delete.html'
    success_url = reverse_lazy('crm:quotation_list')
    
    def delete(self, request, *args, **kwargs):
        quotation = self.get_object()
        messages.success(request, f'Quotation {quotation.quotation_number} deleted successfully!')
        return super().delete(request, *args, **kwargs)

# Sales Order Views
class SalesOrderListView(LoginRequiredMixin, ListView):
    model = SalesOrder
    template_name = 'crm/sales_order_list.html'
    context_object_name = 'sales_orders'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = SalesOrder.objects.select_related('quotation', 'customer', 'contact_person', 'project_manager', 'created_by').prefetch_related('items')
        
        # Filtering
        status_filter = self.request.GET.get('status')
        customer_filter = self.request.GET.get('customer')
        search_query = self.request.GET.get('search')
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if customer_filter:
            queryset = queryset.filter(customer_id=customer_filter)
        if search_query:
            queryset = queryset.filter(
                Q(order_number__icontains=search_query) |
                Q(customer__name__icontains=search_query) |
                Q(customer_po_number__icontains=search_query)
            )
        
        return queryset.order_by('-order_date', '-created_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = SalesOrder.ORDER_STATUS
        context['customers'] = SalesOrder.objects.values('customer__id', 'customer__name').distinct()
        
        # Statistics
        context['total_orders'] = SalesOrder.objects.count()
        context['in_progress_orders'] = SalesOrder.objects.filter(status='in_progress').count()
        context['completed_orders'] = SalesOrder.objects.filter(status='completed').count()
        context['overdue_orders'] = SalesOrder.objects.filter(
            expected_delivery_date__lt=timezone.now().date(),
            status__in=['draft', 'confirmed', 'planning', 'in_progress']
        ).count()
        
        return context

class SalesOrderCreateView(LoginRequiredMixin, CreateView):
    model = SalesOrder
    form_class = SalesOrderForm
    template_name = 'crm/sales_order_form.html'
    
    def get_initial(self):
        initial = super().get_initial()
        quotation_id = self.request.GET.get('quotation')
        if quotation_id:
            try:
                quotation = Quotation.objects.get(pk=quotation_id)
                initial['quotation'] = quotation
                initial['customer'] = quotation.customer
                initial['contact_person'] = quotation.contact_person
                initial['payment_terms'] = quotation.payment_terms
                initial['delivery_terms'] = quotation.delivery_terms
                initial['currency'] = quotation.currency
                initial['tax_rate'] = quotation.tax_rate
            except Quotation.DoesNotExist:
                pass
        return initial
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['item_formset'] = SalesOrderItemFormSet(self.request.POST, self.request.FILES)
        else:
            context['item_formset'] = SalesOrderItemFormSet()
            
            # Pre-populate items from quotation if available
            quotation_id = self.request.GET.get('quotation')
            if quotation_id and not self.request.POST:
                try:
                    quotation = Quotation.objects.get(pk=quotation_id)
                    initial_forms = []
                    for quotation_item in quotation.items.all():
                        initial_forms.append({
                            'quotation_item': quotation_item,
                            'service_category': quotation_item.service_category,
                            'service_description': quotation_item.service_description,
                            'specifications': quotation_item.specifications,
                            'quantity': quotation_item.quantity,
                            'unit': quotation_item.unit,
                            'unit_price': quotation_item.unit_price,
                        })
                    context['item_formset'] = SalesOrderItemFormSet(initial=initial_forms)
                except Quotation.DoesNotExist:
                    pass
        
        return context
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        context = self.get_context_data()
        item_formset = context['item_formset']
        
        if item_formset.is_valid():
            with transaction.atomic():
                self.object = form.save()
                item_formset.instance = self.object
                item_formset.save()
                
                # Update sales order totals
                self.object.calculate_totals()
                
                # Update quotation status if exists
                if self.object.quotation:
                    self.object.quotation.status = 'converted'
                    self.object.quotation.save()
                
                # Update enquiry status if exists
                if self.object.quotation and self.object.quotation.enquiry:
                    self.object.quotation.enquiry.status = 'converted'
                    self.object.quotation.enquiry.save()
                
            messages.success(self.request, f'Sales Order {self.object.order_number} created successfully!')
            return redirect('crm:sales_order_detail', pk=self.object.pk)
        else:
            return self.form_invalid(form)

class SalesOrderUpdateView(LoginRequiredMixin, UpdateView):
    model = SalesOrder
    form_class = SalesOrderForm
    template_name = 'crm/sales_order_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['item_formset'] = SalesOrderItemFormSet(self.request.POST, self.request.FILES, instance=self.object)
        else:
            context['item_formset'] = SalesOrderItemFormSet(instance=self.object)
        return context
    
    def form_valid(self, form):
        form.instance.modified_by = self.request.user
        context = self.get_context_data()
        item_formset = context['item_formset']
        
        if item_formset.is_valid():
            with transaction.atomic():
                self.object = form.save()
                item_formset.instance = self.object
                item_formset.save()
                
                # Update sales order totals
                self.object.calculate_totals()
                
            messages.success(self.request, f'Sales Order {self.object.order_number} updated successfully!')
            return redirect('crm:sales_order_detail', pk=self.object.pk)
        else:
            return self.form_invalid(form)

class SalesOrderDetailView(LoginRequiredMixin, DetailView):
    model = SalesOrder
    template_name = 'crm/sales_order_detail.html'
    context_object_name = 'sales_order'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.items.all()
        return context

class SalesOrderDeleteView(LoginRequiredMixin, DeleteView):
    model = SalesOrder
    template_name = 'crm/sales_order_confirm_delete.html'
    success_url = reverse_lazy('crm:sales_order_list')
    
    def delete(self, request, *args, **kwargs):
        sales_order = self.get_object()
        messages.success(request, f'Sales Order {sales_order.order_number} deleted successfully!')
        return super().delete(request, *args, **kwargs)

# AJAX Views
def get_contact_persons(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    customer_id = request.GET.get('customer_id')
    if customer_id:
        contact_persons = CustomerConcernPerson.objects.filter(
            customer_id=customer_id, is_active=True
        ).values('id', 'concern_person', 'designation', 'mobile_1', 'email_company')
        
        return JsonResponse(list(contact_persons), safe=False)
    return JsonResponse([], safe=False)

def get_enquiry_items(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    enquiry_id = request.GET.get('enquiry_id')
    if enquiry_id:
        items = EnquiryItem.objects.filter(enquiry_id=enquiry_id).values(
            'id', 'service_description', 'quantity', 'unit', 'target_price', 'service_category'
        )
        
        return JsonResponse(list(items), safe=False)
    return JsonResponse([], safe=False)

def update_quotation_status(request, pk):
    if not request.user.is_authenticated:
        raise PermissionDenied
    
    if request.method == 'POST':
        quotation = get_object_or_404(Quotation, pk=pk)
        new_status = request.POST.get('status')
        
        if new_status in dict(Quotation.QUOTATION_STATUS):
            quotation.status = new_status
            if new_status == 'sent':
                quotation.sent_date = timezone.now()
            elif new_status == 'accepted':
                quotation.accepted_date = timezone.now()
            elif new_status == 'acknowledged':
                quotation.acknowledged_date = timezone.now()
            quotation.save()
            
            messages.success(request, f'Quotation status updated to {new_status}')
        else:
            messages.error(request, 'Invalid status')
    
    return redirect('crm:quotation_detail', pk=pk)

def update_order_status(request, pk):
    if not request.user.is_authenticated:
        raise PermissionDenied
    
    if request.method == 'POST':
        order = get_object_or_404(SalesOrder, pk=pk)
        new_status = request.POST.get('status')
        
        if new_status in dict(SalesOrder.ORDER_STATUS):
            order.status = new_status
            if new_status == 'delivered':
                order.actual_delivery_date = timezone.now().date()
            order.save()
            
            messages.success(request, f'Sales Order status updated to {new_status}')
        else:
            messages.error(request, 'Invalid status')
    
    return redirect('crm:sales_order_detail', pk=pk)

# Formset Factories
EnquiryItemFormSet = inlineformset_factory(
    Enquiry, EnquiryItem,
    form=EnquiryItemForm,
    extra=1,
    can_delete=True,
    fields=[
        'service_category', 'service_description', 'detailed_specifications',
        'quantity', 'unit', 'crane_capacity', 'boom_length', 'working_height', 'radius',
        'location_requirements', 'safety_requirements', 'start_date', 'end_date',
        'working_hours', 'target_price', 'customer_budget', 'notes'
    ]
)

QuotationItemFormSet = inlineformset_factory(
    Quotation, QuotationItem,
    form=QuotationItemForm,
    extra=1,
    can_delete=True,
    fields=[
        'enquiry_item', 'service_category', 'service_description', 'specifications',
        'quantity', 'unit', 'unit_price', 'duration', 'equipment_details',
        'manpower_requirements', 'notes'
    ]
)

SalesOrderItemFormSet = inlineformset_factory(
    SalesOrder, SalesOrderItem,
    form=SalesOrderItemForm,
    extra=1,
    can_delete=True,
    fields=[
        'quotation_item', 'service_category', 'service_description', 'specifications',
        'quantity', 'unit', 'unit_price', 'planned_start_date', 'planned_end_date',
        'actual_start_date', 'actual_end_date', 'completed_quantity', 'assigned_equipment',
        'assigned_team', 'status', 'notes'
    ]
)