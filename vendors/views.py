from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.db import transaction
from django.db.models import Q, Count
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.utils import timezone

from CMS.models import StateUTMaster
from .models import *
from .forms import *
import json

@login_required
def vendor_dashboard(request):
    # Dashboard statistics
    total_vendors = Vendor.objects.count()
    active_vendors = Vendor.objects.filter(is_active=True).count()
    msme_vendors = Vendor.objects.filter(is_msme=True).count()
    blacklisted_vendors = Vendor.objects.filter(is_blacklisted=True).count()
    
    # Status breakdown
    status_counts = Vendor.objects.values('status').annotate(count=Count('id'))
    status_data = {item['status']: item['count'] for item in status_counts}
    
    # Recent activities
    recent_vendors = Vendor.objects.select_related('created_by').order_by('-created_at')[:5]
    recent_approvals = VendorApprovalLog.objects.select_related('vendor', 'performed_by').order_by('-performed_at')[:10]
    
    # Company type distribution
    company_type_counts = Vendor.objects.values('company_type').annotate(count=Count('id'))
    
    context = {
        'total_vendors': total_vendors,
        'active_vendors': active_vendors,
        'msme_vendors': msme_vendors,
        'blacklisted_vendors': blacklisted_vendors,
        'status_data': status_data,
        'recent_vendors': recent_vendors,
        'recent_approvals': recent_approvals,
        'company_type_counts': company_type_counts,
    }
    return render(request, 'vendors/dashboard.html', context)

from django.db.models import Q
from django.views.generic import ListView

def vendor_list(request):
    # Fetch all vendors from DB (you can add filters later)
    vendors = Vendor.objects.all().order_by('-id')
    
    # Pass the vendors to the template
    return render(request, 'vendors/vendor_list.html', {'vendors': vendors})

@login_required
def vendor_wizard(request, step=1, vendor_id=None):
    """Complete vendor registration wizard with full error handling"""
    vendor = None
    if vendor_id:
        vendor = get_object_or_404(Vendor, id=vendor_id)
    
    # steps = {
    #     1: ('Basic Information', VendorBasicForm),
    #     2: ('PAN & MSME Details', VendorPANForm),
    #     3: ('Dates & Preferences', VendorDatesForm),
    #     4: ('Contact Details', None),
    #     5: ('Banking Information', None),
    #     6: ('Financial Information', None),
    #     7: ('Statutory & Compliance', None),
    #     8: ('Quality Systems', None),
    #     9: ('Manpower & References', None),
    #     10: ('Documents & Finalize', None),
    # }
    
    steps = {
        1: ('Basic Information', VendorBasicForm),
        2: ('PAN & MSME Details', VendorPANForm),
        3: ('Dates & Preferences', VendorDatesForm),
        4: ('Contact Details', VendorContactForm),
        5: ('Banking Information',VendorBankForm),
        6: ('Financial Information', VendorFinancialForm),
        7: ('Statutory & Compliance', VendorStatutoryForm),
        8: ('Sister Concerns', VendorSisterConcernForm),
        9: ('Customer References & Dealerships',VendorCustomerReferenceForm),
        10: ('Concern Person Details', VendorConcernPersonForm), 
        11: ('References & Relations', VendorReferenceForm),  
        12: ('Quality Systems', VendorQualitySystemForm),
        13: ('Manpower Details', VendorManpowerForm),
        14: ('Documents & Finalize', VendorDocumentForm),
    }
    

    current_step = step
    total_steps = len(steps)
    
    # Validate step range
    if current_step < 1 or current_step > total_steps:
        messages.error(request, 'Invalid step number')
        return redirect('vendors:vendor_dashboard')
    
    # Handle POST requests
    if request.method == 'POST':
        form_class = steps[current_step][1]
        
        if form_class:
            form = form_class(request.POST, request.FILES, instance=vendor)
            if form.is_valid():
                try:
                    if not vendor:
                        vendor = form.save(commit=False)
                        vendor.created_by = request.user
                        vendor.save()
                        # Save many-to-many fields
                        form.save_m2m()
                    else:
                        form.save()
                    
                    # Handle final submission
                    if 'submit_final' in request.POST:
                        if _validate_vendor_completion(vendor):
                            vendor.status = 'submitted'
                            vendor.submitted_date = timezone.now()
                            vendor.save()
                            
                            VendorApprovalLog.objects.create(
                                vendor=vendor,
                                action='submitted',
                                performed_by=request.user,
                                notes='Vendor registration submitted for review'
                            )
                            
                            messages.success(request, 'Vendor registration submitted successfully!')
                            return redirect('vendors:vendor_detail', pk=vendor.id)
                        else:
                            messages.error(request, 'Please complete all required fields before submission')
                            return redirect('vendors:vendor_wizard_step', step=current_step, vendor_id=vendor.id)
                    
                    # Handle navigation
                    if 'save_and_continue' in request.POST:
                        next_step = current_step + 1
                        if next_step <= total_steps:
                            return redirect('vendors:vendor_wizard_step', step=next_step, vendor_id=vendor.id)
                    
                    elif 'save_and_exit' in request.POST:
                        return redirect('vendors:vendor_detail', pk=vendor.id)
                        
                except Exception as e:
                    messages.error(request, f'Error saving data: {str(e)}')
            else:
                # Form validation failed
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field}: {error}')
        else:
            # Steps without main forms (4, 5, 6, 8, 9, 10)
            if 'save_and_continue' in request.POST:
                next_step = current_step + 1
                if next_step <= total_steps:
                    return redirect('vendors:vendor_wizard_step', step=next_step, vendor_id=vendor.id)
    
    # Handle GET requests
    form_class = steps[current_step][1]
    if form_class:
        form = form_class(instance=vendor)
    else:
        form = None
    
    # Build context with all required data
    context = _build_wizard_context(current_step, steps, form, vendor, request)
    
    template_name = f'vendors/vendor_wizard/step{current_step}.html'
    return render(request, template_name, context)

