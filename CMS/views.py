# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Count, Sum, F, Avg
from django.db.models.functions import TruncMonth, TruncYear, ExtractWeek
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, timedelta
import json
from .models import *
from .forms import *

@login_required
def dashboard(request):
    """Customer Management System Dashboard"""
    # Basic statistics
    total_customers = CustomerMaster.objects.count()
    active_customers = CustomerMaster.objects.filter(is_active=True).count()
    total_concern_persons = CustomerConcernPerson.objects.count()
    active_concern_persons = CustomerConcernPerson.objects.filter(is_active=True).count()
    
    # Recent customers
    recent_customers = CustomerMaster.objects.select_related('organization_type').order_by('-created_at')[:5]
    
    # Customers by organization type
    customers_by_type = CustomerMaster.objects.values('organization_type__name').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Recent activities (simplified - in real app, you'd have an Activity model)
    recent_activities = []
    
    context = {
        'total_customers': total_customers,
        'active_customers': active_customers,
        'total_concern_persons': total_concern_persons,
        'active_concern_persons': active_concern_persons,
        'recent_customers': recent_customers,
        'customers_by_type': customers_by_type,
        'recent_activities': recent_activities,
        'title': 'Customer Management Dashboard',
    }
    return render(request, 'cms/dashboard.html', context)

@login_required
def customer_list_view(request):
    customers = CustomerMaster.objects.all().select_related('organization_type').prefetch_related('addresses', 'concern_persons')
    
    # Initialize search form
    search_form = CustomerSearchForm(request.GET or None)
    
    # Apply filters
    if search_form.is_valid():
        name = search_form.cleaned_data.get('name')
        customer_id = search_form.cleaned_data.get('customer_id')
        pan_number = search_form.cleaned_data.get('pan_number')
        organization_type = search_form.cleaned_data.get('organization_type')
        status = search_form.cleaned_data.get('status')
        
        if name:
            customers = customers.filter(name__icontains=name)
        if customer_id:
            customers = customers.filter(customer_id__icontains=customer_id)
        if pan_number:
            customers = customers.filter(pan_number__icontains=pan_number)
        if organization_type:
            customers = customers.filter(organization_type=organization_type)
        if status:
            customers = customers.filter(status=status)
    
    # Pagination
    paginator = Paginator(customers, 25)  # 25 customers per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'customers': page_obj,
        'search_form': search_form,
        'organization_types': TypeOfOrganization.objects.filter(is_active=True),
        'title': 'Customer Management',
        'page_obj': page_obj,
    }
    return render(request, 'cms/customer_list.html', context)

from django.forms import formset_factory, modelformset_factory

