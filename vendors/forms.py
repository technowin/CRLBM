from django import forms
from .models import *
from django.core.validators import FileExtensionValidator
import re
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date

class VendorBasicForm(forms.ModelForm):
    vendor_types = forms.MultipleChoiceField(
        choices=Vendor.VENDOR_TYPES,
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    
    class Meta:
        model = Vendor
        fields = [
            'country', 'company_type', 'company_name', 'display_name', 
            'create_ledger', 'vendor_types', 'work_description', 'category'
        ]
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter company name'}),
            'display_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Name for cheque printing'}),
            'work_description': forms.Select(attrs={'class': 'form-select'}),
            'company_type': forms.Select(attrs={'class': 'form-select'}),
            'country': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def clean_display_name(self):
        display_name = self.cleaned_data.get('display_name')
        if not display_name:
            return self.cleaned_data.get('company_name')
        return display_name

class VendorPANForm(forms.ModelForm):
    pan_number = forms.CharField(
        max_length=10,
        validators=[RegexValidator(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', 'Enter a valid PAN number')],
        widget=forms.TextInput(attrs={
            'class': 'form-control text-uppercase',
            'placeholder': 'ABCDE1234F',
            'oninput': 'this.value = this.value.toUpperCase()'
        })
    )
    
    pan_copy = forms.FileField(
        required=False,
        validators=[FileExtensionValidator(['pdf', 'jpg', 'jpeg', 'png'])],
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png'
        })
    )
    
    msme_certificate = forms.FileField(
        required=False,
        validators=[FileExtensionValidator(['pdf', 'jpg', 'jpeg', 'png'])],
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png'
        })
    )
    
    class Meta:
        model = Vendor
        fields = ['pan_number', 'pan_copy', 'is_msme', 'msme_type', 'msme_number', 'msme_certificate', 'msme_validity']
        widgets = {
            'msme_type': forms.Select(attrs={'class': 'form-select'}),
            'msme_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'MSME registration number'}),
            'msme_validity': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_msme': forms.CheckboxInput(attrs={'class': 'form-check-input', 'onchange': 'toggleMSMEFields(this)'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        is_msme = cleaned_data.get('is_msme')
        msme_type = cleaned_data.get('msme_type')
        msme_number = cleaned_data.get('msme_number')
        
        if is_msme and not msme_type:
            raise forms.ValidationError({
                'msme_type': 'MSME type is required when MSME is selected.'
            })
        
        if is_msme and not msme_number:
            raise forms.ValidationError({
                'msme_number': 'MSME number is required when MSME is selected.'
            })
        
        return cleaned_data

class VendorDatesForm(forms.ModelForm):
    establishment_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    commencement_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    registered_with_bluechip = forms.TypedChoiceField(
        choices=[(True, 'Yes'), (False, 'No')],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        coerce=lambda x: x == 'True',
        required=False
    )
    
    responsibility_return_replace = forms.TypedChoiceField(
        choices=[(True, 'Yes'), (False, 'No')],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        coerce=lambda x: x == 'True',
        required=False
    )
    
    class Meta:
        model = Vendor
        fields = [
            'establishment_date', 'commencement_date', 'payment_preference', 
            'registered_with_bluechip', 'responsibility_return_replace', 'vendor_group'
        ]
        widgets = {
            'payment_preference': forms.Select(attrs={'class': 'form-select'}),
            'vendor_group': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Vendor group/category'}),
        }

    def clean_establishment_date(self):
        establishment_date = self.cleaned_data.get('establishment_date')
        if establishment_date:
            if establishment_date > date.today():
                raise ValidationError("Establishment date cannot be in the future.")
        return establishment_date
    
    def clean_commencement_date(self):
        commencement_date = self.cleaned_data.get('commencement_date')
        establishment_date = self.cleaned_data.get('establishment_date')
        
        if commencement_date and establishment_date:
            if commencement_date < establishment_date:
                raise ValidationError("Commencement date cannot be before establishment date.")
        
        return commencement_date

class VendorSisterConcernForm(forms.ModelForm):
    class Meta:
        model = VendorSisterConcern
        fields = '__all__'
        exclude = ['vendor']
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Company name'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Full address'}),
            'pincode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '6-digit pincode'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City/Location'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contact person name'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Telephone number'}),
            'fax': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Fax number'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@example.com'}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com'}),
        }
            
