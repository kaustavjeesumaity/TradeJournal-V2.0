from .models import Account

def account_context(request):
    """Context processor to add selected account to all templates"""
    if request.user.is_authenticated:
        accounts = Account.objects.filter(user=request.user)
        
        # Handle account selection
        selected_account_id = request.GET.get('account') or request.session.get('selected_account_id')
        selected_account = None
        
        if selected_account_id:
            try:
                selected_account = accounts.get(id=selected_account_id)
                request.session['selected_account_id'] = str(selected_account_id)
            except Account.DoesNotExist:
                pass
        
        if not selected_account and accounts.exists():
            selected_account = accounts.first()
            request.session['selected_account_id'] = str(selected_account.id)
        
        return {
            'selected_account': selected_account,
        }
    
    return {}