@login_required
def customer_create_view(request):
    # Create model formset factories
    AddressFormSet = modelformset_factory(
        CustomerAddress, 
        form=CustomerAddressForm, 
        extra=1, 
        can_delete=True
    )
    BankFormSet = modelformset_factory(
        CustomerBankDetails, 
        form=CustomerBankDetailsForm, 
        extra=1, 
        can_delete=True
    )
    ConcernFormSet = modelformset_factory(
        CustomerConcernPerson, 
        form=CustomerConcernPersonForm, 
        extra=1, 
        can_delete=True
    )
    
    if request.method == 'POST':
        customer_form = CustomerMasterForm(request.POST)
        address_formset = AddressFormSet(request.POST, prefix='addresses')
        bank_formset = BankFormSet(request.POST, prefix='bank_details')
        concern_formset = ConcernFormSet(request.POST, prefix='concern_persons')
        division_form = CustomerDivisionForm(request.POST)
        
        forms_valid = (
            customer_form.is_valid() and 
            address_formset.is_valid() and 
            bank_formset.is_valid() and 
            concern_formset.is_valid() and 
            division_form.is_valid()
        )
        
        if forms_valid:
            # Save customer first
            customer = customer_form.save(commit=False)
            customer.created_by = request.user
            customer.save()
            
            # Save addresses
            addresses = address_formset.save(commit=False)
            for address in addresses:
                address.customer = customer
                address.save()
            
            # Save bank details
            bank_details = bank_formset.save(commit=False)
            for bank_detail in bank_details:
                bank_detail.customer = customer
                bank_detail.save()
            
            # Save concern persons
            concern_persons = concern_formset.save(commit=False)
            for concern_person in concern_persons:
                concern_person.customer = customer
                concern_person.created_by = request.user
                concern_person.save()
                concern_formset.save_m2m()
            
            # Save divisions
            divisions = division_form.cleaned_data['divisions']
            for division in divisions:
                CustomerDivision.objects.create(
                    customer=customer, 
                    division=division,
                    assigned_by=request.user
                )
            
            messages.success(request, f'Customer {customer.name} created successfully!')
            return redirect('customer_detail', pk=customer.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    
    else:
        customer_form = CustomerMasterForm()
        address_formset = AddressFormSet(prefix='addresses', queryset=CustomerAddress.objects.none())
        bank_formset = BankFormSet(prefix='bank_details', queryset=CustomerBankDetails.objects.none())
        concern_formset = ConcernFormSet(prefix='concern_persons', queryset=CustomerConcernPerson.objects.none())
        division_form = CustomerDivisionForm()
    
    context = {
        'customer_form': customer_form,
        'address_forms': address_formset,
        'bank_forms': bank_formset,
        'concern_forms': concern_formset,
        'division_form': division_form,
        'states': StateUTMaster.objects.filter(is_active=True),
        'countries': CountryMaster.objects.filter(is_active=True),
        'title': 'Create New Customer',
    }
    return render(request, 'cms/customer_form.html', context)

@login_required
def customer_create_view1(request):
    # Create formset factories
    AddressFormSet = formset_factory(CustomerAddressForm, extra=1)
    BankFormSet = formset_factory(CustomerBankDetailsForm, extra=1)
    ConcernFormSet = formset_factory(CustomerConcernPersonForm, extra=1)
    
    if request.method == 'POST':
        customer_form = CustomerMasterForm(request.POST)
        address_formset = AddressFormSet(request.POST, prefix='addresses')
        bank_formset = BankFormSet(request.POST, prefix='bank_details')
        concern_formset = ConcernFormSet(request.POST, prefix='concern_persons')
        division_form = CustomerDivisionForm(request.POST)
        
        forms_valid = customer_form.is_valid()
        
        if forms_valid:
            customer = customer_form.save(commit=False)
            customer.created_by = request.user
            customer.save()
            
            # Save addresses
            if address_formset.is_valid():
                for form in address_formset:
                    if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                        address = form.save(commit=False)
                        address.customer = customer
                        address.save()
            
            # Save bank details
            if bank_formset.is_valid():
                for form in bank_formset:
                    if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                        bank_detail = form.save(commit=False)
                        bank_detail.customer = customer
                        bank_detail.save()
            
            # Save concern persons
            if concern_formset.is_valid():
                for form in concern_formset:
                    if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                        concern_person = form.save(commit=False)
                        concern_person.customer = customer
                        concern_person.created_by = request.user
                        concern_person.save()
                        form.save_m2m()
            
            # Save divisions
            if division_form.is_valid():
                divisions = division_form.cleaned_data['divisions']
                for division in divisions:
                    CustomerDivision.objects.create(
                        customer=customer, 
                        division=division,
                        assigned_by=request.user
                    )
            
            messages.success(request, f'Customer {customer.name} created successfully!')
            return redirect('customer_detail', pk=customer.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    
    else:
        customer_form = CustomerMasterForm()
        address_formset = AddressFormSet(prefix='addresses')
        bank_formset = BankFormSet(prefix='bank_details')
        concern_formset = ConcernFormSet(prefix='concern_persons')
        division_form = CustomerDivisionForm()
    
    context = {
        'customer_form': customer_form,
        'address_forms': address_formset,
        'bank_forms': bank_formset,
        'concern_forms': concern_formset,
        'division_form': division_form,
        'states': StateUTMaster.objects.filter(is_active=True),
        'countries': CountryMaster.objects.filter(is_active=True),
        'title': 'Create New Customer',
    }
    return render(request, 'cms/customer_form.html', context)

@login_required
def customer_update_view(request, pk):
    customer = get_object_or_404(CustomerMaster, pk=pk)
    
    # Create model formset factories
    AddressFormSet = modelformset_factory(
        CustomerAddress, 
        form=CustomerAddressForm, 
        extra=1, 
        can_delete=True
    )
    BankFormSet = modelformset_factory(
        CustomerBankDetails, 
        form=CustomerBankDetailsForm, 
        extra=1, 
        can_delete=True
    )
    ConcernFormSet = modelformset_factory(
        CustomerConcernPerson, 
        form=CustomerConcernPersonForm, 
        extra=1, 
        can_delete=True
    )
    
    if request.method == 'POST':
        customer_form = CustomerMasterForm(request.POST, instance=customer)
        address_formset = AddressFormSet(
            request.POST, 
            prefix='addresses',
            queryset=CustomerAddress.objects.filter(customer=customer)
        )
        bank_formset = BankFormSet(
            request.POST, 
            prefix='bank_details',
            queryset=CustomerBankDetails.objects.filter(customer=customer)
        )
        concern_formset = ConcernFormSet(
            request.POST, 
            prefix='concern_persons',
            queryset=CustomerConcernPerson.objects.filter(customer=customer)
        )
        division_form = CustomerDivisionForm(request.POST)
        
        forms_valid = (
            customer_form.is_valid() and 
            address_formset.is_valid() and 
            bank_formset.is_valid() and 
            concern_formset.is_valid() and 
            division_form.is_valid()
        )
        
        if forms_valid:
            # Save customer
            customer = customer_form.save()
            
            # Save addresses
            addresses = address_formset.save(commit=False)
            for address in addresses:
                address.customer = customer
                address.save()
            for address in address_formset.deleted_objects:
                address.delete()
            
            # Save bank details
            bank_details = bank_formset.save(commit=False)
            for bank_detail in bank_details:
                bank_detail.customer = customer
                bank_detail.save()
            for bank_detail in bank_formset.deleted_objects:
                bank_detail.delete()
            
            # Save concern persons
            concern_persons = concern_formset.save(commit=False)
            for concern_person in concern_persons:
                concern_person.customer = customer
                if not concern_person.pk:  # New object
                    concern_person.created_by = request.user
                concern_person.save()
                concern_formset.save_m2m()
            for concern_person in concern_formset.deleted_objects:
                concern_person.delete()
            
            # Save divisions
            customer.divisions.all().delete()
            divisions = division_form.cleaned_data['divisions']
            for division in divisions:
                CustomerDivision.objects.create(
                    customer=customer, 
                    division=division,
                    assigned_by=request.user
                )
            
            messages.success(request, f'Customer {customer.name} updated successfully!')
            return redirect('customer_detail', pk=customer.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    
    else:
        customer_form = CustomerMasterForm(instance=customer)
        
        address_formset = AddressFormSet(
            prefix='addresses',
            queryset=CustomerAddress.objects.filter(customer=customer)
        )
        bank_formset = BankFormSet(
            prefix='bank_details',
            queryset=CustomerBankDetails.objects.filter(customer=customer)
        )
        concern_formset = ConcernFormSet(
            prefix='concern_persons',
            queryset=CustomerConcernPerson.objects.filter(customer=customer)
        )
        
        # Set initial divisions
        existing_divisions = customer.divisions.values_list('division_id', flat=True)
        division_initial = {'divisions': existing_divisions}
        division_form = CustomerDivisionForm(initial=division_initial)
    
    context = {
        'customer_form': customer_form,
        'address_forms': address_formset,
        'bank_forms': bank_formset,
        'concern_forms': concern_formset,
        'division_form': division_form,
        'customer': customer,
        'states': StateUTMaster.objects.filter(is_active=True),
        'countries': CountryMaster.objects.filter(is_active=True),
        'title': f'Update {customer.name}',
    }
    return render(request, 'cms/customer_form.html', context)

@login_required
def customer_update_view1(request, pk):
    customer = get_object_or_404(CustomerMaster, pk=pk)
    
    # Get existing related objects
    addresses = customer.addresses.all()
    bank_details = customer.bank_details.all()
    concern_persons = customer.concern_persons.all()
    existing_divisions = customer.divisions.values_list('division_id', flat=True)
    
    # Create formset factories with initial data
    AddressFormSet = formset_factory(CustomerAddressForm, extra=1, can_delete=True)
    BankFormSet = formset_factory(CustomerBankDetailsForm, extra=1, can_delete=True)
    ConcernFormSet = formset_factory(CustomerConcernPersonForm, extra=1, can_delete=True)
    
    if request.method == 'POST':
        customer_form = CustomerMasterForm(request.POST, instance=customer)
        address_formset = AddressFormSet(request.POST, prefix='addresses')
        bank_formset = BankFormSet(request.POST, prefix='bank_details')
        concern_formset = ConcernFormSet(request.POST, prefix='concern_persons')
        division_form = CustomerDivisionForm(request.POST)
        
        forms_valid = customer_form.is_valid()
        
        if forms_valid:
            customer = customer_form.save()
            
            # Process addresses
            if address_formset.is_valid():
                # Delete existing addresses first (for simplicity, in production you'd want more sophisticated handling)
                customer.addresses.all().delete()
                
                for form in address_formset:
                    if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                        address = form.save(commit=False)
                        address.customer = customer
                        address.save()
            
            # Process bank details
            if bank_formset.is_valid():
                # Delete existing bank details
                customer.bank_details.all().delete()
                
                for form in bank_formset:
                    if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                        bank_detail = form.save(commit=False)
                        bank_detail.customer = customer
                        bank_detail.save()
            
            # Process concern persons
            if concern_formset.is_valid():
                # Delete existing concern persons
                customer.concern_persons.all().delete()
                
                for form in concern_formset:
                    if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                        concern_person = form.save(commit=False)
                        concern_person.customer = customer
                        concern_person.created_by = request.user
                        concern_person.save()
                        form.save_m2m()
            
            # Process divisions
            if division_form.is_valid():
                # Update divisions
                customer.divisions.all().delete()
                divisions = division_form.cleaned_data['divisions']
                for division in divisions:
                    CustomerDivision.objects.create(
                        customer=customer, 
                        division=division,
                        assigned_by=request.user
                    )
            
            messages.success(request, f'Customer {customer.name} updated successfully!')
            return redirect('customer_detail', pk=customer.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    
    else:
        # Prepopulate forms with existing data
        customer_form = CustomerMasterForm(instance=customer)
        
        # Prepare initial data for formsets
        address_initial = []
        for address in addresses:
            address_initial.append({
                'branch_category': address.branch_category,
                'address': address.address,
                'state': address.state,
                'country': address.country,
                'pincode': address.pincode,
                'location': address.location,
                'google_location': address.google_location,
                'telephone': address.telephone,
                'email': address.email,
                'gst_number': address.gst_number,
                'is_primary': address.is_primary,
                'is_active': address.is_active,
            })
        
        bank_initial = []
        for bank in bank_details:
            bank_initial.append({
                'bank_name': bank.bank_name,
                'account_number': bank.account_number,
                'account_holder_name': bank.account_holder_name,
                'branch_name': bank.branch_name,
                'ifsc_code': bank.ifsc_code,
                'account_type': bank.account_type,
                'is_primary': bank.is_primary,
                'is_active': bank.is_active,
            })
        
        concern_initial = []
        for concern in concern_persons:
            concern_initial.append({
                'concern_person': concern.concern_person,
                'designation': concern.designation,
                'mobile_1': concern.mobile_1,
                'mobile_2': concern.mobile_2,
                'office_phone_1': concern.office_phone_1,
                'office_extension_1': concern.office_extension_1,
                'office_phone_2': concern.office_phone_2,
                'email_company': concern.email_company,
                'email_personal': concern.email_personal,
                'remarks': concern.remarks,
                'is_active': concern.is_active,
                'is_primary_contact': concern.is_primary_contact,
            })
        
        address_formset = AddressFormSet(initial=address_initial, prefix='addresses')
        bank_formset = BankFormSet(initial=bank_initial, prefix='bank_details')
        concern_formset = ConcernFormSet(initial=concern_initial, prefix='concern_persons')
        
        # Set initial divisions
        division_initial = {'divisions': existing_divisions}
        division_form = CustomerDivisionForm(initial=division_initial)
    
    context = {
        'customer_form': customer_form,
        'address_forms': address_formset,
        'bank_forms': bank_formset,
        'concern_forms': concern_formset,
        'division_form': division_form,
        'customer': customer,
        'states': StateUTMaster.objects.filter(is_active=True),
        'countries': CountryMaster.objects.filter(is_active=True),
        'title': f'Update {customer.name}',
    }
    return render(request, 'cms/customer_form.html', context)

@login_required
def customer_detail_view(request, pk):
    customer = get_object_or_404(CustomerMaster, pk=pk)
    addresses = customer.addresses.all()
    bank_details = customer.bank_details.all()
    divisions = customer.divisions.select_related('division')
    concern_persons = customer.concern_persons.select_related('country_1', 'country_2', 'address').prefetch_related('concern_for')
    documents = customer.documents.all()
    notes = customer.notes.all()
    
    # Forms for inline additions
    address_form = CustomerAddressForm()
    bank_form = CustomerBankDetailsForm()
    document_form = CustomerDocumentForm()
    note_form = CustomerNoteForm()
    
    context = {
        'customer': customer,
        'addresses': addresses,
        'bank_details': bank_details,
        'divisions': divisions,
        'concern_persons': concern_persons,
        'documents': documents,
        'notes': notes,
        'address_form': address_form,
        'bank_form': bank_form,
        'document_form': document_form,
        'note_form': note_form,
        'title': f'Customer Details - {customer.name}',
    }
    return render(request, 'cms/customer_detail.html', context)

@login_required
def customer_toggle_status(request, pk):
    customer = get_object_or_404(CustomerMaster, pk=pk)
    customer.is_active = not customer.is_active
    customer.save()
    
    action = "activated" if customer.is_active else "deactivated"
    messages.success(request, f'Customer {customer.name} has been {action}.')
    
    return redirect('customer_detail', pk=customer.pk)

@login_required
@require_http_methods(["POST"])
def check_customer_name(request):
    name = request.POST.get('name', '')
    customer_id = request.POST.get('customer_id', '')
    
    if customer_id:  # Update case
        exists = CustomerMaster.objects.filter(name=name).exclude(pk=customer_id).exists()
    else:  # Create case
        exists = CustomerMaster.objects.filter(name=name).exists()
    
    return JsonResponse({'exists': exists, 'name': name})

@login_required
def add_customer_address(request, customer_pk):
    customer = get_object_or_404(CustomerMaster, pk=customer_pk)
    
    if request.method == 'POST':
        form = CustomerAddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.customer = customer
            address.save()
            messages.success(request, 'Address added successfully!')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Address added successfully!'})
            return redirect('customer_detail', pk=customer.pk)
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors})
    
    else:
        form = CustomerAddressForm()
    
    context = {
        'form': form,
        'customer': customer,
        'title': f'Add Address - {customer.name}',
    }
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'cms/partials/address_form.html', context)
    return render(request, 'cms/partials/address_form.html', context)

@login_required
def update_customer_address(request, pk):
    address = get_object_or_404(CustomerAddress, pk=pk)
    
    if request.method == 'POST':
        form = CustomerAddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, 'Address updated successfully!')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Address updated successfully!'})
            return redirect('customer_detail', pk=address.customer.pk)
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors})
    
    else:
        form = CustomerAddressForm(instance=address)
    
    context = {
        'form': form,
        'address': address,
        'title': f'Update Address - {address.customer.name}',
    }
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'cms/partials/address_form.html', context)
    return render(request, 'cms/partials/address_form.html', context)