class VendorContactForm(forms.ModelForm):
    class Meta:
        model = VendorContact
        fields = '__all__'
        exclude = ['vendor', 'created_at']
        widgets = {
            'contact_type': forms.Select(attrs={'class': 'form-select'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Full address'}),
            'state': forms.Select(attrs={'class': 'form-select'}),
            'gst_number': forms.TextInput(attrs={'class': 'form-control text-uppercase', 'placeholder': '22ABCDE1234F1Z5'}),
            'pincode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '6-digit pincode', 'pattern': '[1-9][0-9]{5}'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City/Location'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '10-12 digit number', 'pattern': '[0-9]{10,12}'}),
            'fax': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '10-12 digit number', 'pattern': '[0-9]{10,12}'}),
            'working_time_from': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'working_time_to': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'gst_certificate': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.jpg,.jpeg,.png'}),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['weekly_holidays'] = forms.MultipleChoiceField(
            choices=[
                ('sunday', 'Sunday'),
                ('monday', 'Monday'),
                ('tuesday', 'Tuesday'),
                ('wednesday', 'Wednesday'),
                ('thursday', 'Thursday'),
                ('friday', 'Friday'),
                ('saturday', 'Saturday'),
            ],
            widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
            required=False
        )

    def clean_gst_number(self):
        gst_number = self.cleaned_data.get('gst_number', '').upper()
        if gst_number:
            # Basic GST validation pattern
            gst_pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$'
            if not re.match(gst_pattern, gst_number):
                raise ValidationError('Please enter a valid GST number (Format: 22ABCDE1234F1Z5)')
        return gst_number
    
    def clean_pincode(self):
        pincode = self.cleaned_data.get('pincode')
        if pincode:
            if len(pincode) != 6 or not pincode.isdigit():
                raise ValidationError('Please enter a valid 6-digit pincode')
            if pincode[0] == '0':
                raise ValidationError('Pincode cannot start with 0')
        return pincode
    
class VendorBankForm(forms.ModelForm):
    bank_proof = forms.FileField(
        required=False,
        validators=[FileExtensionValidator(['pdf', 'jpg', 'jpeg', 'png'])],
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png'
        })
    )
    
    class Meta:
        model = VendorBankDetail
        fields = '__all__'
        exclude = ['vendor', 'created_at']
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Company name as in bank records'}),
            'bank_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bank name'}),
            'branch_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Branch name'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'account_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Account number'}),
            'account_type': forms.Select(attrs={'class': 'form-select'}),
            'ifsc_code': forms.TextInput(attrs={'class': 'form-control text-uppercase', 'placeholder': 'ABCD0123456'}),
            'micr_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '9-digit MICR code', 'pattern': '[0-9]{9}'}),
            'swift_code': forms.TextInput(attrs={'class': 'form-control text-uppercase', 'placeholder': 'SWIFT code'}),
            'iban_code': forms.TextInput(attrs={'class': 'form-control text-uppercase', 'placeholder': 'IBAN code'}),
            'bankers_details': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Additional banker details'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_ifsc_code(self):
        ifsc_code = self.cleaned_data.get('ifsc_code', '').upper()
        if ifsc_code:
            ifsc_pattern = r'^[A-Z]{4}0[0-9A-Z]{6}$'
            if not re.match(ifsc_pattern, ifsc_code):
                raise ValidationError('Please enter a valid IFSC code (Format: ABCD0123456)')
        return ifsc_code
    
    def clean_account_number(self):
        account_number = self.cleaned_data.get('account_number')
        if account_number:
            if not account_number.isdigit():
                raise ValidationError('Account number should contain only digits')
            if len(account_number) < 9 or len(account_number) > 18:
                raise ValidationError('Account number should be between 9 and 18 digits')
        return account_number

