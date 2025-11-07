from django.db import models
from django.core.validators import MinValueValidator, RegexValidator
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP
from CMS.models import CustomerMaster, CustomerConcernPerson
from Account.models import CustomUser

class Enquiry(models.Model):
    ENQUIRY_TYPE = (
        ('mail', 'Mail'),
        ('call', 'Call'),
        ('whatsapp', 'WhatsApp'),
        ('tender', 'Tender'),
        ('referral', 'Referral'),
        ('walk_in', 'Walk-in'),
        ('website', 'Website'),
    )
    
    ENQUIRY_STATUS = (
        ('draft', 'Draft'),
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('quoted', 'Quoted'),
        ('converted', 'Converted to Order'),
        ('lost', 'Lost'),
        ('cancelled', 'Cancelled'),
    )
    
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )

    # Basic Information
    enquiry_number = models.CharField(max_length=50, unique=True, editable=False)
    enquiry_type = models.CharField(max_length=20, choices=ENQUIRY_TYPE, default='mail')
    enquiry_date = models.DateField(default=timezone.now)
    required_by_date = models.DateField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=ENQUIRY_STATUS, default='draft')
    
    # Customer Information
    customer = models.ForeignKey(CustomerMaster, on_delete=models.CASCADE, related_name='crm_enquiries')
    contact_person = models.ForeignKey(CustomerConcernPerson, on_delete=models.SET_NULL, null=True, blank=True, related_name='enquiries')
    alternative_contact = models.CharField(max_length=100, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    
    # Enquiry Details
    subject = models.CharField(max_length=200)
    description = models.TextField()
    source = models.CharField(max_length=100, blank=True)  # How they heard about us
    project_requirements = models.TextField(blank=True)
    delivery_location = models.CharField(max_length=200, blank=True)
    
    # Tender Specific Fields
    tender_name = models.CharField(max_length=200, blank=True)
    tender_id = models.CharField(max_length=100, blank=True)
    tender_date = models.DateField(null=True, blank=True)
    tender_authority = models.CharField(max_length=200, blank=True)
    bid_submission_date = models.DateField(null=True, blank=True)
    
    # Referral Specific Fields
    referral_person_name = models.CharField(max_length=100, blank=True)
    referral_mobile = models.CharField(max_length=15, blank=True)
    referral_company = models.CharField(max_length=200, blank=True)
    
    # Financial Information
    currency = models.CharField(max_length=3, choices=(
        ('INR', 'INR - Indian Rupee'),
        ('USD', 'USD - US Dollar'),
        ('EUR', 'EUR - Euro'),
        ('GBP', 'GBP - British Pound'),
        ('AED', 'AED - UAE Dirham'),
    ), default='INR')
    estimated_budget = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    
    # System Fields
    notes = models.TextField(blank=True)
    attachment = models.FileField(upload_to='enquiry_attachments/%Y/%m/', blank=True, null=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='created_enquiries')
    created_date = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='modified_enquiries')

    class Meta:
        verbose_name = "Enquiry"
        verbose_name_plural = "Enquiries"
        ordering = ['-enquiry_date', '-created_date']
        indexes = [
            models.Index(fields=['enquiry_number']),
            models.Index(fields=['status']),
            models.Index(fields=['customer']),
            models.Index(fields=['enquiry_date']),
        ]

    def save(self, *args, **kwargs):
        if not self.enquiry_number:
            last_enquiry = Enquiry.objects.order_by('-created_date').first()
            if last_enquiry:
                last_number = int(last_enquiry.enquiry_number.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            self.enquiry_number = f"ENQ-{str(new_number).zfill(5)}"
        
        # Auto-set contact person email/phone if not provided
        if self.contact_person and not self.email:
            self.email = self.contact_person.email_company or self.contact_person.email_personal
        if self.contact_person and not self.phone:
            self.phone = self.contact_person.mobile_1
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.enquiry_number} - {self.customer.name}"

    @property
    def item_count(self):
        return self.items.count()

    @property
    def total_quantity(self):
        return self.items.aggregate(total=models.Sum('quantity'))['total'] or 0

    @property
    def days_open(self):
        return (timezone.now().date() - self.enquiry_date).days

    @property
    def can_create_quotation(self):
        return self.status in ['new', 'in_progress'] and self.items.exists()

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('crm:enquiry_detail', kwargs={'pk': self.pk})