@login_required
def delete_customer_address(request, pk):
    address = get_object_or_404(CustomerAddress, pk=pk)
    customer_pk = address.customer.pk
    
    if request.method == 'POST':
        address.delete()
        messages.success(request, 'Address deleted successfully!')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Address deleted successfully!'})
    
    return redirect('customer_detail', pk=customer_pk)

@login_required
def add_customer_bank_detail(request, customer_pk):
    customer = get_object_or_404(CustomerMaster, pk=customer_pk)
    
    if request.method == 'POST':
        form = CustomerBankDetailsForm(request.POST)
        if form.is_valid():
            bank_detail = form.save(commit=False)
            bank_detail.customer = customer
            bank_detail.save()
            messages.success(request, 'Bank details added successfully!')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Bank details added successfully!'})
            return redirect('customer_detail', pk=customer.pk)
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors})
    
    else:
        form = CustomerBankDetailsForm()
    
    context = {
        'form': form,
        'customer': customer,
        'title': f'Add Bank Details - {customer.name}',
    }
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'cms/partials/bank_form.html', context)
    return render(request, 'cms/partials/bank_form.html', context)

@login_required
def update_customer_bank_detail(request, pk):
    bank_detail = get_object_or_404(CustomerBankDetails, pk=pk)
    
    if request.method == 'POST':
        form = CustomerBankDetailsForm(request.POST, instance=bank_detail)
        if form.is_valid():
            form.save()
            messages.success(request, 'Bank details updated successfully!')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Bank details updated successfully!'})
            return redirect('customer_detail', pk=bank_detail.customer.pk)
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors})
    
    else:
        form = CustomerBankDetailsForm(instance=bank_detail)
    
    context = {
        'form': form,
        'bank_detail': bank_detail,
        'title': f'Update Bank Details - {bank_detail.customer.name}',
    }
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'cms/partials/bank_form.html', context)
    return render(request, 'cms/partials/bank_form.html', context)