class VendorConcernPersonForm(forms.ModelForm):
    class Meta:
        model = VendorConcernPerson
        fields = '__all__'
        exclude = ['vendor', 'created_at']
        widgets = {
            'branch': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Branch/department'}),
            'concern_for': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full name'}),
            'designation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Designation'}),
            'mobile_1': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Primary mobile number'}),
            'mobile_2': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Secondary mobile number'}),
            'office_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Office phone number'}),
            'company_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'company@example.com'}),
            'personal_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'personal@example.com'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class VendorFinancialForm(forms.ModelForm):
    class Meta:
        model = VendorFinancialInfo
        fields = '__all__'
        exclude = ['vendor']
        widgets = {
            'year': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'YYYY'}),
            'share_capital_reserves': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Amount in lakhs'}),
            'sales_turnover': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Amount in lakhs'}),
            'cash_profit': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Amount in lakhs'}),
        }

    def clean_year(self):
        year = self.cleaned_data.get('year')
        if year:
            current_year = timezone.now().year
            if int(year) > current_year:
                raise ValidationError("Financial year cannot be in the future.")
            if int(year) < current_year - 10:
                raise ValidationError("Financial year cannot be more than 10 years in the past.")
        return year
    
    def clean(self):
        cleaned_data = super().clean()
        year = cleaned_data.get('year')
        vendor = getattr(self.instance, 'vendor', None)
        
        if vendor and year:
            # Check for duplicate financial year
            existing = VendorFinancialInfo.objects.filter(
                vendor=vendor, 
                year=year
            ).exclude(pk=self.instance.pk if self.instance else None)
            
            if existing.exists():
                raise ValidationError({
                    'year': f'Financial information for year {year} already exists.'
                })
        
        return cleaned_data
    
class VendorQualitySystemForm(forms.ModelForm):
    certificate_file = forms.FileField(
        required=False,
        validators=[FileExtensionValidator(['pdf', 'jpg', 'jpeg', 'png'])],
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png'
        })
    )
    
    class Meta:
        model = VendorQualitySystem
        fields = '__all__'
        exclude = ['vendor']
        widgets = {
            'system_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Quality system name'}),
            'certificate_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Certificate number'}),
            'valid_upto': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

class VendorCustomerReferenceForm(forms.ModelForm):
    class Meta:
        model = VendorCustomerReference
        fields = '__all__'
        exclude = ['vendor']
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Customer company name'}),
            'percentage': forms.NumberInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Percentage',
                'min': '0',
                'max': '100',
                'step': '0.01'
            }),
        }
    
    def clean_percentage(self):
        percentage = self.cleaned_data.get('percentage')
        if percentage and percentage > 100:
            raise ValidationError('Percentage cannot exceed 100%')
        return percentage

class VendorDealershipForm(forms.ModelForm):
    class Meta:
        model = VendorDealership
        fields = '__all__'
        exclude = ['vendor']
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Company name'}),
            'product': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Product name'}),
            'territory': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Territory covered'}),
            'since': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Year or date'}),
        }

