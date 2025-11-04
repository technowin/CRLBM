# forms.py
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import *
import re

class CustomerMasterForm(forms.ModelForm):
    date_of_establishment = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=False
    )
    
    class Meta:
        model = CustomerMaster
        fields = [
            'organization_type', 'name', 'is_active', 'date_of_establishment',
            'pan_number', 'msme_udyam_reg_no', 'tan_number', 'cin_number',
            'ie_code', 'exemption_certificates', 'billing_currency',
            'payment_terms', 'requires_advance', 'credit_limit', 'website',
            'billing_contact_person', 'billing_contact_email', 'billing_contact_phone'
        ]
        widgets = {
            'organization_type': forms.Select(attrs={'class': 'form-select', 'id': 'id_organization_type'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter customer name', 'id': 'id_customer_name'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'pan_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ABCDE1234F', 'maxlength': '10', 'oninput': 'this.value = this.value.toUpperCase()'}),
            'msme_udyam_reg_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'UDYAM-XX-XX-XXXXXX'}),
            'tan_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ABCD12345E', 'maxlength': '10', 'oninput': 'this.value = this.value.toUpperCase()'}),
            'cin_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'U12345AB1234ABC123456', 'maxlength': '21', 'oninput': 'this.value = this.value.toUpperCase()'}),
            'ie_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '1234567890'}),
            'exemption_certificates': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter exemption certificate details'}),
            'billing_currency': forms.Select(attrs={'class': 'form-select'}),
            'payment_terms': forms.Select(attrs={'class': 'form-select'}),
            'requires_advance': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'credit_limit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com'}),
            'billing_contact_person': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Name of billing contact person'}),
            'billing_contact_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'billing@example.com'}),
            'billing_contact_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91-XXXXXXXXXX'}),
        }
        labels = {
            'msme_udyam_reg_no': 'MSME / Udyam Registration No.',
            'ie_code': 'Import Export Code',
        }
    
    def clean_pan_number(self):
        pan_number = self.cleaned_data.get('pan_number', '').upper().strip()
        if pan_number:
            if not re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', pan_number):
                raise ValidationError('Invalid PAN number format. Format: ABCDE1234F')
            
            # Check for duplicate PAN (excluding current instance)
            if self.instance.pk:
                if CustomerMaster.objects.filter(pan_number=pan_number).exclude(pk=self.instance.pk).exists():
                    raise ValidationError('A customer with this PAN number already exists.')
            else:
                if CustomerMaster.objects.filter(pan_number=pan_number).exists():
                    raise ValidationError('A customer with this PAN number already exists.')
        return pan_number
    
    def clean_name(self):
        name = self.cleaned_data.get('name').strip()
        if not name:
            raise ValidationError('Customer name is required.')
        
        # Check for duplicate customer names
        if self.instance.pk:  # Update case
            if CustomerMaster.objects.filter(name=name).exclude(pk=self.instance.pk).exists():
                raise ValidationError('A customer with this name already exists.')
        else:  # Create case
            if CustomerMaster.objects.filter(name=name).exists():
                raise ValidationError('A customer with this name already exists.')
        return name
    
    def clean_date_of_establishment(self):
        date = self.cleaned_data.get('date_of_establishment')
        if date and date > timezone.now().date():
            raise ValidationError('Date of establishment cannot be in the future.')
        return date
    
    def clean_credit_limit(self):
        credit_limit = self.cleaned_data.get('credit_limit')
        if credit_limit and credit_limit < 0:
            raise ValidationError('Credit limit cannot be negative.')
        return credit_limit

class CustomerAddressForm(forms.ModelForm):
    class Meta:
        model = CustomerAddress
        fields = [
            'branch_category', 'address', 'state', 'country', 'pincode',
            'location', 'google_location', 'telephone', 'email', 'gst_number', 'is_primary', 'is_active'
        ]
        widgets = {
            'branch_category': forms.Select(attrs={'class': 'form-select'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter complete address'}),
            'state': forms.Select(attrs={'class': 'form-select'}),
            'country': forms.Select(attrs={'class': 'form-select'}),
            'pincode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter pincode', 'maxlength': '10'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter location/area'}),
            'google_location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Google Maps location'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91-XXXXXXXXXX'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'office@example.com'}),
            'gst_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '12ABCDE1234F1Z5', 'maxlength': '15', 'oninput': 'this.value = this.value.toUpperCase()'}),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'DELETE': forms.HiddenInput(),
        }
    
    def clean_gst_number(self):
        gst_number = self.cleaned_data.get('gst_number', '').upper().strip()
        if gst_number:
            if not re.match(r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$', gst_number):
                raise ValidationError('Invalid GST number format.')
        return gst_number
    
    def clean_pincode(self):
        pincode = self.cleaned_data.get('pincode', '').strip()
        if pincode and not pincode.isdigit():
            raise ValidationError('Pincode must contain only numbers.')
        return pincode

class CustomerBankDetailsForm(forms.ModelForm):
    class Meta:
        model = CustomerBankDetails
        fields = ['bank_name', 'account_number', 'account_holder_name', 'branch_name', 'ifsc_code', 'account_type', 'is_primary', 'is_active']
        widgets = {
            'bank_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter bank name'}),
            'account_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter account number'}),
            'account_holder_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter account holder name'}),
            'branch_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter branch name'}),
            'ifsc_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ABCD0123456', 'maxlength': '11', 'oninput': 'this.value = this.value.toUpperCase()'}),
            'account_type': forms.Select(attrs={'class': 'form-select'}),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'DELETE': forms.HiddenInput(),
        }
    
    def clean_ifsc_code(self):
        ifsc_code = self.cleaned_data.get('ifsc_code', '').upper().strip()
        if ifsc_code:
            if not re.match(r'^[A-Z]{4}0[A-Z0-9]{6}$', ifsc_code):
                raise ValidationError('Invalid IFSC code format.')
        return ifsc_code
    
    def clean_account_number(self):
        account_number = self.cleaned_data.get('account_number', '').strip()
        if account_number and not account_number.isdigit():
            raise ValidationError('Account number must contain only numbers.')
        return account_number