@login_required
def delete_customer_bank_detail(request, pk):
    bank_detail = get_object_or_404(CustomerBankDetails, pk=pk)
    customer_pk = bank_detail.customer.pk
    
    if request.method == 'POST':
        bank_detail.delete()
        messages.success(request, 'Bank details deleted successfully!')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Bank details deleted successfully!'})
    
    return redirect('customer_detail', pk=customer_pk)

# Concern Person Views (already provided in previous response, but ensure they're complete)
@login_required
def customer_concern_person_create(request, customer_pk=None):
    customer = None
    if customer_pk:
        customer = get_object_or_404(CustomerMaster, pk=customer_pk)
    
    if request.method == 'POST':
        form = CustomerConcernPersonForm(request.POST)
        if form.is_valid():
            concern_person = form.save(commit=False)
            concern_person.created_by = request.user
            concern_person.save()
            form.save_m2m()  # Save many-to-many data
            
            messages.success(request, f'Concern person {concern_person.concern_person} added successfully!')
            
            if customer:
                return redirect('customer_detail', pk=customer.pk)
            else:
                return redirect('concern_person_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        initial = {}
        if customer:
            initial['customer'] = customer
        form = CustomerConcernPersonForm(initial=initial)
    
    context = {
        'form': form,
        'customer': customer,
        'title': 'Add Concern Person' + (f' - {customer.name}' if customer else ''),
    }
    return render(request, 'cms/concern_person_form.html', context)

@login_required
def customer_concern_person_update(request, pk):
    concern_person = get_object_or_404(CustomerConcernPerson, pk=pk)
    
    if request.method == 'POST':
        form = CustomerConcernPersonForm(request.POST, instance=concern_person)
        if form.is_valid():
            form.save()
            form.save_m2m()
            messages.success(request, f'Concern person {concern_person.concern_person} updated successfully!')
            return redirect('customer_detail', pk=concern_person.customer.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomerConcernPersonForm(instance=concern_person)
    
    context = {
        'form': form,
        'concern_person': concern_person,
        'title': f'Update {concern_person.concern_person}',
    }
    return render(request, 'cms/concern_person_form.html', context)

@login_required
def concern_person_list(request):
    concern_persons = CustomerConcernPerson.objects.all().select_related(
        'customer', 'address', 'country_1', 'country_2'
    ).prefetch_related('concern_for')
    
    # Filtering
    customer_filter = request.GET.get('customer')
    active_filter = request.GET.get('active')
    
    if customer_filter:
        concern_persons = concern_persons.filter(customer_id=customer_filter)
    if active_filter:
        concern_persons = concern_persons.filter(is_active=active_filter == 'true')
    
    # Pagination
    paginator = Paginator(concern_persons, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'concern_persons': page_obj,
        'customers': CustomerMaster.objects.filter(is_active=True),
        'title': 'Concern Persons Management',
        'page_obj': page_obj,
    }
    return render(request, 'cms/concern_person_list.html', context)

@login_required
def add_quick_concern_person(request, customer_pk):
    customer = get_object_or_404(CustomerMaster, pk=customer_pk)
    
    if request.method == 'POST':
        form = ConcernPersonQuickForm(request.POST)
        if form.is_valid():
            concern_person = form.save(commit=False)
            concern_person.customer = customer
            concern_person.created_by = request.user
            
            # Set default country to India
            try:
                india = CountryMaster.objects.get(name='India')
                concern_person.country_1 = india
            except CountryMaster.DoesNotExist:
                pass
            
            concern_person.save()
            messages.success(request, f'Concern person {concern_person.concern_person} added successfully!')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Concern person added successfully!'})
            return redirect('customer_detail', pk=customer.pk)
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors})
    
    else:
        form = ConcernPersonQuickForm()
    
    context = {
        'form': form,
        'customer': customer,
        'title': f'Add Concern Person - {customer.name}',
    }
    return render(request, 'cms/partials/quick_concern_form.html', context)

