from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Account, Trade, Session, ChecklistItem, Positive, Negative, TradePlan, DailyChecklistTemplate, Instrument, TradePlanEvent, Milestone, Lesson, Achievement, Review, Course, Book, KeyLesson, Mistake

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('email', 'phone', 'username')

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label='Email')

class AccountForm(forms.ModelForm):
    account_source = forms.ChoiceField(
        choices=[('manual', 'Manual Entry'), ('mt5', 'MetaTrader 5')],
        widget=forms.RadioSelect,
        initial='manual',
        help_text='Choose how to create this account'    )
    
    class Meta:
        model = Account
        fields = ['name', 'balance', 'currency', 'account_type', 'broker', 'leverage']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add CSS classes to form fields
        self.fields['name'].widget.attrs.update({'class': 'form-control manual-field'})
        self.fields['balance'].widget.attrs.update({'class': 'form-control manual-field'})
        self.fields['currency'].widget.attrs.update({'class': 'form-control manual-field'})
        self.fields['account_type'].widget.attrs.update({'class': 'form-control manual-field'})
        self.fields['broker'].widget.attrs.update({'class': 'form-control manual-field'})
        self.fields['leverage'].widget.attrs.update({'class': 'form-control manual-field'})

        # Dynamically set required fields based on account_source
        data = args[0] if args else None
        account_source = None
        if data:
            account_source = data.get('account_source')
        elif self.initial.get('account_source'):
            account_source = self.initial.get('account_source')
        else:
            account_source = self.fields['account_source'].initial

        if account_source == 'mt5':
            # Make manual fields not required for MT5
            self.fields['name'].required = False
            self.fields['balance'].required = False
            self.fields['currency'].required = False
            self.fields['account_type'].required = False
            self.fields['broker'].required = False
            self.fields['leverage'].required = False
        else:
            # Manual: require name and balance
            self.fields['name'].required = True
            self.fields['balance'].required = True
            self.fields['currency'].required = True
            self.fields['account_type'].required = True
            self.fields['broker'].required = False
            self.fields['leverage'].required = False

    def clean(self):
        cleaned_data = super().clean()
        account_source = cleaned_data.get('account_source')
        
        if account_source == 'mt5':
            # For MT5 accounts, we don't need manual entry of balance, etc.
            # These will be fetched from MT5
            pass
        elif account_source == 'manual':
            # For manual accounts, ensure required fields are provided
            if not cleaned_data.get('name'):
                raise forms.ValidationError('Account name is required for manual accounts.')
            if not cleaned_data.get('balance'):
                raise forms.ValidationError('Initial balance is required for manual accounts.')
        
        return cleaned_data

    def save(self, commit=True):
        account_source = self.cleaned_data.get('account_source')
        instance = super().save(commit=False)
        if account_source == 'mt5':
            # Provide dummy values for required fields to pass model validation
            if not instance.balance:
                instance.balance = 0
            if not instance.name:
                instance.name = 'MT5 Account'
            # You may want to set other fields as well if your model requires them
        if commit:
            instance.save()
        return instance


class MT5AccountForm(forms.Form):
    """Form for connecting MT5 account"""
    mt5_account = forms.CharField(
        label='MT5 Account Number',
        help_text='Your MetaTrader 5 account number'
    )
    mt5_server = forms.CharField(
        label='MT5 Server',
        help_text='Your broker server (e.g., Demo-Server, Live-Server)'
    )
    mt5_password = forms.CharField(
        label='MT5 Password',
        widget=forms.PasswordInput,
        help_text='Your MetaTrader 5 account password'
    )
    account_name = forms.CharField(
        label='Account Name',
        help_text='A friendly name for this account in your journal',
        max_length=100
    )

