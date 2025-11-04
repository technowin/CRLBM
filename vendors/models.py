from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import datetime, timedelta


class VendorCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Vendor Categories"

class Vendor(models.Model):
    COMPANY_TYPES = [
        ('proprietorship', 'Proprietorship'),
        ('partnership', 'Partnership Firm'),
        ('private_limited', 'Private Limited Company'),
        ('public_limited', 'Public Limited Company'),
        ('llp', 'Limited Liability Partnership'),
        ('cooperative', 'Co-Operative Society'),
        ('huf', 'HUF'),
        ('govt_undertaking', 'Govt. Of India Undertaking'),
        ('state_govt', 'State Govt. Undertaking'),
        ('other', 'Other'),
    ]

    VENDOR_TYPES = [
        ('msme', 'MSME'),
        ('manufacturer', 'Manufacturer'),
        ('distributor', 'Distributor'),
        ('dealer', 'Dealer/Agent'),
        ('trader', 'Trader'),
        ('labour', 'Labour Contractor'),
        ('fuel', 'Fuel Supplier'),
    ]

    WORK_DESCRIPTIONS = [
        ('material_supplier', 'Material Supplier'),
        ('service_provider', 'Service Provider'),
        ('labour_supplier', 'Labour Supplier'),
        ('general_contractor', 'General Contractor'),
    ]

    PAYMENT_PREFERENCES = [
        ('cash', 'By Cash'),
        ('cheque', 'By Cheque'),
        ('dd', 'By Demand Draft'),
        ('rtgs', 'By RTGS'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted for Review'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('on_hold', 'On Hold'),
    ]

    # Basic Information
    vendor_code = models.CharField(max_length=20, unique=True, blank=True, null=True)
    country = models.ForeignKey('CMS.CountryMaster', on_delete=models.PROTECT)
    company_type = models.CharField(max_length=20, choices=COMPANY_TYPES)
    company_name = models.CharField(max_length=200)
    display_name = models.CharField(max_length=200, help_text="Name to be printed on cheques")
    create_ledger = models.BooleanField(default=True)

    # Vendor Classification
    vendor_types = models.JSONField(default=list, blank=True, null=True)
    work_description = models.CharField(max_length=20, choices=WORK_DESCRIPTIONS, blank=True, null=True)
    category = models.ForeignKey('vendors.VendorCategory', on_delete=models.SET_NULL, null=True, blank=True)

    # Registration Details
    pan_number = models.CharField(
        max_length=10,
        unique=True,
        validators=[RegexValidator(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', 'Enter a valid PAN number')]
    )
    pan_copy = models.FileField(upload_to='vendor_docs/pan/%Y/%m/', blank=True, null=True)

    # MSME Details
    is_msme = models.BooleanField(default=False)
    msme_type = models.CharField(
        max_length=1,
        choices=[
            ('M', 'Micro'), ('S', 'Small'), ('D', 'Medium'), ('G', 'General'), ('T', 'Not Applicable')
        ],
        blank=True, null=True
    )
    msme_number = models.CharField(max_length=50, blank=True, null=True)
    msme_certificate = models.FileField(upload_to='vendor_docs/msme/%Y/%m/', blank=True, null=True)
    msme_validity = models.DateField(null=True, blank=True)

    # Dates
    establishment_date = models.DateField(null=True, blank=True)
    commencement_date = models.DateField(null=True, blank=True)

    # Payment & Preferences
    payment_preference = models.CharField(max_length=10, choices=PAYMENT_PREFERENCES, blank=True, null=True)
    registered_with_bluechip = models.BooleanField(default=False, null=True)
    responsibility_return_replace = models.BooleanField(default=False, null=True)
    vendor_group = models.CharField(max_length=100, blank=True, null=True, default='')

    # Status & Workflow
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_active = models.BooleanField(default=True)
    is_blacklisted = models.BooleanField(default=False, null=True)
    blacklist_reason = models.TextField(blank=True, null=True, default='')
    blacklist_date = models.DateField(null=True, blank=True)

    # Approval Information
    submitted_date = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        'Account.CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_vendors'
    )
    reviewed_date = models.DateTimeField(null=True, blank=True)
    approved_date = models.DateTimeField(null=True, blank=True)
    approval_notes = models.TextField(blank=True, null=True, default='')
    rejection_reason = models.TextField(blank=True, null=True, default='')

    # Metadata
    created_by = models.ForeignKey('Account.CustomUser', on_delete=models.PROTECT, related_name='created_vendors')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Workflow tracking
    current_assigned_to = models.ForeignKey(
        'Account.CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_vendors'
    )

    class Meta:
        ordering = ['company_name']
        permissions = [
            ('can_submit_vendor', 'Can submit vendor for approval'),
            ('can_review_vendor', 'Can review vendor registration'),
            ('can_approve_vendor', 'Can approve vendor registration'),
            ('can_reject_vendor', 'Can reject vendor registration'),
            ('can_blacklist_vendor', 'Can blacklist vendor'),
        ]
    
    def __str__(self):
        return f"{self.company_name} ({self.vendor_code})"
    
    def save(self, *args, **kwargs):
        if not self.vendor_code:
            # Generate vendor code: V + year + sequential number
            from django.db.models import Count
            year = self.created_at.year if self.created_at else timezone.now().year
            count = Vendor.objects.filter(created_at__year=year).count() + 1
            self.vendor_code = f"V{year}{count:04d}"
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('vendor_detail', kwargs={'pk': self.pk})

    def get_primary_contact(self):
        """Get primary contact address"""
        return self.contacts.filter(is_primary=True).first()
    
    def get_primary_bank(self):
        """Get primary bank account"""
        return self.bank_details.filter(is_primary=True).first()
    
    def get_latest_financial_info(self):
        """Get latest financial information"""
        return self.financial_info.order_by('-year').first()
    
    def get_active_quality_certificates(self):
        """Get active quality certificates"""
        return self.quality_systems.filter(valid_upto__gte=timezone.now().date())
    
    def can_be_submitted(self):
        """Check if vendor can be submitted for approval"""
        return all([
            self.company_name,
            self.pan_number,
            self.country,
            self.contacts.exists(),
            self.bank_details.exists(),
            self.contacts.filter(is_primary=True).exists(),
        ])

class VendorSisterConcern(models.Model):
    """Sister concerns of the vendor"""
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='sister_concerns')
    company_name = models.CharField(max_length=200)
    address = models.TextField()
    pincode = models.CharField(max_length=6, validators=[RegexValidator(r'^[1-9][0-9]{5}$', 'Enter a valid pincode')])
    location = models.CharField(max_length=100, blank=True, null=True)
    contact_person = models.CharField(max_length=200, blank=True, null=True)
    telephone = models.CharField(max_length=12, validators=[RegexValidator(r'^[0-9]{10,12}$', 'Enter a valid telephone number')])
    fax = models.CharField(max_length=12, blank=True, null=True, validators=[RegexValidator(r'^[0-9]{10,12}$', 'Enter a valid fax number')])
    email = models.EmailField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'Sister Concern'
        verbose_name_plural = 'Sister Concerns'
    
    def __str__(self):
        return f"{self.company_name}"
    
class VendorContact(models.Model):
    CONTACT_TYPES = [
        ('branch', 'Branch'),
        ('factory', 'Factory'),
        ('godown', 'Godown/Depot'),
        ('head_office', 'Head Office'),
        ('registered_office', 'Registered Office'),
        ('workshop', 'Workshop/Service Center'),
    ]
    
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='contacts')
    contact_type = models.CharField(max_length=20, choices=CONTACT_TYPES)
    address = models.TextField()
    state = models.ForeignKey('CMS.StateUTMaster', on_delete=models.PROTECT)
    gst_number = models.CharField(max_length=15, validators=[
        RegexValidator(r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$', 'Enter a valid GST number')
    ])
    pincode = models.CharField(max_length=6, validators=[RegexValidator(r'^[1-9][0-9]{5}$', 'Enter a valid pincode')])
    location = models.CharField(max_length=100, blank=True, null=True)
    telephone = models.CharField(max_length=12, validators=[RegexValidator(r'^[0-9]{10,12}$', 'Enter a valid telephone number')])
    fax = models.CharField(max_length=12, blank=True, null=True, validators=[RegexValidator(r'^[0-9]{10,12}$', 'Enter a valid fax number')])
    working_time_from = models.TimeField(default='10:00:00', null=True)
    working_time_to = models.TimeField(default='19:00:00', null=True)
    weekly_holidays = models.JSONField(default=list, null=True)
    
    # GST Certificate
    gst_certificate = models.FileField(upload_to='vendor_docs/gst/%Y/%m/', blank=True, null=True)
    
    is_primary = models.BooleanField(default=False, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-is_primary', 'contact_type']
    
    def clean(self):
        from django.core.exceptions import ValidationError
        # Validate GST number format
        if self.gst_number and len(self.gst_number) != 15:
            raise ValidationError({'gst_number': 'GST number must be 15 characters long'})
    
    def __str__(self):
        return f"{self.get_contact_type_display()} - {self.state.name}"

class VendorBankDetail(models.Model):
    ACCOUNT_TYPES = [
        ('savings', 'Savings Account'),
        ('current', 'Current Account'),
        ('cc', 'Cash Credit'),
        ('od', 'Overdraft'),
    ]
    
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='bank_details')
    company_name = models.CharField(max_length=200)
    bank_name = models.CharField(max_length=200)
    branch_name = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    account_number = models.CharField(max_length=50)
    account_type = models.CharField(max_length=10, choices=ACCOUNT_TYPES, blank=True, null=True)
    ifsc_code = models.CharField(max_length=11, validators=[
        RegexValidator(r'^[A-Z]{4}0[0-9]{6}$', 'Enter a valid IFSC code')
    ])
    micr_code = models.CharField(max_length=9, blank=True, null=True, validators=[
        RegexValidator(r'^[0-9]{9}$', 'Enter a valid MICR code')
    ])
    swift_code = models.CharField(max_length=11, blank=True, null=True)
    iban_code = models.CharField(max_length=34, blank=True, null=True)
    bankers_details = models.TextField(blank=True, null=True)
    bank_proof = models.FileField(upload_to='vendor_docs/bank/%Y/%m/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_primary = models.BooleanField(default=False, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-is_primary', 'bank_name']
    
    def clean(self):
        from django.core.exceptions import ValidationError
        # Validate IFSC code format
        if self.ifsc_code and len(self.ifsc_code) != 11:
            raise ValidationError({'ifsc_code': 'IFSC code must be 11 characters long'})
    
    def __str__(self):
        return f"{self.bank_name} - {self.account_number[-4:]}"

class VendorConcernPerson(models.Model):
    """Concern person details"""
    CONCERN_FOR = [
        ('billing', 'Billing'),
        ('payment', 'Payment'),
        ('project', 'Project'),
        ('site', 'Site'),
        ('technical', 'Technical'),
        ('commercial', 'Commercial'),
        ('other', 'Other'),
    ]
    
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='concern_persons')
    branch = models.CharField(max_length=200, help_text="Branch or department")
    concern_for = models.CharField(max_length=20, choices=CONCERN_FOR)
    name = models.CharField(max_length=240)
    designation = models.CharField(max_length=240, blank=True, null=True)
    mobile_1 = models.CharField(max_length=10, validators=[RegexValidator(r'^[6-9][0-9]{9}$', 'Enter a valid mobile number')])
    mobile_2 = models.CharField(max_length=10, blank=True, null=True, validators=[RegexValidator(r'^[6-9][0-9]{9}$', 'Enter a valid mobile number')])
    office_phone = models.CharField(max_length=12, blank=True, null=True, validators=[RegexValidator(r'^[0-9]{10,12}$', 'Enter a valid phone number')])
    company_email = models.EmailField(blank=True, null=True)
    personal_email = models.EmailField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_primary = models.BooleanField(default=False, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Concern Person'
        verbose_name_plural = 'Concern Persons'
        ordering = ['-is_primary', 'concern_for']
    
    def __str__(self):
        return f"{self.name} - {self.get_concern_for_display()}"

class VendorFinancialInfo(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='financial_info')
    year = models.CharField(max_length=4, validators=[RegexValidator(r'^[0-9]{4}$', 'Enter a valid year')])
    share_capital_reserves = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    sales_turnover = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    cash_profit = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    
    class Meta:
        unique_together = ['vendor', 'year']
        ordering = ['-year']

class VendorQualitySystem(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='quality_systems')
    system_name = models.CharField(max_length=200)
    certificate_number = models.CharField(max_length=100)
    valid_upto = models.DateField()
    certificate_file = models.FileField(upload_to='vendor_docs/quality/%Y/%m/', blank=True, null=True)
    
    class Meta:
        ordering = ['-valid_upto']
    
    @property
    def is_expired(self):
        return self.valid_upto < timezone.now().date()
    
    @property
    def is_expiring_soon(self):
        thirty_days_from_now = timezone.now().date() + timedelta(days=30)
        return self.valid_upto <= thirty_days_from_now and self.valid_upto >= timezone.now().date()
    
    def __str__(self):
        return f"{self.system_name} - {self.certificate_number}"

class VendorCustomerReference(models.Model):
    """Customer references for the vendor"""
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='customer_references')
    customer_name = models.CharField(max_length=200)
    percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Percentage of total business"
    )
    
    class Meta:
        verbose_name = 'Customer Reference'
        verbose_name_plural = 'Customer References'
        ordering = ['-percentage']
    
    def __str__(self):
        return f"{self.customer_name} ({self.percentage}%)"