@login_required
def toggle_concern_person_status(request, pk):
    concern_person = get_object_or_404(CustomerConcernPerson, pk=pk)
    concern_person.is_active = not concern_person.is_active
    concern_person.save()
    
    action = "activated" if concern_person.is_active else "deactivated"
    message = f'Concern person {concern_person.concern_person} has been {action}.'
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'is_active': concern_person.is_active,
            'message': message
        })
    
    messages.success(request, message)
    return redirect('customer_detail', pk=concern_person.customer.pk)

@login_required
def delete_concern_person(request, pk):
    concern_person = get_object_or_404(CustomerConcernPerson, pk=pk)
    customer_pk = concern_person.customer.pk
    
    if request.method == 'POST':
        concern_person_name = concern_person.concern_person
        concern_person.delete()
        messages.success(request, f'Concern person {concern_person_name} deleted successfully!')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Concern person deleted successfully!'})
    
    return redirect('customer_detail', pk=customer_pk)

@login_required
def get_customer_addresses(request, customer_pk):
    customer = get_object_or_404(CustomerMaster, pk=customer_pk)
    branch_category = request.GET.get('branch_category')
    
    addresses = customer.addresses.filter(is_active=True)
    if branch_category:
        addresses = addresses.filter(branch_category=branch_category)
    
    address_options = '<option value="">[Select Address]</option>'
    for address in addresses:
        address_text = f"{address.get_branch_category_display()} - {address.address[:50]}..."
        if len(address.address) > 50:
            address_text += "..."
        address_options += f'<option value="{address.pk}">{address_text}</option>'
    
    return JsonResponse({'addresses': address_options})