class CustomerDivisionForm(forms.Form):
    divisions = forms.ModelMultipleChoiceField(
        queryset=DivisionMaster.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False
    )

class CustomerConcernPersonForm(forms.ModelForm):
    concern_for = forms.ModelMultipleChoiceField(
        queryset=ConcernCategory.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False
    )
    
    class Meta:
        model = CustomerConcernPerson
        fields = [
            'customer', 'branch_category', 'address', 'concern_person', 'designation',
            'concern_for', 'country_1', 'mobile_1', 'country_2', 'mobile_2',
            'office_phone_1', 'office_extension_1', 'office_phone_2',
            'email_company', 'email_personal', 'remarks', 'is_active', 'is_primary_contact'
        ]
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select', 'id': 'concern_customer'}),
            'branch_category': forms.Select(attrs={'class': 'form-select', 'id': 'concern_branch_category'}),
            'address': forms.Select(attrs={'class': 'form-select', 'id': 'concern_address'}),
            'concern_person': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter concern person name'}),
            'designation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter designation'}),
            'country_1': forms.Select(attrs={'class': 'form-select'}),
            'mobile_1': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '10-digit mobile number', 'maxlength': '10'}),
            'country_2': forms.Select(attrs={'class': 'form-select'}),
            'mobile_2': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '10-digit mobile number', 'maxlength': '10'}),
            'office_phone_1': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Office phone', 'maxlength': '11'}),
            'office_extension_1': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ext', 'maxlength': '4'}),
            'office_phone_2': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Office phone 2', 'maxlength': '11'}),
            'email_company': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'company.email@example.com'}),
            'email_personal': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'personal.email@example.com'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter any remarks'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_primary_contact': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'DELETE': forms.HiddenInput(),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial country to India
        if not self.instance.pk:
            try:
                india = CountryMaster.objects.get(name='India')
                self.fields['country_1'].initial = india
                self.fields['country_2'].initial = india
            except CountryMaster.DoesNotExist:
                pass
    
    def clean_mobile_1(self):
        mobile_1 = self.cleaned_data.get('mobile_1')
        if mobile_1 and len(mobile_1) != 10:
            raise ValidationError('Mobile number must be exactly 10 digits.')
        if mobile_1 and not mobile_1.isdigit():
            raise ValidationError('Mobile number must contain only numbers.')
        return mobile_1
    
    def clean_mobile_2(self):
        mobile_2 = self.cleaned_data.get('mobile_2')
        if mobile_2 and len(mobile_2) != 10:
            raise ValidationError('Mobile number must be exactly 10 digits.')
        if mobile_2 and not mobile_2.isdigit():
            raise ValidationError('Mobile number must contain only numbers.')
        return mobile_2
    
    def clean_office_phone_1(self):
        phone = self.cleaned_data.get('office_phone_1')
        if phone and not phone.isdigit():
            raise ValidationError('Office phone must contain only numbers.')
        return phone
    
    def clean_office_phone_2(self):
        phone = self.cleaned_data.get('office_phone_2')
        if phone and not phone.isdigit():
            raise ValidationError('Office phone must contain only numbers.')
        return phone

class ConcernPersonQuickForm(forms.ModelForm):
    """Simplified form for adding concern persons from customer detail page"""
    class Meta:
        model = CustomerConcernPerson
        fields = ['concern_person', 'designation', 'mobile_1', 'email_company', 'is_active']
        widgets = {
            'concern_person': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter concern person name'}),
            'designation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter designation'}),
            'mobile_1': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '10-digit mobile number', 'maxlength': '10'}),
            'email_company': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'company.email@example.com'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class CustomerSearchForm(forms.Form):
    name = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Search by customer name...'
    }))
    customer_id = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Customer ID'
    }))
    pan_number = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'PAN Number'
    }))
    organization_type = forms.ModelChoiceField(
        queryset=TypeOfOrganization.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + CustomerMaster.CUSTOMER_STATUS,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

class CustomerDocumentForm(forms.ModelForm):
    class Meta:
        model = CustomerDocument
        fields = ['document_type', 'document_name', 'document_file', 'remarks']
        widgets = {
            'document_type': forms.Select(attrs={'class': 'form-select'}),
            'document_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter document name'}),
            'document_file': forms.FileInput(attrs={'class': 'form-control'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Enter any remarks'}),
        }

class CustomerNoteForm(forms.ModelForm):
    class Meta:
        model = CustomerNote
        fields = ['title', 'content', 'priority']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter note title'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter note content'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
        }