class VendorDealership(models.Model):
    """Distributor or dealership information"""
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='dealerships')
    company_name = models.CharField(max_length=200)
    product = models.CharField(max_length=200)
    territory = models.CharField(max_length=200)
    since = models.CharField(max_length=50, help_text="Year or date since dealership")
    
    class Meta:
        verbose_name = 'Dealership'
        verbose_name_plural = 'Dealerships'
    
    def __str__(self):
        return f"{self.company_name} - {self.product}"

class VendorManpower(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='manpower')
    total_strength = models.PositiveIntegerField(default=0)
    
    # Key personnel categories
    resident_managers = models.PositiveIntegerField(default=0, null=True)
    resident_managers_qualification = models.TextField(blank=True, null=True)
    resident_managers_experience = models.TextField(blank=True, null=True)
    
    site_engineers = models.PositiveIntegerField(default=0, null=True)
    site_engineers_qualification = models.TextField(blank=True, null=True)
    site_engineers_experience = models.TextField(blank=True, null=True)
    
    quality_engineers = models.PositiveIntegerField(default=0, null=True)
    quality_engineers_qualification = models.TextField(blank=True, null=True)
    quality_engineers_experience = models.TextField(blank=True, null=True)
    
    safety_coordinators = models.PositiveIntegerField(default=0, null=True)
    safety_coordinators_qualification = models.TextField(blank=True, null=True)
    safety_coordinators_experience = models.TextField(blank=True, null=True)
    
    supervisors = models.PositiveIntegerField(default=0, null=True)
    supervisors_qualification = models.TextField(blank=True, null=True)
    supervisors_experience = models.TextField(blank=True, null=True)
    
    skilled_workmen = models.PositiveIntegerField(default=0, null=True)
    skilled_workmen_qualification = models.TextField(blank=True, null=True)
    skilled_workmen_experience = models.TextField(blank=True, null=True)
    
    others = models.PositiveIntegerField(default=0, null=True)
    others_qualification = models.TextField(blank=True, null=True)
    others_experience = models.TextField(blank=True, null=True)