def _validate_vendor_completion(vendor):
    """Validate that vendor has all required data before submission"""
    required_fields = [
        vendor.company_name,
        vendor.pan_number,
        vendor.country,
        vendor.company_type,
    ]
    
    # Check basic required fields
    if not all(required_fields):
        return False
    
    # Check for at least one contact
    if not vendor.contacts.exists():
        return False
    
    # Check for at least one bank account
    if not vendor.bank_details.exists():
        return False
    
    # Check for primary contact
    if not vendor.contacts.filter(is_primary=True).exists():
        return False
    
    return True

def _build_wizard_context(current_step, steps, form, vendor, request):
    """Build comprehensive context for wizard steps"""
    step_list = [
        {"number": num, "title": name}
        for num, (name, form) in steps.items()
    ]
    if request.user.is_authenticated ==True:                
                global user,role_id
                user = request.user.id    
                role_id = request.user.role_id 
    context = {
        'current_step': current_step,
        'total_steps': len(steps),
        'steps': steps,
        'form': form,
        'vendor': vendor,
        'role_id': role_id,
        'step_list': step_list,
        'step_title': steps.get(current_step, ('Unknown Step', None))[0],
    }
    
    # Step-specific context data
    if current_step == 4 and vendor:
        context.update({
            'contacts': vendor.contacts.all(),
            'contact_form': VendorContactForm(),
            'states': StateUTMaster.objects.all(),
        })
        
    elif current_step == 5 and vendor:
        context.update({
            'bank_details': vendor.bank_details.all(),
            'bank_form': VendorBankForm(),
        })
        
    elif current_step == 6 and vendor:
        context.update({
            'financial_info': vendor.financial_info.all().order_by('-year'),
            'financial_form': VendorFinancialForm(),
        })
        
    elif current_step == 7 and vendor:
        statutory_instance, created = VendorStatutory.objects.get_or_create(vendor=vendor)
        context.update({
            'statutory_form': VendorStatutoryForm(instance=statutory_instance),
        })
        
    elif current_step == 8 and vendor:
        context.update({
            'quality_systems': vendor.quality_systems.all().order_by('-valid_upto'),
            'quality_form': VendorQualitySystemForm(),
        })
        
    elif current_step == 9 and vendor:
        manpower_instance, created = VendorManpower.objects.get_or_create(vendor=vendor)
        reference_instance, created = VendorReference.objects.get_or_create(vendor=vendor)
        
        context.update({
            'manpower_form': VendorManpowerForm(instance=manpower_instance),
            'customer_references': vendor.customer_references.all().order_by('-percentage'),
            'customer_reference_form': VendorCustomerReferenceForm(),
            'dealerships': vendor.dealerships.all(),
            'dealership_form': VendorDealershipForm(),
            'reference_form': VendorReferenceForm(instance=reference_instance),
            'concern_persons': vendor.concern_persons.all(),
            'concern_form': VendorConcernPersonForm(),
        })
        
    elif current_step == 10 and vendor:
        context.update({
            'documents': vendor.documents.all().order_by('-uploaded_at'),
            'document_form': VendorDocumentForm(),
        })
    
    return context

