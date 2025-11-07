from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Enquiry, EnquiryItem, Quotation, QuotationItem, SalesOrder, SalesOrderItem
from CMS.models import CustomerMaster, CustomerConcernPerson

class EnquiryForm(forms.ModelForm):
    required_by_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        help_text="Date by which the service is required"
    )
    tender_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    bid_submission_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    class Meta:
        model = Enquiry
        fields = [
            'enquiry_type', 'enquiry_date', 'required_by_date', 'priority', 
            'customer', 'contact_person', 'alternative_contact', 'email', 'phone',
            'subject', 'description', 'source', 'project_requirements', 'delivery_location',
            'tender_name', 'tender_id', 'tender_date', 'tender_authority', 'bid_submission_date',
            'referral_person_name', 'referral_mobile', 'referral_company',
            'currency', 'estimated_budget', 'notes', 'attachment'
        ]
        widgets = {
            'enquiry_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'enquiry_type': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'contact_person': forms.Select(attrs={'class': 'form-control'}),
            'alternative_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'source': forms.TextInput(attrs={'class': 'form-control'}),
            'project_requirements': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'delivery_location': forms.TextInput(attrs={'class': 'form-control'}),
            'tender_name': forms.TextInput(attrs={'class': 'form-control'}),
            'tender_id': forms.TextInput(attrs={'class': 'form-control'}),
            'tender_authority': forms.TextInput(attrs={'class': 'form-control'}),
            'referral_person_name': forms.TextInput(attrs={'class': 'form-control'}),
            'referral_mobile': forms.TextInput(attrs={'class': 'form-control'}),
            'referral_company': forms.TextInput(attrs={'class': 'form-control'}),
            'currency': forms.Select(attrs={'class': 'form-control'}),
            'estimated_budget': forms.NumberInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'attachment': forms.FileInput(attrs={'class': 'form-control'}),
        }
        help_texts = {
            'enquiry_type': "Select the type of enquiry. Additional fields will appear based on your selection.",
            'priority': "Set the priority level for this enquiry",
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        # Set current date as default for enquiry date
        if not self.instance.pk:
            self.fields['enquiry_date'].initial = timezone.now().date()
        
        # Filter contact persons based on selected customer
        if 'customer' in self.data:
            try:
                customer_id = int(self.data.get('customer'))
                self.fields['contact_person'].queryset = CustomerConcernPerson.objects.filter(
                    customer_id=customer_id, is_active=True
                ).order_by('concern_person')
            except (ValueError, TypeError):
                self.fields['contact_person'].queryset = CustomerConcernPerson.objects.none()
        elif self.instance.pk:
            self.fields['contact_person'].queryset = self.instance.customer.concern_persons.filter(
                is_active=True
            ).order_by('concern_person')
        else:
            self.fields['contact_person'].queryset = CustomerConcernPerson.objects.none()

    def clean_required_by_date(self):
        required_by_date = self.cleaned_data.get('required_by_date')
        enquiry_date = self.cleaned_data.get('enquiry_date') or timezone.now().date()
        
        if required_by_date and required_by_date < enquiry_date:
            raise ValidationError("Required by date cannot be before enquiry date")
        
        return required_by_date

    def clean(self):
        cleaned_data = super().clean()
        enquiry_type = cleaned_data.get('enquiry_type')
        
        # Validate tender-specific fields
        if enquiry_type == 'tender':
            if not cleaned_data.get('tender_name'):
                self.add_error('tender_name', 'Tender name is required for tender enquiries')
            if not cleaned_data.get('tender_id'):
                self.add_error('tender_id', 'Tender ID is required for tender enquiries')
            if not cleaned_data.get('bid_submission_date'):
                self.add_error('bid_submission_date', 'Bid submission date is required for tender enquiries')
        
        # Validate referral-specific fields
        if enquiry_type == 'referral':
            if not cleaned_data.get('referral_person_name'):
                self.add_error('referral_person_name', 'Referral person name is required for referral enquiries')
        
        return cleaned_data


class EnquiryItemForm(forms.ModelForm):
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    class Meta:
        model = EnquiryItem
        fields = [
            'service_category', 'service_description', 'detailed_specifications',
            'quantity', 'unit', 'crane_capacity', 'boom_length', 'working_height', 'radius',
            'location_requirements', 'safety_requirements', 'start_date', 'end_date',
            'working_hours', 'target_price', 'customer_budget', 'notes'
        ]
        widgets = {
            'service_category': forms.Select(attrs={'class': 'form-control'}),
            'service_description': forms.TextInput(attrs={'class': 'form-control'}),
            'detailed_specifications': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'unit': forms.Select(attrs={'class': 'form-control'}),
            'crane_capacity': forms.TextInput(attrs={'class': 'form-control'}),
            'boom_length': forms.TextInput(attrs={'class': 'form-control'}),
            'working_height': forms.TextInput(attrs={'class': 'form-control'}),
            'radius': forms.TextInput(attrs={'class': 'form-control'}),
            'location_requirements': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'safety_requirements': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'working_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'target_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'customer_budget': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            self.add_error('end_date', 'End date cannot be before start date')
        
        return cleaned_data


class QuotationForm(forms.ModelForm):
    quotation_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    class Meta:
        model = Quotation
        fields = [
            'enquiry', 'quotation_date', 'validity_days', 'customer', 'contact_person',
            'billing_address', 'shipping_address', 'currency', 'payment_terms',
            'delivery_terms', 'incoterms', 'tax_rate', 'other_charges',
            'scope_of_work', 'terms_conditions', 'special_instructions', 'notes'
        ]
        widgets = {
            'enquiry': forms.Select(attrs={'class': 'form-control'}),
            'validity_days': forms.Select(attrs={'class': 'form-control'}),
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'contact_person': forms.Select(attrs={'class': 'form-control'}),
            'billing_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'shipping_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'currency': forms.Select(attrs={'class': 'form-control'}),
            'payment_terms': forms.TextInput(attrs={'class': 'form-control'}),
            'delivery_terms': forms.TextInput(attrs={'class': 'form-control'}),
            'incoterms': forms.TextInput(attrs={'class': 'form-control'}),
            'tax_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'other_charges': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'scope_of_work': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'terms_conditions': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'special_instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['quotation_date'].initial = timezone.now().date()
        
        # Filter enquiries that can be quoted
        self.fields['enquiry'].queryset = Enquiry.objects.filter(
            status__in=['new', 'in_progress']
        )


class QuotationItemForm(forms.ModelForm):
    class Meta:
        model = QuotationItem
        fields = [
            'enquiry_item', 'service_category', 'service_description', 'specifications',
            'quantity', 'unit', 'unit_price', 'duration', 'equipment_details',
            'manpower_requirements', 'notes'
        ]
        widgets = {
            'enquiry_item': forms.Select(attrs={'class': 'form-control'}),
            'service_category': forms.Select(attrs={'class': 'form-control'}),
            'service_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'specifications': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'unit': forms.Select(attrs={'class': 'form-control'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'duration': forms.TextInput(attrs={'class': 'form-control'}),
            'equipment_details': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'manpower_requirements': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class SalesOrderForm(forms.ModelForm):
    order_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    expected_delivery_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    actual_delivery_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    customer_po_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    class Meta:
        model = SalesOrder
        fields = [
            'quotation', 'order_date', 'expected_delivery_date', 'customer', 'contact_person',
            'customer_po_number', 'customer_po_date', 'customer_po_file', 'delivery_address',
            'site_contact_person', 'site_contact_phone', 'currency', 'payment_terms',
            'delivery_terms', 'tax_rate', 'other_charges', 'advance_received',
            'project_manager', 'site_supervisor', 'project_requirements', 'safety_requirements',
            'notes', 'internal_notes'
        ]
        widgets = {
            'quotation': forms.Select(attrs={'class': 'form-control'}),
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'contact_person': forms.Select(attrs={'class': 'form-control'}),
            'customer_po_number': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_po_file': forms.FileInput(attrs={'class': 'form-control'}),
            'delivery_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'site_contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'site_contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'currency': forms.Select(attrs={'class': 'form-control'}),
            'payment_terms': forms.TextInput(attrs={'class': 'form-control'}),
            'delivery_terms': forms.TextInput(attrs={'class': 'form-control'}),
            'tax_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'other_charges': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'advance_received': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'project_manager': forms.Select(attrs={'class': 'form-control'}),
            'site_supervisor': forms.TextInput(attrs={'class': 'form-control'}),
            'project_requirements': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'safety_requirements': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'internal_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['order_date'].initial = timezone.now().date()
        
        # Filter quotations that can be converted to orders
        self.fields['quotation'].queryset = Quotation.objects.filter(
            status='accepted'
        )

    def clean_expected_delivery_date(self):
        expected_delivery_date = self.cleaned_data.get('expected_delivery_date')
        order_date = self.cleaned_data.get('order_date') or timezone.now().date()
        
        if expected_delivery_date and expected_delivery_date < order_date:
            raise ValidationError("Expected delivery date cannot be before order date")
        
        return expected_delivery_date
    
    def clean_advance_received(self):
        advance_received = self.cleaned_data.get('advance_received') or 0
        total_amount = self.cleaned_data.get('total_amount') or 0
        
        if advance_received > total_amount:
            raise ValidationError("Advance received cannot be greater than total amount")
        
        return advance_received


class SalesOrderItemForm(forms.ModelForm):
    planned_start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    planned_end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    actual_start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    actual_end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    class Meta:
        model = SalesOrderItem
        fields = [
            'quotation_item', 'service_category', 'service_description', 'specifications',
            'quantity', 'unit', 'unit_price', 'planned_start_date', 'planned_end_date',
            'actual_start_date', 'actual_end_date', 'completed_quantity', 'assigned_equipment',
            'assigned_team', 'status', 'notes'
        ]
        widgets = {
            'quotation_item': forms.Select(attrs={'class': 'form-control'}),
            'service_category': forms.Select(attrs={'class': 'form-control'}),
            'service_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'specifications': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'unit': forms.Select(attrs={'class': 'form-control'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'completed_quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'assigned_equipment': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'assigned_team': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def clean_completed_quantity(self):
        completed_quantity = self.cleaned_data.get('completed_quantity') or 0
        quantity = self.cleaned_data.get('quantity') or 0
        
        if completed_quantity > quantity:
            raise ValidationError("Completed quantity cannot exceed ordered quantity")
        
        return completed_quantity