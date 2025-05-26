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