# Document Management Views
@login_required
def add_customer_document(request, customer_pk):
    customer = get_object_or_404(CustomerMaster, pk=customer_pk)
    
    if request.method == 'POST':
        form = CustomerDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.customer = customer
            document.uploaded_by = request.user
            document.save()
            messages.success(request, 'Document uploaded successfully!')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Document uploaded successfully!'})
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors})
    
    return redirect('customer_detail', pk=customer.pk)

@login_required
def verify_customer_document(request, pk):
    document = get_object_or_404(CustomerDocument, pk=pk)
    
    if request.method == 'POST':
        document.is_verified = True
        document.verified_by = request.user
        document.verified_at = timezone.now()
        document.save()
        
        messages.success(request, 'Document verified successfully!')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Document verified successfully!'})
    
    return redirect('customer_detail', pk=document.customer.pk)

@login_required
def delete_customer_document(request, pk):
    document = get_object_or_404(CustomerDocument, pk=pk)
    customer_pk = document.customer.pk
    
    if request.method == 'POST':
        document.delete()
        messages.success(request, 'Document deleted successfully!')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Document deleted successfully!'})
    
    return redirect('customer_detail', pk=customer_pk)

# Note Management Views
@login_required
def add_customer_note(request, customer_pk):
    customer = get_object_or_404(CustomerMaster, pk=customer_pk)
    
    if request.method == 'POST':
        form = CustomerNoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.customer = customer
            note.created_by = request.user
            note.save()
            messages.success(request, 'Note added successfully!')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Note added successfully!'})
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors})
    
    return redirect('customer_detail', pk=customer.pk)