@login_required
def add_sister_concern(request, vendor_id):
    """Add sister concern for vendor"""
    vendor = get_object_or_404(Vendor, id=vendor_id)
    
    if request.method == 'POST':
        form = VendorSisterConcernForm(request.POST)
        if form.is_valid():
            sister_concern = form.save(commit=False)
            sister_concern.vendor = vendor
            sister_concern.save()
            messages.success(request, 'Sister concern added successfully')
        else:
            for error in form.errors:
                messages.error(request, f'Error in {error}: {form.errors[error]}')
    
    return redirect('vendors:vendor_wizard_step', step=8, vendor_id=vendor.id)

@login_required
def delete_sister_concern(request, sister_concern_id):
    """Delete sister concern"""
    sister_concern = get_object_or_404(VendorSisterConcern, id=sister_concern_id)
    vendor_id = sister_concern.vendor.id
    sister_concern.delete()
    messages.success(request, 'Sister concern deleted successfully')
    return redirect('vendors:vendor_wizard_step', step=8, vendor_id=vendor_id)

@login_required
def add_vendor_contact(request, vendor_id):
    vendor = get_object_or_404(Vendor, id=vendor_id)
    if request.method == 'POST':
        form = VendorContactForm(request.POST, request.FILES)
        if form.is_valid():
            contact = form.save(commit=False)
            contact.vendor = vendor
            
            # If this is set as primary, unset others
            if contact.is_primary:
                vendor.contacts.update(is_primary=False)
            
            contact.save()
            messages.success(request, 'Contact address added successfully')
        else:
            for error in form.errors:
                messages.error(request, f'Error in {error}: {form.errors[error]}')
    
    return redirect('vendor_wizard_step', step=4, vendor_id=vendor.id)

@login_required
def delete_vendor_contact(request, contact_id):
    contact = get_object_or_404(VendorContact, id=contact_id)
    vendor_id = contact.vendor.id
    contact.delete()
    messages.success(request, 'Contact address deleted successfully')
    return redirect('vendor_wizard_step', step=4, vendor_id=vendor_id)

@login_required
def add_vendor_bank(request, vendor_id):
    vendor = get_object_or_404(Vendor, id=vendor_id)
    if request.method == 'POST':
        form = VendorBankForm(request.POST, request.FILES)
        if form.is_valid():
            bank_detail = form.save(commit=False)
            bank_detail.vendor = vendor
            
            # If this is set as primary, unset others
            if bank_detail.is_primary:
                vendor.bank_details.update(is_primary=False)
            
            bank_detail.save()
            messages.success(request, 'Bank details added successfully')
        else:
            for error in form.errors:
                messages.error(request, f'Error in {error}: {form.errors[error]}')
    
    return redirect('vendor_wizard_step', step=5, vendor_id=vendor.id)

@login_required
def delete_vendor_bank(request, bank_id):
    bank_detail = get_object_or_404(VendorBankDetail, id=bank_id)
    vendor_id = bank_detail.vendor.id
    bank_detail.delete()
    messages.success(request, 'Bank details deleted successfully')
    return redirect('vendor_wizard_step', step=5, vendor_id=vendor_id)

