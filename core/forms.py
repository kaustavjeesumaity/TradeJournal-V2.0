from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Account, Trade, TradeAttachment

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
    attachment = forms.FileField(required=False, label='Attachment (image/pdf)', widget=forms.ClearableFileInput(attrs={'accept': 'image/*,application/pdf'}))
    gross_pnl = forms.DecimalField(label='Gross P&L', required=False)
    charges = forms.DecimalField(label='Charges', required=False)
    class Meta:
        model = Trade
        fields = [
            'account', 'instrument', 'entry_price', 'exit_price',
            'entry_date', 'exit_date', 'quantity', 'notes', 'tags',
            'gross_pnl', 'charges'
        ]

class MT5FetchForm(forms.Form):
    mt5_account = forms.CharField(label='MT5 Account Number')
    mt5_server = forms.CharField(label='MT5 Server')
    mt5_password = forms.CharField(label='MT5 Password', widget=forms.PasswordInput)

    # No account selection; account is auto-created/linked in the view