class VendorStatutory(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='statutory_details')
    service_tax_reg_no = models.CharField(max_length=100, blank=True, null=True)
    vat_reg_no = models.CharField(max_length=100, blank=True, null=True)
    vat_reg_date = models.DateField(null=True, blank=True)
    pf_reg_no = models.CharField(max_length=100, blank=True, null=True)
    cpwd_registered = models.BooleanField(default=False, null=True)
    cpwd_details = models.TextField(blank=True, null=True)
    gst_number = models.CharField(max_length=15, blank=True, null=True, validators=[
        RegexValidator(r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$', 'Enter a valid GST number')
    ])
    
    class Meta:
        verbose_name_plural = "Vendor statutory details"

class VendorReference(models.Model):
    """References and relations with SCIPL"""
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='references')
    
    # Current SCIPL employee relations
    scip_employee_name = models.CharField(max_length=200, blank=True, null=True)
    scip_employee_relation = models.CharField(max_length=100, blank=True, null=True)
    
    # Ex-SCIPL employee working with vendor
    ex_scip_employee_name = models.CharField(max_length=200, blank=True, null=True)
    ex_scip_employee_designation = models.CharField(max_length=200, blank=True, null=True)
    ex_scip_employee_department = models.CharField(max_length=200, blank=True, null=True)
    
    class Meta:
        verbose_name = 'Vendor Reference'
        verbose_name_plural = 'Vendor References'
    
    def __str__(self):
        return f"References for {self.vendor.company_name}"

class VendorDocument(models.Model):
    DOCUMENT_TYPES = [
        ('pan', 'PAN Card'),
        ('gst', 'GST Certificate'),
        ('msme', 'MSME Certificate'),
        ('bank', 'Bank Proof'),
        ('incorporation', 'Certificate of Incorporation'),
        ('quality', 'Quality Certificate'),
        ('other', 'Other'),
    ]
    
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    file = models.FileField(upload_to='vendor_docs/%Y/%m/',blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, null=True)
    is_verified = models.BooleanField(default=False, null=True)
    
    class Meta:
        ordering = ['-uploaded_at']

class VendorApprovalLog(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='approval_logs')
    action = models.CharField(max_length=20, choices=[
        ('submitted', 'Submitted'),
        ('reviewed', 'Reviewed'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('blacklisted', 'Blacklisted'),
    ])
    performed_by = models.ForeignKey('Account.CustomUser', on_delete=models.PROTECT)
    performed_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-performed_at']