@login_required
def add_financial_info(request, vendor_id):
    vendor = get_object_or_404(Vendor, id=vendor_id)
    if request.method == 'POST':
        form = VendorFinancialForm(request.POST)
        if form.is_valid():
            financial_info = form.save(commit=False)
            financial_info.vendor = vendor
            financial_info.save()
            messages.success(request, 'Financial information added successfully')
        else:
            for error in form.errors:
                messages.error(request, f'Error in {error}: {form.errors[error]}')
    
    return redirect('vendor_wizard_step', step=6, vendor_id=vendor.id)

@login_required
def delete_financial_info(request, financial_id):
    financial_info = get_object_or_404(VendorFinancialInfo, id=financial_id)
    vendor_id = financial_info.vendor.id
    financial_info.delete()
    messages.success(request, 'Financial information deleted successfully')
    return redirect('vendor_wizard_step', step=6, vendor_id=vendor_id)

@login_required
def save_statutory_details(request, vendor_id):
    vendor = get_object_or_404(Vendor, id=vendor_id)
    if request.method == 'POST':
        statutory_instance = vendor.statutory_details.first()
        form = VendorStatutoryForm(request.POST, instance=statutory_instance)
        if form.is_valid():
            statutory = form.save(commit=False)
            statutory.vendor = vendor
            statutory.save()
            messages.success(request, 'Statutory details saved successfully')
        else:
            for error in form.errors:
                messages.error(request, f'Error in {error}: {form.errors[error]}')
    
    return redirect('vendor_wizard_step', step=7, vendor_id=vendor.id)

@login_required
def add_quality_system(request, vendor_id):
    vendor = get_object_or_404(Vendor, id=vendor_id)
    if request.method == 'POST':
        form = VendorQualitySystemForm(request.POST, request.FILES)
        if form.is_valid():
            quality_system = form.save(commit=False)
            quality_system.vendor = vendor
            quality_system.save()
            messages.success(request, 'Quality system added successfully')
        else:
            for error in form.errors:
                messages.error(request, f'Error in {error}: {form.errors[error]}')
    
    return redirect('vendor_wizard_step', step=8, vendor_id=vendor.id)

@login_required
def delete_quality_system(request, quality_id):
    quality_system = get_object_or_404(VendorQualitySystem, id=quality_id)
    vendor_id = quality_system.vendor.id
    quality_system.delete()
    messages.success(request, 'Quality system deleted successfully')
    return redirect('vendor_wizard_step', step=8, vendor_id=vendor_id)

@login_required
def save_manpower(request, vendor_id):
    vendor = get_object_or_404(Vendor, id=vendor_id)
    if request.method == 'POST':
        manpower_instance = vendor.manpower.first()
        form = VendorManpowerForm(request.POST, instance=manpower_instance)
        if form.is_valid():
            manpower = form.save(commit=False)
            manpower.vendor = vendor
            manpower.save()
            messages.success(request, 'Manpower details saved successfully')
        else:
            for error in form.errors:
                messages.error(request, f'Error in {error}: {form.errors[error]}')
    
    return redirect('vendor_wizard_step', step=9, vendor_id=vendor.id)

@login_required
def add_customer_reference(request, vendor_id):
    """Add customer reference for vendor"""
    vendor = get_object_or_404(Vendor, id=vendor_id)
    
    if request.method == 'POST':
        form = VendorCustomerReferenceForm(request.POST)
        if form.is_valid():
            customer_ref = form.save(commit=False)
            customer_ref.vendor = vendor
            customer_ref.save()
            messages.success(request, 'Customer reference added successfully')
        else:
            for error in form.errors:
                messages.error(request, f'Error in {error}: {form.errors[error]}')
    
    return redirect('vendors:vendor_wizard_step', step=9, vendor_id=vendor.id)

@login_required
def delete_customer_reference(request, reference_id):
    """Delete customer reference"""
    customer_ref = get_object_or_404(VendorCustomerReference, id=reference_id)
    vendor_id = customer_ref.vendor.id
    customer_ref.delete()
    messages.success(request, 'Customer reference deleted successfully')
    return redirect('vendors:vendor_wizard_step', step=9, vendor_id=vendor_id)