class TradeForm(forms.ModelForm):
    gross_pnl = forms.DecimalField(label='Gross P&L', required=False)
    charges = forms.DecimalField(label='Charges', required=False)
    class Meta:
        model = Trade
        fields = [
            'account', 'instrument', 'asset_class', 'direction', 'status', 'entry_price', 'exit_price',
            'entry_date', 'exit_date', 'size', 'stop_loss', 'take_profit', 'risk_per_trade',
            'fees', 'slippage', 'r_multiple', 'notes', 'tags', 'gross_pnl', 'charges',
            'session', 'checklist', 'positives', 'negatives', 'order_type', 'outcome',            'psychological_state', 'journal_notes', 'lessons_learned', 'planned_trade'
        ]
        widgets = {
            'tags': forms.SelectMultiple(attrs={'class': 'form-control select-multi-tag'}),
            'positives': forms.SelectMultiple(attrs={'class': 'form-control select-multi-positive'}),
            'negatives': forms.SelectMultiple(attrs={'class': 'form-control select-multi-negative'}),
            'session': forms.RadioSelect(),
            'checklist': forms.CheckboxSelectMultiple(),
            'direction': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'planned_trade': forms.Select(attrs={'class': 'form-select'}),
        }

class MT5FetchForm(forms.Form):
    mt5_account = forms.ModelChoiceField(
        queryset=None,  # Will be set in __init__
        label='Select MT5 Account',
        help_text='Choose from your existing MT5 accounts',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    mt5_password = forms.CharField(
        label='MT5 Password', 
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text='Your MetaTrader 5 account password'
    )

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            # Only show accounts that have MT5 integration
            self.fields['mt5_account'].queryset = Account.objects.filter(
                user=user,
                mt5_account_number__isnull=False,
                mt5_server__isnull=False
            ).exclude(mt5_account_number='').exclude(mt5_server='')
            
            # If no MT5 accounts exist, show helpful message
            if not self.fields['mt5_account'].queryset.exists():
                self.fields['mt5_account'].empty_label = "No MT5 accounts found - Create one first"
                self.fields['mt5_account'].widget.attrs['disabled'] = True
            else:
                self.fields['mt5_account'].empty_label = "Select an MT5 account"
            print("MT5 Account Form initialized for user:", user.username if user else "No user")

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
            'instrument': forms.Select(attrs={'class': 'form-select'}),
            'planned_entry': forms.NumberInput(attrs={'class': 'form-control'}),
            'planned_stop': forms.NumberInput(attrs={'class': 'form-control'}),
            'planned_target': forms.NumberInput(attrs={'class': 'form-control'}),
            'planned_size': forms.NumberInput(attrs={'class': 'form-control'}),
            'checklist_template': forms.Select(attrs={'class': 'form-select'}),
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
    confidence = forms.IntegerField(min_value=1, max_value=10, required=False, widget=forms.NumberInput(attrs={'class': 'form-range', 'min': 1, 'max': 10}))
    description = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2, 'class': 'form-control', 'placeholder': 'Describe what you observed or felt...'}))

    class Meta:
        model = TradePlanEvent
        fields = ['description', 'emotion', 'confidence', 'action']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2, 'class': 'form-control', 'placeholder': 'Describe what you observed or felt...'}),
        }

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'email', 'username', 'phone', 'avatar', 'timezone', 'country', 'trading_style',
            'experience_level', 'risk_profile', 'default_account', 'goals', 'motivational_quote',
            'review_frequency', 'custom_checklist', 'discipline_score', 'psychological_notes', 'learning_progress'
        ]
        widgets = {
            'goals': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'motivational_quote': forms.TextInput(attrs={'class': 'form-control'}),
            'review_frequency': forms.TextInput(attrs={'class': 'form-control'}),
            'custom_checklist': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'psychological_notes': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'learning_progress': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }

class MilestoneForm(forms.ModelForm):
    class Meta:
        model = Milestone
        fields = ['description']

class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['content', 'source']

class AchievementForm(forms.ModelForm):
    class Meta:
        model = Achievement
        fields = ['name', 'description']

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['period', 'summary']

# Structured learning progress forms
class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['name', 'completed', 'completion_date', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'completion_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'author', 'completed', 'completion_date', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'completion_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

class KeyLessonForm(forms.ModelForm):
    class Meta:
        model = KeyLesson
        fields = ['content', 'date']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

class MistakeForm(forms.ModelForm):
    class Meta:
        model = Mistake
        fields = ['description', 'date']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
