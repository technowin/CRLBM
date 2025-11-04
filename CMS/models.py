# models.py
from django.db import models
from django.core.validators import RegexValidator, MinValueValidator
from django.utils import timezone
from django.contrib.auth.models import User

class TypeOfOrganization(models.Model):
    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Type of Organization"
        verbose_name_plural = "Types of Organization"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class BranchCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Branch Category"
        verbose_name_plural = "Branch Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class StateUTMaster(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    is_union_territory = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "State/UT"
        verbose_name_plural = "States/UTs"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class CountryMaster(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=5, unique=True)
    currency = models.CharField(max_length=50)
    currency_code = models.CharField(max_length=3)
    phone_code = models.CharField(max_length=5, default='+91')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Country"
        verbose_name_plural = "Countries"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class DivisionMaster(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Division"
        verbose_name_plural = "Divisions"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class ConcernCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Concern Category"
        verbose_name_plural = "Concern Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class CustomerMaster(models.Model):
    CUSTOMER_STATUS = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
    ]
    
    PAYMENT_TERMS = [
        ('net_7', 'Net 7 Days'),
        ('net_15', 'Net 15 Days'),
        ('net_30', 'Net 30 Days'),
        ('net_45', 'Net 45 Days'),
        ('net_60', 'Net 60 Days'),
        ('due_on_receipt', 'Due on Receipt'),
        ('advance', 'Advance Payment'),
    ]
    
    CURRENCY_CHOICES = [
        ('INR', 'Indian Rupee (INR)'),
        ('USD', 'US Dollar (USD)'),
        ('EUR', 'Euro (EUR)'),
        ('GBP', 'British Pound (GBP)'),
        ('AED', 'UAE Dirham (AED)'),
    ]
    
    # Basic Information
    customer_id = models.CharField(max_length=20, unique=True, blank=True)
    organization_type = models.ForeignKey(TypeOfOrganization, on_delete=models.PROTECT)
    name = models.CharField(max_length=255)
    display_name = models.CharField(max_length=300, blank=True)
    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=CUSTOMER_STATUS, default='active')
    
    # General Information
    date_of_establishment = models.DateField(null=True, blank=True)
    pan_number = models.CharField(max_length=10, unique=True, validators=[
        RegexValidator(regex='^[A-Z]{5}[0-9]{4}[A-Z]{1}$', message='Invalid PAN format')
    ])
    msme_udyam_reg_no = models.CharField(max_length=25, blank=True)
    tan_number = models.CharField(max_length=10, blank=True, validators=[
        RegexValidator(regex='^[A-Z]{4}[0-9]{5}[A-Z]{1}$', message='Invalid TAN format')
    ])
    cin_number = models.CharField(max_length=21, blank=True, validators=[
        RegexValidator(regex='^[A-Z]{1}[0-9]{5}[A-Z]{2}[0-9]{4}[A-Z]{3}[0-9]{6}$', message='Invalid CIN format')
    ])
    ie_code = models.CharField(max_length=10, blank=True)
    exemption_certificates = models.TextField(blank=True)
    
    # Financial Information
    billing_currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='INR')
    payment_terms = models.CharField(max_length=20, choices=PAYMENT_TERMS, default='net_30')
    requires_advance = models.BooleanField(default=False)
    credit_limit = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, validators=[MinValueValidator(0)])
    current_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    
    # Contact Information
    website = models.URLField(blank=True)
    billing_contact_person = models.CharField(max_length=100, blank=True)
    billing_contact_email = models.EmailField(blank=True)
    billing_contact_phone = models.CharField(max_length=15, blank=True)
    
    # System Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('Account.CustomUser', on_delete=models.PROTECT, related_name='created_customers')
    
    class Meta:
        verbose_name = "Customer"
        verbose_name_plural = "Customers"
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['customer_id']),
            models.Index(fields=['pan_number']),
            models.Index(fields=['is_active']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.customer_id:
            # Generate customer ID: CUST + 6 digit number
            last_customer = CustomerMaster.objects.order_by('-id').first()
            last_id = last_customer.id if last_customer else 0
            self.customer_id = f"CUST{str(last_id + 1).zfill(6)}"
        
        # Generate display name
        org_type_name = self.organization_type.name if self.organization_type else ""
        self.display_name = f"{self.name} {org_type_name}".strip()
        
        # Update status based on is_active
        if not self.is_active:
            self.status = 'inactive'
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.name} ({self.customer_id})"
    
    @property
    def available_credit(self):
        return self.credit_limit - self.current_balance
    
    @property
    def total_concern_persons(self):
        return self.concern_persons.count()
    
    @property
    def active_concern_persons(self):
        return self.concern_persons.filter(is_active=True).count()