@login_required
def add_dealership(request, vendor_id):
    """Add dealership information"""
    vendor = get_object_or_404(Vendor, id=vendor_id)
    
    if request.method == 'POST':
        form = VendorDealershipForm(request.POST)
        if form.is_valid():
            dealership = form.save(commit=False)
            dealership.vendor = vendor
            dealership.save()
            messages.success(request, 'Dealership information added successfully')
        else:
            for error in form.errors:
                messages.error(request, f'Error in {error}: {form.errors[error]}')
    
    return redirect('vendors:vendor_wizard_step', step=9, vendor_id=vendor.id)

@login_required
def delete_dealership(request, dealership_id):
    """Delete dealership information"""
    dealership = get_object_or_404(VendorDealership, id=dealership_id)
    vendor_id = dealership.vendor.id
    dealership.delete()
    messages.success(request, 'Dealership information deleted successfully')
    return redirect('vendors:vendor_wizard_step', step=9, vendor_id=vendor_id)

@login_required
def save_reference(request, vendor_id):
    vendor = get_object_or_404(Vendor, id=vendor_id)
    if request.method == 'POST':
        reference_instance = vendor.references.first()
        form = VendorReferenceForm(request.POST, instance=reference_instance)
        if form.is_valid():
            reference = form.save(commit=False)
            reference.vendor = vendor
            reference.save()
            messages.success(request, 'Reference details saved successfully')
        else:
            for error in form.errors:
                messages.error(request, f'Error in {error}: {form.errors[error]}')
    
    return redirect('vendor_wizard_step', step=9, vendor_id=vendor.id)

@login_required
def add_concern_person(request, vendor_id):
    """Add concern person"""
    vendor = get_object_or_404(Vendor, id=vendor_id)
    
    if request.method == 'POST':
        form = VendorConcernPersonForm(request.POST)
        if form.is_valid():
            concern_person = form.save(commit=False)
            concern_person.vendor = vendor
            
            # If this is set as primary, unset others
            if concern_person.is_primary:
                vendor.concern_persons.update(is_primary=False)
            
            concern_person.save()
            messages.success(request, 'Concern person added successfully')
        else:
            for error in form.errors:
                messages.error(request, f'Error in {error}: {form.errors[error]}')
    
    return redirect('vendors:vendor_wizard_step', step=10, vendor_id=vendor.id)

@login_required
def delete_concern_person(request, person_id):
    """Delete concern person"""
    concern_person = get_object_or_404(VendorConcernPerson, id=person_id)
    vendor_id = concern_person.vendor.id
    concern_person.delete()
    messages.success(request, 'Concern person deleted successfully')
    return redirect('vendors:vendor_wizard_step', step=10, vendor_id=vendor_id)

@login_required
def add_document(request, vendor_id):
    vendor = get_object_or_404(Vendor, id=vendor_id)
    if request.method == 'POST':
        form = VendorDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.vendor = vendor
            document.save()
            messages.success(request, 'Document uploaded successfully')
        else:
            for error in form.errors:
                messages.error(request, f'Error in {error}: {form.errors[error]}')
    
    return redirect('vendor_wizard_step', step=10, vendor_id=vendor.id)

@login_required
def delete_document(request, document_id):
    document = get_object_or_404(VendorDocument, id=document_id)
    vendor_id = document.vendor.id
    document.delete()
    messages.success(request, 'Document deleted successfully')
    return redirect('vendor_wizard_step', step=10, vendor_id=vendor_id)

@login_required
@permission_required('vendors.can_review_vendor')
def vendor_review(request, pk):
    vendor = get_object_or_404(Vendor, id=pk)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        notes = request.POST.get('notes', '')
        
        if action == 'approve':
            vendor.status = 'approved'
            vendor.reviewed_by = request.user
            vendor.reviewed_date = timezone.now()
            vendor.approval_notes = notes
            vendor.save()
            
            VendorApprovalLog.objects.create(
                vendor=vendor,
                action='approved',
                performed_by=request.user,
                notes=notes
            )
            
            messages.success(request, 'Vendor approved successfully')
            
        elif action == 'reject':
            vendor.status = 'rejected'
            vendor.reviewed_by = request.user
            vendor.reviewed_date = timezone.now()
            vendor.approval_notes = notes
            vendor.save()
            
            VendorApprovalLog.objects.create(
                vendor=vendor,
                action='rejected',
                performed_by=request.user,
                notes=notes
            )
            
            messages.success(request, 'Vendor registration rejected')
        
        elif action == 'request_changes':
            vendor.status = 'draft'
            vendor.approval_notes = notes
            vendor.save()
            
            VendorApprovalLog.objects.create(
                vendor=vendor,
                action='reviewed',
                performed_by=request.user,
                notes=f"Changes requested: {notes}"
            )
            
            messages.success(request, 'Changes requested from vendor')
        
        return redirect('vendor_detail', pk=vendor.id)
    
    context = {
        'vendor': vendor,
        'approval_logs': vendor.approval_logs.all(),
    }
    return render(request, 'vendors/vendor_review.html', context)