@login_required
def resolve_customer_note(request, pk):
    note = get_object_or_404(CustomerNote, pk=pk)
    
    if request.method == 'POST':
        note.is_resolved = True
        note.resolved_by = request.user
        note.resolved_at = timezone.now()
        note.save()
        
        messages.success(request, 'Note marked as resolved!')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Note marked as resolved!'})
    
    return redirect('customer_detail', pk=note.customer.pk)

@login_required
def delete_customer_note(request, pk):
    note = get_object_or_404(CustomerNote, pk=pk)
    customer_pk = note.customer.pk
    
    if request.method == 'POST':
        note.delete()
        messages.success(request, 'Note deleted successfully!')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Note deleted successfully!'})
    
    return redirect('customer_detail', pk=customer_pk)

# Export and Reporting Views
@login_required
def export_customers_csv(request):
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="customers.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Customer ID', 'Name', 'Organization Type', 'PAN', 'Status', 'Credit Limit', 'Created Date'])
    
    customers = CustomerMaster.objects.all().select_related('organization_type')
    for customer in customers:
        writer.writerow([
            customer.customer_id,
            customer.name,
            customer.organization_type.name,
            customer.pan_number,
            customer.get_status_display(),
            customer.credit_limit,
            customer.created_at.strftime('%Y-%m-%d')
        ])
    
    return response

@login_required
def customer_reports(request):
    # Basic report data
    customers_by_status = CustomerMaster.objects.values('status').annotate(
        count=Count('id')
    )
    
    customers_by_org_type = CustomerMaster.objects.values('organization_type__name').annotate(
        count=Count('id')
    ).order_by('-count')
    
    top_customers_by_credit = CustomerMaster.objects.filter(
        credit_limit__gt=0
    ).order_by('-credit_limit')[:10]
    
    recent_customers = CustomerMaster.objects.order_by('-created_at')[:10]
    
    context = {
        'customers_by_status': customers_by_status,
        'customers_by_org_type': customers_by_org_type,
        'top_customers_by_credit': top_customers_by_credit,
        'recent_customers': recent_customers,
        'title': 'Customer Reports',
    }
    return render(request, 'cms/customer_reports.html', context)