class CustomerAddress(models.Model):
    BRANCH_CATEGORIES = [
        ('registered_office', 'Registered Office/Head Office'),
        ('branch_office', 'Regional/Branch Office'),
        ('factory', 'Factory/Mfg. Facility'),
        ('warehouse', 'Godown/Warehouse'),
        ('project_site', 'Job Site/Project Site'),
    ]
    
    customer = models.ForeignKey(CustomerMaster, on_delete=models.CASCADE, related_name='addresses')
    branch_category = models.CharField(max_length=20, choices=BRANCH_CATEGORIES)
    branch_id = models.CharField(max_length=20, blank=True)
    
    # Address Details
    address = models.TextField()
    state = models.ForeignKey(StateUTMaster, on_delete=models.PROTECT)
    country = models.ForeignKey(CountryMaster, on_delete=models.PROTECT)
    pincode = models.CharField(max_length=10)
    location = models.CharField(max_length=100)
    google_location = models.CharField(max_length=300, blank=True)
    
    # Contact Details
    telephone = models.CharField(max_length=15, blank=True)
    email = models.EmailField(blank=True)
    
    # Tax Information
    gst_number = models.CharField(max_length=15, blank=True, validators=[
        RegexValidator(regex='^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$', message='Invalid GST format')
    ])
    
    is_primary = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Customer Address"
        verbose_name_plural = "Customer Addresses"
        ordering = ['-is_primary', 'branch_category']
        unique_together = ['customer', 'branch_id']
    
    def save(self, *args, **kwargs):
        if not self.branch_id:
            # Generate branch ID based on category
            category_code = self.branch_category[:3].upper()
            count = CustomerAddress.objects.filter(customer=self.customer, branch_category=self.branch_category).count()
            self.branch_id = f"{category_code}{str(count + 1).zfill(3)}"
        
        # If this is set as primary, unset others
        if self.is_primary:
            CustomerAddress.objects.filter(customer=self.customer, is_primary=True).update(is_primary=False)
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.customer.name} - {self.get_branch_category_display()}"

class CustomerBankDetails(models.Model):
    ACCOUNT_TYPES = [
        ('savings', 'Savings Account'),
        ('current', 'Current Account'),
        ('cc', 'Cash Credit'),
        ('od', 'Overdraft'),
    ]
    
    customer = models.ForeignKey(CustomerMaster, on_delete=models.CASCADE, related_name='bank_details')
    bank_name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=20)
    account_holder_name = models.CharField(max_length=255, blank=True)
    branch_name = models.CharField(max_length=100)
    ifsc_code = models.CharField(max_length=11, validators=[
        RegexValidator(regex='^[A-Z]{4}0[A-Z0-9]{6}$', message='Invalid IFSC code format')
    ])
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES, default='current')
    is_primary = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Customer Bank Detail"
        verbose_name_plural = "Customer Bank Details"
        ordering = ['-is_primary', 'bank_name']
        unique_together = ['customer', 'account_number']
    
    def save(self, *args, **kwargs):
        # If this is set as primary, unset others
        if self.is_primary:
            CustomerBankDetails.objects.filter(customer=self.customer, is_primary=True).update(is_primary=False)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.bank_name} - {self.account_number}"