@login_required
@permission_required('vendors.can_approve_vendor')
def vendor_blacklist(request, pk):
    vendor = get_object_or_404(Vendor, id=pk)
    
    if request.method == 'POST':
        reason = request.POST.get('blacklist_reason', '')
        vendor.is_blacklisted = True
        vendor.blacklist_reason = reason
        vendor.blacklist_date = timezone.now()
        vendor.is_active = False
        vendor.save()
        
        VendorApprovalLog.objects.create(
            vendor=vendor,
            action='blacklisted',
            performed_by=request.user,
            notes=f"Blacklisted: {reason}"
        )
        
        messages.warning(request, 'Vendor has been blacklisted')
        return redirect('vendor_detail', pk=vendor.id)
    
    return redirect('vendor_detail', pk=vendor.id)

@login_required
def vendor_remove_blacklist(request, pk):
    vendor = get_object_or_404(Vendor, id=pk)
    
    if request.method == 'POST':
        vendor.is_blacklisted = False
        vendor.blacklist_reason = ''
        vendor.blacklist_date = None
        vendor.is_active = True
        vendor.save()
        
        VendorApprovalLog.objects.create(
            vendor=vendor,
            action='approved',  # Treat as re-approval
            performed_by=request.user,
            notes="Removed from blacklist"
        )
        
        messages.success(request, 'Vendor removed from blacklist')
    
    return redirect('vendor_detail', pk=vendor.id)

class VendorDetailView(DetailView):
    model = Vendor
    template_name = 'vendors/vendor_detail.html'
    context_object_name = 'vendor'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vendor = self.object
        
        context.update({
            'contacts': vendor.contacts.all(),
            'bank_details': vendor.bank_details.all(),
            'financial_info': vendor.financial_info.all(),
            'quality_systems': vendor.quality_systems.all(),
            'customer_references': vendor.customer_references.all(),
            'dealerships': vendor.dealerships.all(),
            'concern_persons': vendor.concern_persons.all(),
            'documents': vendor.documents.all(),
            'approval_logs': vendor.approval_logs.all(),
            'statutory_details': vendor.statutory_details.first(),
            'manpower_details': vendor.manpower.first(),
            'reference_details': vendor.references.first(),
        })
        
        return context

@login_required
def vendor_export(request):
    # Basic export functionality - can be enhanced with libraries like pandas
    vendors = Vendor.objects.all()
    
    # This is a simple example - in production, use libraries like reportlab or weasyprint
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="vendors.csv"'
    
    # Simple CSV export implementation
    import csv
    writer = csv.writer(response)
    writer.writerow(['Vendor Code', 'Company Name', 'PAN', 'Status', 'Company Type', 'Created Date'])
    
    for vendor in vendors:
        writer.writerow([
            vendor.vendor_code,
            vendor.company_name,
            vendor.pan_number,
            vendor.get_status_display(),
            vendor.get_company_type_display(),
            vendor.created_at.strftime('%Y-%m-%d')
        ])
    
    return response

# API Views for AJAX functionality
@login_required
def get_states(request, country_id):
    states = StateUTMaster.objects.values('id', 'name')
    return JsonResponse(list(states), safe=False)

@login_required
def validate_pan(request):
    pan_number = request.GET.get('pan_number', '')
    vendor_id = request.GET.get('vendor_id')
    
    # Check if PAN already exists
    queryset = Vendor.objects.filter(pan_number=pan_number.upper())
    if vendor_id:
        queryset = queryset.exclude(id=vendor_id)
    
    exists = queryset.exists()
    
    return JsonResponse({'exists': exists, 'valid': len(pan_number) == 10})

@login_required
def vendor_quick_stats(request):
    stats = {
        'total': Vendor.objects.count(),
        'active': Vendor.objects.filter(is_active=True).count(),
        'pending_review': Vendor.objects.filter(status='submitted').count(),
        'approved': Vendor.objects.filter(status='approved').count(),
    }
    return JsonResponse(stats)


# Add model properties for better template functionality
def add_model_properties():
    """Add dynamic properties to models for template usage"""
    
    # Add to VendorQualitySystem model
    def is_expired(self):
        from django.utils import timezone
        return self.valid_upto < timezone.now().date()
    
    def is_expiring_soon(self):
        from django.utils import timezone
        from datetime import timedelta
        thirty_days_from_now = timezone.now().date() + timedelta(days=30)
        return self.valid_upto <= thirty_days_from_now and self.valid_upto >= timezone.now().date()
    
    # Attach to model (this would ideally be in models.py)
    VendorQualitySystem.is_expired = property(is_expired)
    VendorQualitySystem.is_expiring_soon = property(is_expiring_soon)

# Call this function to add the properties
add_model_properties()


@login_required
def save_manpower(request, vendor_id):
    """Save manpower details for a vendor"""
    vendor = get_object_or_404(Vendor, id=vendor_id)
    
    if request.method == 'POST':
        manpower_instance = vendor.manpower.first()
        form = VendorManpowerForm(request.POST, instance=manpower_instance)
        
        if form.is_valid():
            manpower = form.save(commit=False)
            manpower.vendor = vendor
            manpower.save()
            messages.success(request, 'Manpower details saved successfully')
        else:
            for error in form.errors:
                messages.error(request, f'Error in {error}: {form.errors[error]}')
    
    return redirect('vendors:vendor_wizard_step', step=9, vendor_id=vendor.id)

@login_required
def add_customer_reference(request, vendor_id):
    """Add customer reference for a vendor"""
    vendor = get_object_or_404(Vendor, id=vendor_id)
    
    if request.method == 'POST':
        form = VendorCustomerReferenceForm(request.POST)
        if form.is_valid():
            customer_ref = form.save(commit=False)
            customer_ref.vendor = vendor
            customer_ref.save()
            messages.success(request, 'Customer reference added successfully')
        else:
            for error in form.errors:
                messages.error(request, f'Error in {error}: {form.errors[error]}')
    
    return redirect('vendors:vendor_wizard_step', step=9, vendor_id=vendor.id)

@login_required
def delete_customer_reference(request, reference_id):
    """Delete customer reference"""
    customer_ref = get_object_or_404(VendorCustomerReference, id=reference_id)
    vendor_id = customer_ref.vendor.id
    customer_ref.delete()
    messages.success(request, 'Customer reference deleted successfully')
    return redirect('vendors:vendor_wizard_step', step=9, vendor_id=vendor_id)

@login_required
def add_dealership(request, vendor_id):
    """Add dealership information"""
    vendor = get_object_or_404(Vendor, id=vendor_id)
    
    if request.method == 'POST':
        form = VendorDealershipForm(request.POST)
        if form.is_valid():
            dealership = form.save(commit=False)
            dealership.vendor = vendor
            dealership.save()
            messages.success(request, 'Dealership information added successfully')
        else:
            for error in form.errors:
                messages.error(request, f'Error in {error}: {form.errors[error]}')
    
    return redirect('vendors:vendor_wizard_step', step=9, vendor_id=vendor.id)

@login_required
def delete_dealership(request, dealership_id):
    """Delete dealership information"""
    dealership = get_object_or_404(VendorDealership, id=dealership_id)
    vendor_id = dealership.vendor.id
    dealership.delete()
    messages.success(request, 'Dealership information deleted successfully')
    return redirect('vendors:vendor_wizard_step', step=9, vendor_id=vendor_id)