class VendorManpowerForm(forms.ModelForm):
    class Meta:
        model = VendorManpower
        fields = '__all__'
        exclude = ['vendor']
        widgets = {
            'total_strength': forms.NumberInput(attrs={'class': 'form-control'}),
            'resident_managers': forms.NumberInput(attrs={'class': 'form-control'}),
            'resident_managers_qualification': forms.TextInput(attrs={'class': 'form-control'}),
            'resident_managers_experience': forms.TextInput(attrs={'class': 'form-control'}),
            'site_engineers': forms.NumberInput(attrs={'class': 'form-control'}),
            'site_engineers_qualification': forms.TextInput(attrs={'class': 'form-control'}),
            'site_engineers_experience': forms.TextInput(attrs={'class': 'form-control'}),
            'quality_engineers': forms.NumberInput(attrs={'class': 'form-control'}),
            'quality_engineers_qualification': forms.TextInput(attrs={'class': 'form-control'}),
            'quality_engineers_experience': forms.TextInput(attrs={'class': 'form-control'}),
            'safety_coordinators': forms.NumberInput(attrs={'class': 'form-control'}),
            'safety_coordinators_qualification': forms.TextInput(attrs={'class': 'form-control'}),
            'safety_coordinators_experience': forms.TextInput(attrs={'class': 'form-control'}),
            'supervisors': forms.NumberInput(attrs={'class': 'form-control'}),
            'supervisors_qualification': forms.TextInput(attrs={'class': 'form-control'}),
            'supervisors_experience': forms.TextInput(attrs={'class': 'form-control'}),
            'skilled_workmen': forms.NumberInput(attrs={'class': 'form-control'}),
            'skilled_workmen_qualification': forms.TextInput(attrs={'class': 'form-control'}),
            'skilled_workmen_experience': forms.TextInput(attrs={'class': 'form-control'}),
            'others': forms.NumberInput(attrs={'class': 'form-control'}),
            'others_qualification': forms.TextInput(attrs={'class': 'form-control'}),
            'others_experience': forms.TextInput(attrs={'class': 'form-control'}),
        }

class VendorStatutoryForm(forms.ModelForm):
    class Meta:
        model = VendorStatutory
        fields = '__all__'
        exclude = ['vendor']
        widgets = {
            'service_tax_reg_no': forms.TextInput(attrs={'class': 'form-control'}),
            'vat_reg_no': forms.TextInput(attrs={'class': 'form-control'}),
            'vat_reg_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'pf_reg_no': forms.TextInput(attrs={'class': 'form-control'}),
            'cpwd_registered': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'cpwd_details': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'gst_number': forms.TextInput(attrs={'class': 'form-control text-uppercase'}),
        }

class VendorReferenceForm(forms.ModelForm):
    class Meta:
        model = VendorReference
        fields = '__all__'
        exclude = ['vendor']
        widgets = {
            'scip_employee_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Employee name'}),
            'scip_employee_relation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Relationship with vendor'}),
            'ex_scip_employee_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex-employee name'}),
            'ex_scip_employee_designation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Designation in your company'}),
            'ex_scip_employee_department': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Department in your company'}),
        }

class VendorDocumentForm(forms.ModelForm):
    file = forms.FileField(
        validators=[FileExtensionValidator(['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx'])],
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png,.doc,.docx'
        })
    )
    
    class Meta:
        model = VendorDocument
        fields = '__all__'
        exclude = ['vendor', 'uploaded_at', 'is_verified']
        widgets = {
            'document_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Document description'}),
        }

class VendorApprovalForm(forms.ModelForm):
    """Form for vendor approval workflow"""
    action = forms.ChoiceField(
        choices=[
            ('approve', 'Approve Vendor'),
            ('reject', 'Reject Vendor'),
            ('request_changes', 'Request Changes'),
            ('on_hold', 'Put On Hold'),
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter approval notes, rejection reason, or change requests...'}),
        required=False
    )
    
    class Meta:
        model = Vendor
        fields = ['status', 'approval_notes', 'rejection_reason']
        
class VendorSearchForm(forms.Form):
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by company name, PAN, vendor code...'
        })
    )
    company_type = forms.ChoiceField(
        choices=[('', 'All Types')] + Vendor.COMPANY_TYPES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + Vendor.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    is_active = forms.ChoiceField(
        choices=[('', 'All'), ('true', 'Active'), ('false', 'Inactive')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )