from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.

class User(AbstractUser):
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    # Add preferences fields as needed

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

class Account(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='accounts')
    name = models.CharField(max_length=100)
    balance = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10, default='USD')
    created_at = models.DateTimeField(auto_now_add=True)
    # MT5 integration fields
    mt5_account_number = models.CharField(max_length=32, blank=True, null=True)
    mt5_server = models.CharField(max_length=128, blank=True, null=True)
    mt5_last_fetch = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.currency})"

class Tag(models.Model):
    name = models.CharField(max_length=50)
    def __str__(self):
        return self.name

class Instrument(models.Model):
    name = models.CharField(max_length=50, unique=True)
    def __str__(self):
        return self.name

class Session(models.Model):
    name = models.CharField(max_length=50, unique=True)
    def __str__(self):
        return self.name

class ChecklistItem(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.name

class Positive(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.name

class Negative(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.name

class Trade(models.Model):
    account = models.ForeignKey('Account', on_delete=models.CASCADE, related_name='trades')
    instrument = models.CharField(max_length=100)
    entry_price = models.DecimalField(max_digits=12, decimal_places=4)
    exit_price = models.DecimalField(max_digits=12, decimal_places=4)
    entry_date = models.DateTimeField()
    exit_date = models.DateTimeField()
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    notes = models.TextField(blank=True)
    tags = models.ManyToManyField('Tag', blank=True)
    session = models.ForeignKey('Session', null=True, blank=True, on_delete=models.SET_NULL)
    checklist = models.ManyToManyField('ChecklistItem', blank=True)
    positives = models.ManyToManyField('Positive', blank=True)
    negatives = models.ManyToManyField('Negative', blank=True)
    gross_pnl = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    charges = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_pnl = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    @property
    def pnl(self):
        return self.net_pnl

    # Add a property for instrument object if needed
    @property
    def instrument_obj(self):
        from .models import Instrument
        return Instrument.objects.filter(name=self.instrument).first()

    def __str__(self):
        return f"{self.instrument} ({self.entry_date.date()} - {self.exit_date.date()})"

class TradeAttachment(models.Model):
    trade = models.ForeignKey('Trade', on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='trade_attachments/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attachment for {self.trade} ({self.file.name})"

class DailyChecklistTemplate(models.Model):
    name = models.CharField(max_length=100, default='Default')
    effective_date = models.DateField(help_text='Checklist applies from this date (inclusive)')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-effective_date']

    def __str__(self):
        return f"{self.name} (from {self.effective_date})"

class DailyChecklistItem(models.Model):
    template = models.ForeignKey(DailyChecklistTemplate, on_delete=models.CASCADE, related_name='items')
    text = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.text

class UserDailyChecklistProgress(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    item = models.ForeignKey(DailyChecklistItem, on_delete=models.CASCADE)
    date = models.DateField()
    checked = models.BooleanField(default=False)
    checked_at = models.DateTimeField(blank=True, null=True)
    holiday = models.BooleanField(default=False)  # NEW FIELD

    class Meta:
        unique_together = ('user', 'item', 'date')
        ordering = ['date', 'item']

    def __str__(self):
        return f"{self.user} - {self.item} on {self.date}: {'Done' if self.checked else 'Not done'}"

class TradePlan(models.Model):
    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('executed', 'Executed'),
        ('abandoned', 'Abandoned'),
    ]
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    instrument = models.ForeignKey('Instrument', on_delete=models.CASCADE)
    planned_entry = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    planned_stop = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    planned_target = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    planned_size = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    planned_at = models.DateTimeField(auto_now_add=True)
    checklist_template = models.ForeignKey('DailyChecklistTemplate', on_delete=models.SET_NULL, blank=True, null=True)
    rationale = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='planned')
    # Custom checklist items (JSON or text)
    custom_checklist = models.TextField(blank=True, help_text='Comma-separated custom checklist items')

    def __str__(self):
        return f"{self.instrument} plan by {self.user} on {self.planned_at:%Y-%m-%d}"  

class TradePlanAttachment(models.Model):
    trade_plan = models.ForeignKey(TradePlan, on_delete=models.CASCADE, related_name='attachments')
    image = models.ImageField(upload_to='trade_plan_attachments/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attachment for {self.trade_plan}"

class TradePlanEvent(models.Model):
    trade_plan = models.ForeignKey(TradePlan, on_delete=models.CASCADE, related_name='events')
    timestamp = models.DateTimeField(auto_now_add=True)
    description = models.TextField()
    emotion = models.CharField(max_length=100, blank=True)
    confidence = models.IntegerField(blank=True, null=True, help_text='0-100 scale')
    action = models.CharField(max_length=100, blank=True, help_text='E.g. Observed, Planned, Executed, Dropped')
    attachment = models.FileField(upload_to='trade_plan_event_attachments/', blank=True, null=True)

    def __str__(self):
        return f"{self.trade_plan} @ {self.timestamp:%Y-%m-%d %H:%M} - {self.action}"