@login_required
def save_reference(request, vendor_id):
    """Save reference details"""
    vendor = get_object_or_404(Vendor, id=vendor_id)
    
    if request.method == 'POST':
        reference_instance = vendor.references.first()
        form = VendorReferenceForm(request.POST, instance=reference_instance)
        
        if form.is_valid():
            reference = form.save(commit=False)
            reference.vendor = vendor
            reference.save()
            messages.success(request, 'Reference details saved successfully')
        else:
            for error in form.errors:
                messages.error(request, f'Error in {error}: {form.errors[error]}')
    
    return redirect('vendors:vendor_wizard_step', step=11, vendor_id=vendor.id)

@login_required
@permission_required('vendors.can_review_vendor')
def vendor_workflow_dashboard(request):
    """Dashboard for vendor approval workflow"""
    # Get vendors based on user permissions
    if request.user.has_perm('vendors.can_approve_vendor'):
        pending_vendors = Vendor.objects.filter(status='submitted')
        under_review_vendors = Vendor.objects.filter(status='under_review')
        on_hold_vendors = Vendor.objects.filter(status='on_hold')
    elif request.user.has_perm('vendors.can_review_vendor'):
        pending_vendors = Vendor.objects.filter(status='submitted')
        under_review_vendors = Vendor.objects.filter(status='under_review', current_assigned_to=request.user)
        on_hold_vendors = Vendor.objects.filter(status='on_hold', current_assigned_to=request.user)
    else:
        pending_vendors = Vendor.objects.none()
        under_review_vendors = Vendor.objects.none()
        on_hold_vendors = Vendor.objects.none()
    
    # Statistics
    stats = {
        'total_pending': pending_vendors.count(),
        'total_under_review': under_review_vendors.count(),
        'total_on_hold': on_hold_vendors.count(),
        'total_approved': Vendor.objects.filter(status='approved').count(),
        'total_rejected': Vendor.objects.filter(status='rejected').count(),
    }
    
    context = {
        'pending_vendors': pending_vendors,
        'under_review_vendors': under_review_vendors,
        'on_hold_vendors': on_hold_vendors,
        'stats': stats,
    }
    
    return render(request, 'vendors/workflow_dashboard.html', context)

@login_required
@permission_required('vendors.can_review_vendor')
def assign_vendor_review(request, pk):
    """Assign vendor for review"""
    vendor = get_object_or_404(Vendor, id=pk)
    
    if request.method == 'POST':
        vendor.status = 'under_review'
        vendor.current_assigned_to = request.user
        vendor.save()
        
        VendorApprovalLog.objects.create(
            vendor=vendor,
            action='assigned',
            performed_by=request.user,
            notes=f'Assigned to {request.user.get_full_name()} for review'
        )
        
        messages.success(request, f'Vendor assigned to you for review')
    
    return redirect('vendors:vendor_review', pk=vendor.id)

@login_required
def vendor_wizard_start(request):
    """Start the vendor wizard - redirect to step 1"""
    return redirect('vendors:vendor_wizard_step', step=1)

@login_required
def vendor_approve(request, pk):
    """Approve vendor (alternative endpoint)"""
    vendor = get_object_or_404(Vendor, id=pk)
    
    if request.method == 'POST':
        vendor.status = 'approved'
        vendor.reviewed_by = request.user
        vendor.reviewed_date = timezone.now()
        vendor.approval_notes = request.POST.get('notes', '')
        vendor.save()
        
        VendorApprovalLog.objects.create(
            vendor=vendor,
            action='approved',
            performed_by=request.user,
            notes=request.POST.get('notes', '')
        )
        
        messages.success(request, 'Vendor approved successfully')
    
    return redirect('vendors:vendor_detail', pk=vendor.id)

@login_required
def vendor_reject(request, pk):
    """Reject vendor (alternative endpoint)"""
    vendor = get_object_or_404(Vendor, id=pk)
    
    if request.method == 'POST':
        vendor.status = 'rejected'
        vendor.reviewed_by = request.user
        vendor.reviewed_date = timezone.now()
        vendor.approval_notes = request.POST.get('notes', '')
        vendor.save()
        
        VendorApprovalLog.objects.create(
            vendor=vendor,
            action='rejected',
            performed_by=request.user,
            notes=request.POST.get('notes', '')
        )
        
        messages.warning(request, 'Vendor registration rejected')
    
    return redirect('vendors:vendor_detail', pk=vendor.id)