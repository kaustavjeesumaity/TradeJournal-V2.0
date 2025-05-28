from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Account, Trade, Session, ChecklistItem, Positive, Negative, TradePlan, DailyChecklistTemplate, Instrument, TradePlanEvent

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('email', 'phone', 'username')

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label='Email')

class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['name', 'balance', 'currency']

    def clean(self):
        cleaned_data = super().clean()
        # Prevent manual entry of MT5 fields (should not be in form, but double check)
        if hasattr(self.instance, 'mt5_account_number') and (self.instance.mt5_account_number or self.instance.mt5_server):
            raise forms.ValidationError('Manual creation of MT5-linked accounts is not allowed.')
        return cleaned_data

class TradeForm(forms.ModelForm):
    gross_pnl = forms.DecimalField(label='Gross P&L', required=False)
    charges = forms.DecimalField(label='Charges', required=False)
    class Meta:
        model = Trade
        fields = [
            'account', 'instrument', 'entry_price', 'exit_price',
            'entry_date', 'exit_date', 'quantity', 'notes', 'tags',
            'gross_pnl', 'charges', 'session', 'checklist', 'positives', 'negatives'
        ]
        widgets = {
            'tags': forms.SelectMultiple(attrs={'class': 'form-control select-multi-tag'}),
            'positives': forms.SelectMultiple(attrs={'class': 'form-control select-multi-positive'}),
            'negatives': forms.SelectMultiple(attrs={'class': 'form-control select-multi-negative'}),
            'session': forms.RadioSelect(),
            'checklist': forms.CheckboxSelectMultiple(),
        }

class MT5FetchForm(forms.Form):
    mt5_account = forms.CharField(label='MT5 Account Number')
    mt5_server = forms.CharField(label='MT5 Server')
    mt5_password = forms.CharField(label='MT5 Password', widget=forms.PasswordInput)

    # No account selection; account is auto-created/linked in the view

class TradePlanForm(forms.ModelForm):
    class Meta:
        model = TradePlan
        fields = [
            'instrument', 'planned_entry', 'planned_stop', 'planned_target', 'planned_size',
            'checklist_template', 'custom_checklist', 'rationale', 'status'
        ]
        widgets = {
            'rationale': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'custom_checklist': forms.TextInput(attrs={'placeholder': 'Comma-separated custom items', 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

class TradePlanEventForm(forms.ModelForm):
    EMOTION_CHOICES = [
        ('', '---------'),
        ('Calm', 'Calm'),
        ('Anxious', 'Anxious'),
        ('Excited', 'Excited'),
        ('Confident', 'Confident'),
        ('Fearful', 'Fearful'),
        ('Frustrated', 'Frustrated'),
        ('Hopeful', 'Hopeful'),
        ('Disciplined', 'Disciplined'),
        ('Other', 'Other'),
    ]
    ACTION_CHOICES = [
        ('', '---------'),
        ('Observed', 'Observed'),
        ('Planned', 'Planned'),
        ('Executed', 'Executed'),
        ('Dropped', 'Dropped'),
        ('Adjusted', 'Adjusted'),
        ('Exited', 'Exited'),
        ('Other', 'Other'),
    ]
    emotion = forms.ChoiceField(choices=EMOTION_CHOICES, required=False, widget=forms.Select(attrs={'class': 'form-select'}))
    action = forms.ChoiceField(choices=ACTION_CHOICES, required=False, widget=forms.Select(attrs={'class': 'form-select'}))
    confidence = forms.IntegerField(min_value=1, max_value=10, widget=forms.NumberInput(attrs={'class': 'form-range', 'min': 1, 'max': 10}))
    attachment = forms.FileField(required=False, widget=forms.ClearableFileInput(attrs={'class': 'form-control'}))
    class Meta:
        model = TradePlanEvent
        fields = ['description', 'emotion', 'confidence', 'action', 'attachment']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2, 'class': 'form-control', 'placeholder': 'Describe what you observed or felt...'}),
        }