class CustomerDivision(models.Model):
    customer = models.ForeignKey(CustomerMaster, on_delete=models.CASCADE, related_name='divisions')
    division = models.ForeignKey(DivisionMaster, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    assigned_date = models.DateField(auto_now_add=True)
    assigned_by = models.ForeignKey('Account.CustomUser', on_delete=models.PROTECT)
    
    class Meta:
        verbose_name = "Customer Division"
        verbose_name_plural = "Customer Divisions"
        unique_together = ['customer', 'division']
    
    def __str__(self):
        return f"{self.customer.name} - {self.division.name}"

class CustomerConcernPerson(models.Model):
    customer = models.ForeignKey(CustomerMaster, on_delete=models.CASCADE, related_name='concern_persons')
    branch_category = models.CharField(max_length=20, choices=CustomerAddress.BRANCH_CATEGORIES, blank=True)
    address = models.ForeignKey(CustomerAddress, on_delete=models.SET_NULL, null=True, blank=True, related_name='concern_persons')
    
    # Personal Information
    concern_person = models.CharField(max_length=240)
    designation = models.CharField(max_length=240, blank=True)
    concern_for = models.ManyToManyField(ConcernCategory, blank=True, related_name='concern_persons')
    
    # Contact Information
    country_1 = models.ForeignKey(CountryMaster, on_delete=models.PROTECT, related_name='concern_persons_country1')
    mobile_1 = models.CharField(max_length=15, validators=[
        RegexValidator(regex='^[0-9]{10}$', message='Mobile number must be 10 digits')
    ])
    country_2 = models.ForeignKey(CountryMaster, on_delete=models.PROTECT, related_name='concern_persons_country2', null=True, blank=True)
    mobile_2 = models.CharField(max_length=15, blank=True, validators=[
        RegexValidator(regex='^[0-9]{10}$', message='Mobile number must be 10 digits')
    ])
    
    # Office Contact
    office_phone_1 = models.CharField(max_length=11, blank=True)
    office_extension_1 = models.CharField(max_length=4, blank=True)
    office_phone_2 = models.CharField(max_length=11, blank=True)
    
    # Email Addresses
    email_company = models.EmailField(blank=True)
    email_personal = models.EmailField(blank=True)
    
    # Additional Information
    remarks = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    is_primary_contact = models.BooleanField(default=False)
    
    # System Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('Account.CustomUser', on_delete=models.PROTECT, related_name='created_concern_persons')
    
    class Meta:
        verbose_name = "Customer Concern Person"
        verbose_name_plural = "Customer Concern Persons"
        ordering = ['customer', 'concern_person']
        indexes = [
            models.Index(fields=['concern_person']),
            models.Index(fields=['is_active']),
            models.Index(fields=['customer', 'is_active']),
        ]
    
    def save(self, *args, **kwargs):
        # If this is set as primary contact, unset others
        if self.is_primary_contact:
            CustomerConcernPerson.objects.filter(customer=self.customer, is_primary_contact=True).update(is_primary_contact=False)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.concern_person} - {self.customer.name}"
    
    @property
    def full_mobile_1(self):
        if self.country_1 and self.mobile_1:
            return f"{self.country_1.phone_code} {self.mobile_1}"
        return self.mobile_1
    
    @property
    def full_mobile_2(self):
        if self.country_2 and self.mobile_2:
            return f"{self.country_2.phone_code} {self.mobile_2}"
        return self.mobile_2

class CustomerDocument(models.Model):
    DOCUMENT_TYPES = [
        ('pan_card', 'PAN Card'),
        ('gst_certificate', 'GST Certificate'),
        ('msme_certificate', 'MSME Certificate'),
        ('incorporation_certificate', 'Incorporation Certificate'),
        ('trade_license', 'Trade License'),
        ('udyam_certificate', 'Udyam Certificate'),
        ('other', 'Other'),
    ]
    
    customer = models.ForeignKey(CustomerMaster, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES)
    document_name = models.CharField(max_length=255)
    document_file = models.FileField(upload_to='customer_documents/%Y/%m/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey('Account.CustomUser', on_delete=models.PROTECT)
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey('Account.CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_documents')
    verified_at = models.DateTimeField(null=True, blank=True)
    remarks = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Customer Document"
        verbose_name_plural = "Customer Documents"
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.customer.name} - {self.get_document_type_display()}"

class CustomerNote(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    customer = models.ForeignKey(CustomerMaster, on_delete=models.CASCADE, related_name='notes')
    title = models.CharField(max_length=200)
    content = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    is_resolved = models.BooleanField(default=False)
    created_by = models.ForeignKey('Account.CustomUser', on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey('Account.CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_notes')
    
    class Meta:
        verbose_name = "Customer Note"
        verbose_name_plural = "Customer Notes"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.customer.name} - {self.title}"