class EnquiryItem(models.Model):
    SERVICE_CATEGORIES = (
        ('crane_rental', 'Crane Rental'),
        ('heavy_lift', 'Heavy Lift Services'),
        ('transportation', 'Transportation & Logistics'),
        ('rigging', 'Rigging Services'),
        ('equipment', 'Equipment Rental'),
        ('consultation', 'Consultation & Planning'),
        ('other', 'Other Services'),
    )

    UNIT_CHOICES = (
        ('hour', 'Per Hour'),
        ('day', 'Per Day'),
        ('week', 'Per Week'),
        ('month', 'Per Month'),
        ('trip', 'Per Trip'),
        ('ton', 'Per Ton'),
        ('unit', 'Per Unit'),
        ('lot', 'Per Lot'),
    )

    enquiry = models.ForeignKey(Enquiry, on_delete=models.CASCADE, related_name='items')
    service_category = models.CharField(max_length=50, choices=SERVICE_CATEGORIES)
    service_description = models.CharField(max_length=200)
    detailed_specifications = models.TextField(blank=True)
    
    # Quantity and Units
    quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='hour')
    
    # Requirements
    crane_capacity = models.CharField(max_length=100, blank=True)  # e.g., "50 Tons", "100 Tons"
    boom_length = models.CharField(max_length=100, blank=True)
    working_height = models.CharField(max_length=100, blank=True)
    radius = models.CharField(max_length=100, blank=True)
    location_requirements = models.TextField(blank=True)
    safety_requirements = models.TextField(blank=True)
    
    # Timeline
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    working_hours = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    
    # Pricing
    target_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, 
                                     validators=[MinValueValidator(Decimal('0.01'))])
    customer_budget = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    notes = models.TextField(blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Enquiry Item"
        verbose_name_plural = "Enquiry Items"
        ordering = ['enquiry', 'service_category']

    def __str__(self):
        return f"{self.enquiry.enquiry_number} - {self.service_description}"

    @property
    def duration_days(self):
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days
        return None


class Quotation(models.Model):
    QUOTATION_STATUS = (
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('acknowledged', 'Acknowledged'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
        ('converted', 'Converted to Order'),
    )

    VALIDITY_CHOICES = (
        (15, '15 Days'),
        (30, '30 Days'),
        (45, '45 Days'),
        (60, '60 Days'),
        (90, '90 Days'),
    )

    # Basic Information
    quotation_number = models.CharField(max_length=50, unique=True, editable=False)
    enquiry = models.ForeignKey(Enquiry, on_delete=models.CASCADE, related_name='quotations')
    quotation_date = models.DateField(default=timezone.now)
    validity_days = models.IntegerField(choices=VALIDITY_CHOICES, default=30)
    expiry_date = models.DateField(editable=False)
    status = models.CharField(max_length=20, choices=QUOTATION_STATUS, default='draft')
    
    # Customer Information
    customer = models.ForeignKey(CustomerMaster, on_delete=models.CASCADE, related_name='crm_quotations')
    contact_person = models.ForeignKey(CustomerConcernPerson, on_delete=models.SET_NULL, null=True, blank=True)
    billing_address = models.TextField()
    shipping_address = models.TextField(blank=True)
    
    # Commercial Terms
    currency = models.CharField(max_length=3, choices=Enquiry._meta.get_field('currency').choices, default='INR')
    payment_terms = models.CharField(max_length=200, default='30 Days from Date of Invoice')
    delivery_terms = models.CharField(max_length=200, default='Ex-Works')
    incoterms = models.CharField(max_length=50, blank=True)
    
    # Pricing Summary
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=18)  # GST %
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    other_charges = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Terms and Conditions
    scope_of_work = models.TextField(blank=True)
    terms_conditions = models.TextField(blank=True)
    special_instructions = models.TextField(blank=True)
    
    # System Fields
    sent_date = models.DateTimeField(null=True, blank=True)
    acknowledged_date = models.DateTimeField(null=True, blank=True)
    accepted_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='created_quotations')
    created_date = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='modified_quotations')

    class Meta:
        verbose_name = "Quotation"
        verbose_name_plural = "Quotations"
        ordering = ['-quotation_date', '-created_date']
        indexes = [
            models.Index(fields=['quotation_number']),
            models.Index(fields=['status']),
            models.Index(fields=['customer']),
            models.Index(fields=['expiry_date']),
        ]

    def save(self, *args, **kwargs):
        if not self.quotation_number:
            last_quote = Quotation.objects.order_by('-created_date').first()
            if last_quote:
                last_number = int(last_quote.quotation_number.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            self.quotation_number = f"QT-{str(new_number).zfill(5)}"
        
        # Calculate expiry date
        if self.quotation_date and self.validity_days:
            self.expiry_date = self.quotation_date + timezone.timedelta(days=self.validity_days)
        
        # Auto-populate customer and contact from enquiry
        if self.enquiry and not self.customer:
            self.customer = self.enquiry.customer
        if self.enquiry and not self.contact_person:
            self.contact_person = self.enquiry.contact_person
        
        super().save(*args, **kwargs)

    def __str__(self):
        return self.quotation_number

    @property
    def is_expired(self):
        return timezone.now().date() > self.expiry_date if self.expiry_date else False

    @property
    def item_count(self):
        return self.items.count()

    @property
    def days_until_expiry(self):
        if self.expiry_date:
            return (self.expiry_date - timezone.now().date()).days
        return None

    def calculate_totals(self):
        """Calculate quotation totals from items"""
        items = self.items.all()
        self.subtotal = sum(item.line_total for item in items)
        self.tax_amount = (self.subtotal * self.tax_rate / 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        self.total_amount = (self.subtotal + self.tax_amount + self.other_charges).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        self.save()

    def can_create_order(self):
        return self.status in ['accepted'] and self.items.exists()

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('crm:quotation_detail', kwargs={'pk': self.pk})


class QuotationItem(models.Model):
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name='items')
    enquiry_item = models.ForeignKey(EnquiryItem, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Service Details
    service_category = models.CharField(max_length=50, choices=EnquiryItem.SERVICE_CATEGORIES)
    service_description = models.TextField()
    specifications = models.TextField(blank=True)
    
    # Quantity and Pricing
    quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    unit = models.CharField(max_length=20, choices=EnquiryItem.UNIT_CHOICES, default='hour')
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    
    # Calculations
    line_total = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    
    # Additional Information
    duration = models.CharField(max_length=100, blank=True)  # e.g., "8 hours per day for 5 days"
    equipment_details = models.TextField(blank=True)
    manpower_requirements = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Quotation Item"
        verbose_name_plural = "Quotation Items"
        ordering = ['quotation', 'service_category']

    def save(self, *args, **kwargs):
        # Calculate line total
        self.line_total = (self.quantity * self.unit_price).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        super().save(*args, **kwargs)
        
        # Update quotation totals
        if self.quotation:
            self.quotation.calculate_totals()

    def __str__(self):
        return f"{self.quotation.quotation_number} - {self.service_description}"


class SalesOrder(models.Model):
    ORDER_STATUS = (
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('planning', 'Planning'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('partially_delivered', 'Partially Delivered'),
        ('delivered', 'Delivered'),
        ('invoiced', 'Invoiced'),
        ('cancelled', 'Cancelled'),
    )

    # Basic Information
    order_number = models.CharField(max_length=50, unique=True, editable=False)
    quotation = models.ForeignKey(Quotation, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales_orders')
    order_date = models.DateField(default=timezone.now)
    expected_delivery_date = models.DateField()
    actual_delivery_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='draft')
    
    # Customer Information
    customer = models.ForeignKey(CustomerMaster, on_delete=models.CASCADE, related_name='crm_sales_orders')
    contact_person = models.ForeignKey(CustomerConcernPerson, on_delete=models.SET_NULL, null=True, blank=True)
    customer_po_number = models.CharField(max_length=100)
    customer_po_date = models.DateField(null=True, blank=True)
    customer_po_file = models.FileField(upload_to='customer_po/%Y/%m/', blank=True, null=True)
    
    # Delivery Information
    delivery_address = models.TextField()
    site_contact_person = models.CharField(max_length=100, blank=True)
    site_contact_phone = models.CharField(max_length=20, blank=True)
    
    # Commercial Terms
    currency = models.CharField(max_length=3, choices=Enquiry._meta.get_field('currency').choices, default='INR')
    payment_terms = models.CharField(max_length=200)
    delivery_terms = models.CharField(max_length=200)
    
    # Pricing Summary
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=18)
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    other_charges = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    advance_received = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Project Details
    project_manager = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_orders')
    site_supervisor = models.CharField(max_length=100, blank=True)
    project_requirements = models.TextField(blank=True)
    safety_requirements = models.TextField(blank=True)
    
    # System Fields
    notes = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='created_sales_orders')
    created_date = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='modified_sales_orders')

    class Meta:
        verbose_name = "Sales Order"
        verbose_name_plural = "Sales Orders"
        ordering = ['-order_date', '-created_date']
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['status']),
            models.Index(fields=['customer']),
            models.Index(fields=['expected_delivery_date']),
        ]

    def save(self, *args, **kwargs):
        if not self.order_number:
            last_order = SalesOrder.objects.order_by('-created_date').first()
            if last_order:
                last_number = int(last_order.order_number.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            self.order_number = f"SO-{str(new_number).zfill(5)}"
        
        # Auto-populate from quotation
        if self.quotation and not self.customer:
            self.customer = self.quotation.customer
        if self.quotation and not self.contact_person:
            self.contact_person = self.quotation.contact_person
        if self.quotation and not self.payment_terms:
            self.payment_terms = self.quotation.payment_terms
        if self.quotation and not self.delivery_terms:
            self.delivery_terms = self.quotation.delivery_terms
        
        super().save(*args, **kwargs)

    def __str__(self):
        return self.order_number

    @property
    def item_count(self):
        return self.items.count()

    @property
    def progress_percentage(self):
        status_weights = {
            'draft': 0,
            'confirmed': 20,
            'planning': 40,
            'in_progress': 60,
            'partially_delivered': 80,
            'completed': 90,
            'delivered': 95,
            'invoiced': 100,
            'cancelled': 0,
        }
        return status_weights.get(self.status, 0)

    @property
    def is_overdue(self):
        if self.expected_delivery_date and self.status not in ['delivered', 'invoiced', 'cancelled']:
            return timezone.now().date() > self.expected_delivery_date
        return False

    def calculate_totals(self):
        """Calculate sales order totals from items"""
        items = self.items.all()
        self.subtotal = sum(item.line_total for item in items)
        self.tax_amount = (self.subtotal * self.tax_rate / 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        self.total_amount = (self.subtotal + self.tax_amount + self.other_charges).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        self.save()

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('crm:sales_order_detail', kwargs={'pk': self.pk})


class SalesOrderItem(models.Model):
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='items')
    quotation_item = models.ForeignKey(QuotationItem, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Service Details
    service_category = models.CharField(max_length=50, choices=EnquiryItem.SERVICE_CATEGORIES)
    service_description = models.TextField()
    specifications = models.TextField(blank=True)
    
    # Quantity and Pricing
    quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    unit = models.CharField(max_length=20, choices=EnquiryItem.UNIT_CHOICES, default='hour')
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    
    # Calculations
    line_total = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    
    # Execution Details
    planned_start_date = models.DateField(null=True, blank=True)
    planned_end_date = models.DateField(null=True, blank=True)
    actual_start_date = models.DateField(null=True, blank=True)
    actual_end_date = models.DateField(null=True, blank=True)
    completed_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Resource Allocation
    assigned_equipment = models.TextField(blank=True)
    assigned_team = models.TextField(blank=True)
    status = models.CharField(max_length=20, default='pending', choices=(
        ('pending', 'Pending'),
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ))
    
    notes = models.TextField(blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Sales Order Item"
        verbose_name_plural = "Sales Order Items"
        ordering = ['sales_order', 'service_category']

    def save(self, *args, **kwargs):
        # Calculate line total
        self.line_total = (self.quantity * self.unit_price).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        super().save(*args, **kwargs)
        
        # Update sales order totals
        if self.sales_order:
            self.sales_order.calculate_totals()

    def __str__(self):
        return f"{self.sales_order.order_number} - {self.service_description}"

    @property
    def completion_percentage(self):
        if self.quantity > 0:
            return (self.completed_quantity / self.quantity * 100).quantize(Decimal('1.00'))
        return Decimal('0.00')
    

class Project(models.Model):
    PROJECT_STATUS = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
    ]

    name = models.CharField(max_length=200)
    project_id = models.CharField(max_length=20, unique=True)
    customer = models.ForeignKey('CMS.CustomerMaster', on_delete=models.CASCADE)
    division = models.ForeignKey('CMS.DivisionMaster', on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=PROJECT_STATUS, default='active')
    is_active = models.BooleanField(default=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.project_id} - {self.name}"

    class Meta:
        verbose_name = "Project"
        verbose_name_plural = "Projects"

class Region(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Region"
        verbose_name_plural = "Regions"

class Site(models.Model):
    SITE_TYPES = [
        ('project_site', 'Project Site'),
        ('company_yard', 'Company Yard'),
        ('client_site', 'Client Site'),
    ]

    # Basic Information
    name = models.CharField(max_length=200)
    site_id = models.CharField(max_length=20, unique=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    site_type = models.CharField(max_length=20, choices=SITE_TYPES, default='project_site')
    is_active = models.BooleanField(default=True)
    
    # Location Details
    region = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True, blank=True)
    state = models.ForeignKey('CMS.StateUTMaster', on_delete=models.SET_NULL, null=True)
    address = models.TextField()
    site_location = models.CharField(max_length=300)
    pin_code = models.CharField(max_length=6, validators=[RegexValidator(r'^\d{6}$', 'Enter a valid 6-digit PIN code')])
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Management
    site_head = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, 
                                 related_name='site_head')
    
    # Meta
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='sites_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.site_id} - {self.name}"

    class Meta:
        verbose_name = "Site"
        verbose_name_plural = "Sites"
        ordering = ['-created_at']


class SiteEmployee(models.Model):
    ROLES = [
        ('site_head', 'Site Head'),
        ('project_manager', 'Project Manager'),
        ('supervisor', 'Supervisor'),
        ('safety_officer', 'Safety Officer'),
        ('logistics_manager', 'Logistics Manager'),
    ]

    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='involved_employees')
    employee = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    role = models.CharField(max_length=50, choices=ROLES)
    is_reporting_authority = models.BooleanField(default=False)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.role} - {self.site}"

    class Meta:
        verbose_name = "Site Employee"
        verbose_name_plural = "Site Employees"
        unique_together = ['site', 'employee']


class SiteDocument(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=100)
    file = models.FileField(upload_to='site_documents/')
    description = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.document_type} - {self.site}"

    class Meta:
        verbose_name = "Site Document"
        verbose_name_plural = "Site Documents"